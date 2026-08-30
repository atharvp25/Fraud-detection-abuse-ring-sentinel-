"""
Model Training — trains 5 models and saves them for comparison.

Model 1 (Baseline):    Simple if/else rules (no ML at all)
Model 2 (Tabular):     XGBoost on tabular features only
Model 3 (Graph+ML):    XGBoost on tabular + graph features
Model 4 (Anomaly):     Isolation Forest (unsupervised — no labels needed)
Model 5 (Ensemble):    XGBoost + Isolation Forest combined

The comparison proves to judges that each layer adds value.
"""
import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report


# ══════════════════════════════════════════════════
# The feature columns we use (excluding customer_id and label)
# ══════════════════════════════════════════════════

TABULAR_FEATURES = [
    "account_age_days",
    "total_transactions",
    "total_refunds",
    "refund_rate",
    "avg_transaction_amount",
    "max_transaction_amount",
    "total_amount_spent",
    "transaction_velocity",
    "txn_timespan_days",
    "num_devices_used",
    "num_ips_used",
    "num_payments_used",
    "shared_device_users",
    "shared_ip_users",
    "shared_payment_users",
    "avg_accounts_per_device",
    "avg_accounts_per_ip",
    "avg_accounts_per_payment",
]

# Graph features will be added later (Day 2 Session 1 continuation)
GRAPH_FEATURES = [
    "graph_degree",
    "graph_component_size",
    "graph_avg_neighbor_refund_rate",
]

LABEL_COL = "is_ring_member"


def load_splits(processed_dir):
    """Load train, validation, and test CSVs."""
    train = pd.read_csv(os.path.join(processed_dir, "train.csv"))
    val = pd.read_csv(os.path.join(processed_dir, "validation.csv"))
    test = pd.read_csv(os.path.join(processed_dir, "test.csv"))
    return train, val, test


# ══════════════════════════════════════════════════
# MODEL 1: Simple Rules Baseline (No ML)
# ══════════════════════════════════════════════════

def rules_baseline_predict(df):
    """
    A simple hand-written rule:
    IF shared_device_users > 1 AND refund_rate > 0.30 → predict fraud (1)
    ELSE → predict safe (0)
    
    This is what a junior analyst might do manually.
    Our ML model needs to BEAT this to prove it's useful.
    """
    predictions = np.zeros(len(df), dtype=int)
    
    mask = (
        (df["shared_device_users"] > 1) &
        (df["refund_rate"] > 0.30)
    )
    predictions[mask] = 1
    
    return predictions


# ══════════════════════════════════════════════════
# MODEL 2: XGBoost on Tabular Features Only
# ══════════════════════════════════════════════════

def train_xgboost_tabular(train, val):
    """
    Train XGBoost using ONLY tabular features (no graph).
    Uses scale_pos_weight to handle class imbalance.
    """
    # Get feature columns that actually exist in the data
    available_features = [f for f in TABULAR_FEATURES if f in train.columns]
    
    X_train = train[available_features]
    y_train = train[LABEL_COL]
    X_val = val[available_features]
    y_val = val[LABEL_COL]

    # Handle class imbalance: tell XGBoost to pay MORE attention to ring members
    num_safe = (y_train == 0).sum()
    num_ring = (y_train == 1).sum()
    scale_weight = num_safe / max(num_ring, 1)  # avoid division by zero

    print(f"   Class balance: {num_safe} safe vs {num_ring} ring members")
    print(f"   scale_pos_weight = {scale_weight:.2f}")

    model = XGBClassifier(
        n_estimators=200,          # 200 trees
        max_depth=4,               # reduced from 6 to prevent overfitting
        learning_rate=0.05,        # slower learning = better generalization
        scale_pos_weight=scale_weight,  # handle imbalance
        min_child_weight=5,        # regularization: min samples per leaf
        subsample=0.8,             # use 80% of data per tree (reduces overfitting)
        colsample_bytree=0.8,      # use 80% of features per tree
        reg_alpha=0.1,             # L1 regularization
        reg_lambda=1.0,            # L2 regularization
        random_state=42,
        eval_metric="logloss",
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False,
    )

    # ── Overfitting check: compare train vs validation ──
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    
    train_f1 = f1_score(y_train, train_preds)
    val_f1 = f1_score(y_val, val_preds)
    overfit_gap = train_f1 - val_f1
    
    print(f"   Train      → P: {precision_score(y_train, train_preds):.3f}  "
          f"R: {recall_score(y_train, train_preds):.3f}  "
          f"F1: {train_f1:.3f}")
    print(f"   Validation → P: {precision_score(y_val, val_preds):.3f}  "
          f"R: {recall_score(y_val, val_preds):.3f}  "
          f"F1: {val_f1:.3f}")
    
    if overfit_gap > 0.05:
        print(f"   ⚠️  OVERFITTING DETECTED! Gap = {overfit_gap:.3f} (train F1 - val F1)")
    elif overfit_gap < -0.02:
        print(f"   ⚠️  UNDERFITTING? Gap = {overfit_gap:.3f}")
    else:
        print(f"   ✅ Good fit. Gap = {overfit_gap:.3f}")

    return model, available_features


