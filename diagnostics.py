import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
from ml_pipeline.train_models import TABULAR_FEATURES, GRAPH_FEATURES

def run_diagnostics():
    print("="*60)
    print("DIAGNOSTICS REPORT")
    print("="*60)

    # Load data
    train = pd.read_csv("data/processed/train.csv")
    test = pd.read_csv("data/processed/test.csv")
    features = pd.read_csv("data/processed/feature_matrix.csv")

    available_features = [f for f in TABULAR_FEATURES + GRAPH_FEATURES if f in train.columns]
    X_train, y_train = train[available_features], train["is_ring_member"]
    X_test, y_test = test[available_features], test["is_ring_member"]

    # 1. Feature Importance
    print("\n[1] Feature Importance (XGBoost)")
    model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)
    importances = list(zip(available_features, model.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    for feat, imp in importances[:5]:
        print(f"    {feat}: {imp:.4f}")

    # 2. Shuffled Label Test
    print("\n[2] Shuffled-Label Test")
    y_train_shuffled = np.random.permutation(y_train)
    shuffled_model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, use_label_encoder=False, eval_metric="logloss")
    shuffled_model.fit(X_train, y_train_shuffled)
    preds_shuffled = shuffled_model.predict(X_test)
    print(f"    F1 Score on test with shuffled labels: {f1_score(y_test, preds_shuffled):.4f}")

    # 3. Train/Test Split Grouping Leakage
    print("\n[3] Train/Test Split Grouping Leakage")
    # Check if members of the same ring exist in both train and test
    train_rings = set(train[train["is_ring_member"] == 1]["customer_id"].values) # Wait, we need ring_id, not in processed data?
    # Let's check raw labels
    labels = pd.read_csv("data/raw/labels.csv")
    train_with_rings = train.merge(labels[["customer_id", "ring_id"]], on="customer_id", how="left")
    test_with_rings = test.merge(labels[["customer_id", "ring_id"]], on="customer_id", how="left")
    
    train_ring_ids = set(train_with_rings[train_with_rings["is_ring_member"] == 1]["ring_id"].dropna())
    test_ring_ids = set(test_with_rings[test_with_rings["is_ring_member"] == 1]["ring_id"].dropna())
    overlap = train_ring_ids.intersection(test_ring_ids)
    print(f"    Total distinct rings in train: {len(train_ring_ids)}")
    print(f"    Total distinct rings in test: {len(test_ring_ids)}")
    print(f"    Rings spanning BOTH train and test (LEAKAGE): {len(overlap)}")

    # 4. Exact Duplicate Rows
    print("\n[4] Exact/Near-Duplicate Rows")
    common_rows = pd.merge(X_train, X_test, how='inner')
    print(f"    Exact duplicate feature vectors between train and test: {len(common_rows)}")

    # 5. Dumb Rule Baseline
    print("\n[5] Dumb-Rule Baseline (shared_device_users > 3)")
    dumb_preds = (X_test["shared_device_users"] > 3).astype(int)
    print(f"    Precision: {precision_score(y_test, dumb_preds):.3f}")
    print(f"    Recall:    {recall_score(y_test, dumb_preds):.3f}")
    print(f"    F1 Score:  {f1_score(y_test, dumb_preds):.3f}")
    
    print("="*60)

if __name__ == "__main__":
    run_diagnostics()
