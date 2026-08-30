"""
Evaluation Framework — tests all models on the held-out test set.

Produces:
- Precision, Recall, F1 for each model
- False positive count and estimated cost
- Comparison table (Rules vs XGBoost vs Graph+ML)
- Per-ring-type breakdown
"""
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from ml_pipeline.train_models import rules_baseline_predict, TABULAR_FEATURES, GRAPH_FEATURES, LABEL_COL


def evaluate_model(name, y_true, y_pred):
    """Calculate and print all metrics for a model."""
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # False-positive cost estimation:
    # If we wrongly block a legitimate customer, we lose their future transactions.
    # Assume avg customer value = ₹5,000/month → ₹60,000/year
    avg_customer_value = 60000  # ₹/year
    fp_cost = fp * avg_customer_value

    print(f"\n{'─' * 50}")
    print(f"📊 {name}")
    print(f"{'─' * 50}")
    print(f"   Precision:       {precision:.3f}  ({precision*100:.1f}%)")
    print(f"   Recall:          {recall:.3f}  ({recall*100:.1f}%)")
    print(f"   F1 Score:        {f1:.3f}  ({f1*100:.1f}%)")
    print(f"")
    print(f"   True Positives:  {tp}  (correctly caught ring members)")
    print(f"   True Negatives:  {tn}  (correctly cleared safe users)")
    print(f"   False Positives: {fp}  (wrongly flagged safe users) ⚠️")
    print(f"   False Negatives: {fn}  (missed ring members) ⚠️")
    print(f"")
    print(f"   Estimated FP Cost: ₹{fp_cost:,.0f}")

    return {
        "model": name,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "fp_cost_inr": fp_cost,
    }


def run_evaluation():
    """Main evaluation pipeline — runs on the HELD-OUT test set (never seen during training)."""
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

    print("=" * 60)
    print("📋 Model Evaluation — Held-Out Test Set")
    print("=" * 60)

    # Load test set
    test = pd.read_csv(os.path.join(processed_dir, "test.csv"))
    y_test = test[LABEL_COL]

    print(f"\nTest set: {len(test)} customers")
    print(f"   Ring members: {y_test.sum()} ({y_test.mean()*100:.1f}%)")
    print(f"   Safe users:   {(y_test == 0).sum()} ({(1-y_test.mean())*100:.1f}%)")

    results = []

    # ── Model 1: Rules Baseline ──
    print("\n" + "=" * 60)
    print("Evaluating Model 1: Rules Baseline")
    rules_preds = rules_baseline_predict(test)
    r1 = evaluate_model("📏 Rules Baseline", y_test, rules_preds)
    results.append(r1)

    # ── Model 2: XGBoost Tabular ──
    print("\n" + "=" * 60)
    print("Evaluating Model 2: XGBoost (Tabular)")
    tabular_path = os.path.join(models_dir, "xgboost_tabular.pkl")
    if os.path.exists(tabular_path):
        saved = joblib.load(tabular_path)
        model_tabular = saved["model"]
        features = saved["features"]
        
        # Ensure all needed features exist
        available = [f for f in features if f in test.columns]
        X_test = test[available]
        tabular_preds = model_tabular.predict(X_test)
        r2 = evaluate_model("🌲 XGBoost (Tabular)", y_test, tabular_preds)
        results.append(r2)
    else:
        print("   ❌ xgboost_tabular.pkl not found. Train models first.")

    # ── Model 3: XGBoost + Graph ──
    print("\n" + "=" * 60)
    print("Evaluating Model 3: XGBoost (Tabular + Graph)")
    graph_path = os.path.join(models_dir, "xgboost_graph.pkl")
    if os.path.exists(graph_path):
        saved = joblib.load(graph_path)
        model_graph = saved["model"]
        features = saved["features"]
        
        available = [f for f in features if f in test.columns]
        X_test = test[available]
        graph_preds = model_graph.predict(X_test)
        r3 = evaluate_model("🕸️ XGBoost (Graph + ML)", y_test, graph_preds)
        results.append(r3)
    else:
        print("   ⚠️  xgboost_graph.pkl not found (graph features not added yet)")

    # ── Model 4: Isolation Forest ──
    print("\n" + "=" * 60)
    print("Evaluating Model 4: Isolation Forest (Anomaly Detection)")
    iso_path = os.path.join(models_dir, "isolation_forest.pkl")
    iso_preds = None
    if os.path.exists(iso_path):
        saved = joblib.load(iso_path)
        model_iso = saved["model"]
        iso_features = saved["features"]
        
        available = [f for f in iso_features if f in test.columns]
        iso_raw = model_iso.predict(test[available])
        iso_preds = np.where(iso_raw == -1, 1, 0)  # -1 (anomaly) → 1 (ring member)
        r4 = evaluate_model("🔍 Isolation Forest", y_test, iso_preds)
        results.append(r4)
    else:
        print("   ❌ isolation_forest.pkl not found.")

    # ── Model 5: Ensemble (XGBoost + Isolation Forest) ──
    print("\n" + "=" * 60)
    print("Evaluating Model 5: Ensemble (XGBoost + Isolation Forest)")
    if os.path.exists(graph_path) and iso_preds is not None:
        # Ensemble: flag if EITHER model flags
        ensemble_preds = np.where(
            (graph_preds == 1) | (iso_preds == 1), 1, 0
        )
        r5 = evaluate_model("🤝 Ensemble (XGB+IF)", y_test, ensemble_preds)
        results.append(r5)
    elif iso_preds is not None and 'tabular_preds' in dir():
        ensemble_preds = np.where(
            (tabular_preds == 1) | (iso_preds == 1), 1, 0
        )
        r5 = evaluate_model("🤝 Ensemble (XGB+IF)", y_test, ensemble_preds)
        results.append(r5)
    else:
        print("   ❌ Cannot create ensemble — missing models.")

    # ── Comparison Table ──
    print("\n\n" + "=" * 60)
    print("🏆 MODEL COMPARISON TABLE")
    print("=" * 60)

    comparison = pd.DataFrame(results)
    print(f"\n{'Model':<30} {'Precision':>10} {'Recall':>10} {'F1':>10} {'FP':>8} {'FP Cost':>15}")
    print("─" * 85)
    for _, row in comparison.iterrows():
        print(f"{row['model']:<30} {row['precision']:>10.3f} {row['recall']:>10.3f} "
              f"{row['f1']:>10.3f} {row['false_positives']:>8} ₹{row['fp_cost_inr']:>12,.0f}")

    # Save results
    comparison.to_csv(os.path.join(processed_dir, "evaluation_results.csv"), index=False)
    print(f"\n✅ Results saved to evaluation_results.csv")

    # ── Feature Importance (for XGBoost Tabular) ──
    if os.path.exists(tabular_path):
        print("\n" + "=" * 60)
        print("🔑 TOP 10 MOST IMPORTANT FEATURES")
        print("=" * 60)
        saved = joblib.load(tabular_path)
        model = saved["model"]
        features = saved["features"]
        
        importance = pd.DataFrame({
            "feature": features,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

        for i, row in importance.head(10).iterrows():
            bar = "█" * int(row["importance"] * 50)
            print(f"   {row['feature']:<30} {row['importance']:.4f} {bar}")

    print("\n" + "=" * 60)
    print("✅ Evaluation complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()