# ══════════════════════════════════════════════════
# MODEL 3: XGBoost on Tabular + Graph Features
# ══════════════════════════════════════════════════

def train_xgboost_with_graph(train, val):
    """
    Train XGBoost using tabular + graph features.
    This should perform BETTER than tabular-only, proving graph adds value.
    """
    # Combine tabular + graph features (only those that exist)
    all_features = TABULAR_FEATURES + GRAPH_FEATURES
    available_features = [f for f in all_features if f in train.columns]
    
    X_train = train[available_features]
    y_train = train[LABEL_COL]
    X_val = val[available_features]
    y_val = val[LABEL_COL]

    num_safe = (y_train == 0).sum()
    num_ring = (y_train == 1).sum()
    scale_weight = num_safe / max(num_ring, 1)

    print(f"   Class balance: {num_safe} safe vs {num_ring} ring members")
    print(f"   Using {len(available_features)} features (tabular + graph)")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=scale_weight,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        eval_metric="logloss",
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False,
    )

    # ── Overfitting check ──
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    
    train_f1 = f1_score(y_train, train_preds)
    val_f1 = f1_score(y_val, val_preds)
    overfit_gap = train_f1 - val_f1
    
    print(f"   Train      → P: {precision_score(y_train, train_preds):.3f}  "
          f"R: {recall_score(y_train, train_preds):.3f}  "
          f"F1: {train_f1:.3f}")
    print(f"   Validation → P: {precision_score(y_val, val_preds):.3f}  "
          f"R: {recall_score(y_val, val_preds):.3f}  "
          f"F1: {val_f1:.3f}")
    
    if overfit_gap > 0.05:
        print(f"   ⚠️  OVERFITTING DETECTED! Gap = {overfit_gap:.3f}")
    elif overfit_gap < -0.02:
        print(f"   ⚠️  UNDERFITTING? Gap = {overfit_gap:.3f}")
    else:
        print(f"   ✅ Good fit. Gap = {overfit_gap:.3f}")

    return model, available_features


