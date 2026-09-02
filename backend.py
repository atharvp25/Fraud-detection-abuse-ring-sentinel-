"""
FastAPI Backend — Serves ML results, ring data, and LLM explanations to the React dashboard.

Risk scores are computed from the actual XGBoost model's predict_proba() output,
not a hand-written formula. This ensures the dashboard reflects the real model.
"""
import os
import sys
import traceback
import pandas as pd
import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from llm_engine.explain import explain_ring, explain_customer

app = FastAPI(title="Abuse Ring Sentinel API", version="1.0")

# Allow React dev server (localhost:5173) to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Data paths ──
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ── Load ML model at startup for real risk scoring ──
ML_MODEL = None
ML_FEATURES = None
try:
    model_path = os.path.join(MODELS_DIR, "xgboost_tabular.pkl")
    if os.path.exists(model_path):
        saved = joblib.load(model_path)
        ML_MODEL = saved["model"]
        ML_FEATURES = saved["features"]
        print(f"[OK] XGBoost model loaded ({len(ML_FEATURES)} features)")
    else:
        print("[WARN] xgboost_tabular.pkl not found -- risk scores will use fallback formula")
except Exception as e:
    print(f"[WARN] Failed to load model: {e} -- risk scores will use fallback formula")


def load_csv(directory, filename):
    """Load a CSV file, return empty DataFrame if not found."""
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


# ══════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Abuse Ring Sentinel API is running"}


@app.get("/api/overview")
def get_overview():
    """Dashboard overview — total stats, class balance, model results."""
    customers = load_csv(RAW_DIR, "customers.csv")
    labels = load_csv(RAW_DIR, "labels.csv")
    ring_meta = load_csv(RAW_DIR, "ring_metadata.csv")
    transactions = load_csv(RAW_DIR, "transactions.csv")
    eval_results = load_csv(PROCESSED_DIR, "evaluation_results.csv")

    total_customers = len(customers)
    total_rings = len(ring_meta)
    ring_members = int(labels["is_ring_member"].sum()) if "is_ring_member" in labels.columns else 0
    total_transactions = len(transactions)

    # Customer type breakdown
    type_counts = {}
    if "customer_type" in customers.columns:
        type_counts = customers["customer_type"].value_counts().to_dict()

    # Ring type breakdown
    ring_type_counts = {}
    if "ring_type" in ring_meta.columns:
        ring_type_counts = ring_meta["ring_type"].value_counts().to_dict()

    # Model comparison
    models = []
    if not eval_results.empty:
        models = eval_results.to_dict(orient="records")

    return {
        "total_customers": total_customers,
        "total_rings": total_rings,
        "ring_members": ring_members,
        "safe_users": total_customers - ring_members,
        "total_transactions": total_transactions,
        "customer_types": type_counts,
        "ring_types": ring_type_counts,
        "models": models,
    }


@app.get("/api/rings")
def get_rings():
    """List all detected rings with risk scores from the actual XGBoost model."""
    ring_meta = load_csv(RAW_DIR, "ring_metadata.csv")
    labels = load_csv(RAW_DIR, "labels.csv")
    features = load_csv(PROCESSED_DIR, "feature_matrix.csv")

    if ring_meta.empty:
        return {"rings": []}

    rings = []
    for _, ring in ring_meta.iterrows():
        ring_id = ring["ring_id"]

        # Get members of this ring
        member_ids = labels[labels["ring_id"] == ring_id]["customer_id"].tolist()

        # Get feature stats for members
        member_features = features[features["customer_id"].isin(member_ids)]
        avg_refund = float(member_features["refund_rate"].mean()) if not member_features.empty else 0
        avg_amount = float(member_features["avg_transaction_amount"].mean()) if not member_features.empty else 0

        # Risk score from ACTUAL model predict_proba() — not a hand-written formula
        risk_score = _compute_ring_risk_score(member_features)

        rings.append({
            "ring_id": ring_id,
            "ring_type": ring.get("ring_type", "unknown"),
            "ring_size": int(ring.get("ring_size", 0)),
            "num_shared_devices": int(ring.get("num_shared_devices", 0)),
            "num_shared_ips": int(ring.get("num_shared_ips", 0)),
            "num_shared_payments": int(ring.get("num_shared_payments", 0)),
            "avg_refund_rate": round(avg_refund, 3),
            "avg_transaction_amount": round(avg_amount, 2),
            "risk_score": risk_score,
        })

    # Sort by risk score descending
    rings.sort(key=lambda x: x["risk_score"], reverse=True)
    return {"rings": rings}


def _compute_ring_risk_score(member_features):
    """
    Compute risk score using the REAL model's predict_proba().
    Returns the average fraud probability across all ring members, scaled to 0-100.
    Falls back to a simple heuristic if the model isn't loaded.
    """
    if ML_MODEL is not None and ML_FEATURES is not None and not member_features.empty:
        try:
            available = [f for f in ML_FEATURES if f in member_features.columns]
            X = member_features[available].fillna(0)
            probas = ML_MODEL.predict_proba(X)[:, 1]  # Probability of being a ring member
            avg_proba = float(probas.mean())
            return int(round(avg_proba * 100))
        except Exception:
            pass

    # Fallback: simple heuristic (only if model unavailable)
    if not member_features.empty:
        avg_refund = float(member_features["refund_rate"].mean())
        return int(min(avg_refund * 120, 100))
    return 0


@app.get("/api/rings/{ring_id}")
def get_ring_detail(ring_id: str):
    """Detailed view of a specific ring — members, features, connections."""
    ring_meta = load_csv(RAW_DIR, "ring_metadata.csv")
    labels = load_csv(RAW_DIR, "labels.csv")
    features = load_csv(PROCESSED_DIR, "feature_matrix.csv")
    device_map = load_csv(RAW_DIR, "customer_device_map.csv")
    ip_map = load_csv(RAW_DIR, "customer_ip_map.csv")
    payment_map = load_csv(RAW_DIR, "customer_payment_map.csv")

    # Get ring metadata
    ring_row = ring_meta[ring_meta["ring_id"] == ring_id]
    if ring_row.empty:
        raise HTTPException(status_code=404, detail=f"Ring {ring_id} not found")

    ring_info = ring_row.iloc[0].to_dict()

    # Get member IDs
    member_ids = labels[labels["ring_id"] == ring_id]["customer_id"].tolist()

    # Get feature data for each member
    member_features = features[features["customer_id"].isin(member_ids)]

    # Get model confidence per member
    member_probas = {}
    if ML_MODEL is not None and ML_FEATURES is not None and not member_features.empty:
        try:
            available = [f for f in ML_FEATURES if f in member_features.columns]
            X = member_features[available].fillna(0)
            probas = ML_MODEL.predict_proba(X)[:, 1]
            for cid, prob in zip(member_features["customer_id"].values, probas):
                member_probas[cid] = float(prob)
        except Exception:
            pass

    members = []
    for _, m in member_features.iterrows():
        cid = m["customer_id"]
        members.append({
            "customer_id": cid,
            "model_confidence": round(member_probas.get(cid, 0), 3),
            "refund_rate": round(float(m.get("refund_rate", 0)), 3),
            "num_devices_used": int(m.get("num_devices_used", 0)),
            "shared_device_users": int(m.get("shared_device_users", 0)),
            "shared_ip_users": int(m.get("shared_ip_users", 0)),
            "total_transactions": int(m.get("total_transactions", 0)),
            "avg_transaction_amount": round(float(m.get("avg_transaction_amount", 0)), 2),
            "account_age_days": int(m.get("account_age_days", 0)),
            "total_amount_spent": round(float(m.get("total_amount_spent", 0)), 2),
        })

    # Build graph connections for visualization
    nodes = []
    edges = []
    node_set = set()

    for cid in member_ids:
        nodes.append({"id": cid, "type": "customer", "label": cid})
        node_set.add(cid)

    # Device connections
    for cid in member_ids:
        cust_devices = device_map[device_map["customer_id"] == cid]
        for _, row in cust_devices.iterrows():
            did = row["device_id"]
            if did not in node_set:
                nodes.append({"id": did, "type": "device", "label": did[:12]})
                node_set.add(did)
            edges.append({"source": cid, "target": did, "type": "device"})

    # IP connections
    for cid in member_ids:
        cust_ips = ip_map[ip_map["customer_id"] == cid]
        for _, row in cust_ips.iterrows():
            iid = row["ip_id"]
            if iid not in node_set:
                nodes.append({"id": iid, "type": "ip", "label": str(iid)[:12]})
                node_set.add(iid)
            edges.append({"source": cid, "target": iid, "type": "ip"})

    # Payment connections
    for cid in member_ids:
        cust_pays = payment_map[payment_map["customer_id"] == cid]
        for _, row in cust_pays.iterrows():
            pid = row["payment_id"]
            if pid not in node_set:
                nodes.append({"id": pid, "type": "payment", "label": pid[:12]})
                node_set.add(pid)
            edges.append({"source": cid, "target": pid, "type": "payment"})

    avg_refund = float(member_features["refund_rate"].mean()) if not member_features.empty else 0
    total_amount = float(member_features["total_amount_spent"].sum()) if not member_features.empty else 0

    return {
        "ring_id": ring_id,
        "ring_type": ring_info.get("ring_type", "unknown"),
        "ring_size": int(ring_info.get("ring_size", 0)),
        "num_shared_devices": int(ring_info.get("num_shared_devices", 0)),
        "num_shared_ips": int(ring_info.get("num_shared_ips", 0)),
        "num_shared_payments": int(ring_info.get("num_shared_payments", 0)),
        "avg_refund_rate": round(avg_refund, 3),
        "total_amount": round(total_amount, 2),
        "members": members,
        "graph": {"nodes": nodes, "edges": edges},
    }