def run_training():
    """Main training pipeline."""
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)

    print("=" * 60)
    print("🧠 Model Training Pipeline")
    print("=" * 60)

    # Load data
    print("\n[1/6] Loading data splits...")
    train, val, test = load_splits(processed_dir)
    print(f"       Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")

    # ── Model 1: Rules Baseline ──
    print("\n[2/6] 📏 Model 1: Rules Baseline...")
    val_rules_preds = rules_baseline_predict(val)
    y_val = val[LABEL_COL]
    print(f"   Validation → P: {precision_score(y_val, val_rules_preds):.3f}  "
          f"R: {recall_score(y_val, val_rules_preds):.3f}  "
          f"F1: {f1_score(y_val, val_rules_preds):.3f}")

    # ── Model 2: XGBoost Tabular ──
    print("\n[3/6] 🌲 Model 2: XGBoost (Tabular features only)...")
    model_tabular, tabular_feature_names = train_xgboost_tabular(train, val)

    # ── Model 3: XGBoost + Graph ──
    print("\n[4/6] 🕸️  Model 3: XGBoost (Tabular + Graph features)...")
    graph_cols_present = [f for f in GRAPH_FEATURES if f in train.columns]
    if graph_cols_present:
        model_graph, graph_feature_names = train_xgboost_with_graph(train, val)
    else:
        print("   ⚠️  Graph features not found. Skipping Model 3.")
        model_graph = None
        graph_feature_names = None

    # ── Model 4: Isolation Forest (Unsupervised Anomaly Detection) ──
    print("\n[5/6] 🔍 Model 4: Isolation Forest (Anomaly Detection)...")
    all_features = TABULAR_FEATURES + GRAPH_FEATURES
    available_features = [f for f in all_features if f in train.columns]

    # Isolation Forest does NOT use labels — it learns what "normal" looks like
    # and flags anything that deviates. contamination = expected % of anomalies.
    X_train_all = train[available_features]
    
    # Estimate contamination from training data
    ring_pct = train[LABEL_COL].mean()
    contamination = max(0.01, min(ring_pct, 0.15))  # clamp between 1-15%
    
    iso_forest = IsolationForest(
        n_estimators=300,          # 300 trees
        max_samples="auto",        # subsample size
        contamination=contamination,  # expected fraction of anomalies
        random_state=42,
        n_jobs=-1,                 # use all CPU cores
    )
    iso_forest.fit(X_train_all)   # NO labels used!
    
    # Isolation Forest returns -1 for anomaly, 1 for normal → convert to 0/1
    val_iso_raw = iso_forest.predict(val[available_features])
    val_iso_preds = np.where(val_iso_raw == -1, 1, 0)  # -1 (anomaly) → 1 (ring member)
    
    train_iso_raw = iso_forest.predict(X_train_all)
    train_iso_preds = np.where(train_iso_raw == -1, 1, 0)
    
    y_train = train[LABEL_COL]
    train_iso_f1 = f1_score(y_train, train_iso_preds)
    val_iso_f1 = f1_score(y_val, val_iso_preds)
    
    print(f"   Contamination set to: {contamination:.3f}")
    print(f"   Train      → P: {precision_score(y_train, train_iso_preds):.3f}  "
          f"R: {recall_score(y_train, train_iso_preds):.3f}  "
          f"F1: {train_iso_f1:.3f}")
    print(f"   Validation → P: {precision_score(y_val, val_iso_preds):.3f}  "
          f"R: {recall_score(y_val, val_iso_preds):.3f}  "
          f"F1: {val_iso_f1:.3f}")

    # ── Model 5: Ensemble (XGBoost + Isolation Forest) ──
    print("\n[6/6] 🤝 Model 5: Ensemble (XGBoost + Isolation Forest)...")
    
    # Ensemble logic: flag a customer if EITHER model flags them
    # This maximizes recall (catches more fraud) at the cost of some precision
    if model_graph:
        val_xgb_preds = model_graph.predict(val[graph_feature_names])
    else:
        val_xgb_preds = model_tabular.predict(val[tabular_feature_names])
    
    val_ensemble_preds = np.where(
        (val_xgb_preds == 1) | (val_iso_preds == 1), 1, 0
    )
    
    print(f"   Validation → P: {precision_score(y_val, val_ensemble_preds):.3f}  "
          f"R: {recall_score(y_val, val_ensemble_preds):.3f}  "
          f"F1: {f1_score(y_val, val_ensemble_preds):.3f}")

    # ── Save All Models ──
    print("\n💾 Saving models...")
    
    joblib.dump({
        "model": model_tabular,
        "features": tabular_feature_names,
        "model_type": "xgboost_tabular",
    }, os.path.join(models_dir, "xgboost_tabular.pkl"))
    print(f"   ✅ xgboost_tabular.pkl saved")

    if model_graph:
        joblib.dump({
            "model": model_graph,
            "features": graph_feature_names,
            "model_type": "xgboost_graph",
        }, os.path.join(models_dir, "xgboost_graph.pkl"))
        print(f"   ✅ xgboost_graph.pkl saved")

    joblib.dump({
        "model": iso_forest,
        "features": available_features,
        "model_type": "isolation_forest",
    }, os.path.join(models_dir, "isolation_forest.pkl"))
    print(f"   ✅ isolation_forest.pkl saved")

    print("\n" + "=" * 60)
    print("✅ Model training complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_training()