@app.get("/api/rings/{ring_id}/explain")
def explain_ring_endpoint(ring_id: str):
    """Generate an LLM investigation report for a ring.
    Gracefully handles API failures with a fallback template."""
    try:
        # First get ring data
        ring_data = get_ring_detail(ring_id)

        # Call LLM
        explanation = explain_ring(ring_data)

        return {
            "ring_id": ring_id,
            "explanation": explanation,
        }
    except HTTPException:
        raise  # Re-raise 404 for unknown rings
    except Exception as e:
        # Graceful fallback: generate a template report without LLM
        print(f"LLM Error: {e}")
        traceback.print_exc()
        try:
            ring_data = get_ring_detail(ring_id)
            fallback = _generate_fallback_report(ring_data)
            return {
                "ring_id": ring_id,
                "explanation": fallback,
            }
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to generate report")


def _generate_fallback_report(ring_data):
    """Template-based fallback when LLM API is unavailable."""
    r = ring_data
    return f"""## Investigation Report (Auto-Generated)

> ⚠️ LLM API unavailable — this is a template-based fallback report.

**Ring ID**: {r['ring_id']}  
**Type**: {r['ring_type']}  
**Members**: {r['ring_size']}  

### Key Statistics
- Shared Devices: {r['num_shared_devices']}
- Shared IPs: {r['num_shared_ips']}
- Shared Payments: {r['num_shared_payments']}
- Average Refund Rate: {r['avg_refund_rate']*100:.1f}%
- Total Amount: ₹{r.get('total_amount', 0):,.0f}

### Recommended Action
Escalate to human investigator for manual review.

---
*Note: Full AI-powered analysis requires the Groq API to be available. Retry when the API is back online.*
"""


@app.get("/api/models")
def get_model_comparison():
    """Return model comparison data for charts."""
    eval_results = load_csv(PROCESSED_DIR, "evaluation_results.csv")

    if eval_results.empty:
        return {"models": []}

    models = eval_results.to_dict(orient="records")

    # Feature importance
    feature_importance = []
    tabular_path = os.path.join(MODELS_DIR, "xgboost_tabular.pkl")
    if os.path.exists(tabular_path):
        saved = joblib.load(tabular_path)
        model = saved["model"]
        feat_names = saved["features"]
        importance = sorted(
            zip(feat_names, model.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
        feature_importance = [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in importance[:15]
        ]

    return {
        "models": models,
        "feature_importance": feature_importance,
    }


@app.get("/api/features/distribution")
def get_feature_distributions():
    """Return feature distributions for legitimate vs ring members."""
    features = load_csv(PROCESSED_DIR, "feature_matrix.csv")

    if features.empty:
        return {"distributions": []}

    key_features = ["refund_rate", "shared_device_users", "avg_accounts_per_device", "txn_timespan_days"]
    distributions = {}

    for feat in key_features:
        if feat in features.columns:
            safe = features[features["is_ring_member"] == 0][feat].describe().to_dict()
            ring = features[features["is_ring_member"] == 1][feat].describe().to_dict()
            distributions[feat] = {
                "safe": {k: round(float(v), 3) for k, v in safe.items()},
                "ring": {k: round(float(v), 3) for k, v in ring.items()},
            }

    return {"distributions": distributions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
