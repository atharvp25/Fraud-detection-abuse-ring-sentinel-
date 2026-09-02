"""
Final validation script — addresses all of Sonnet's criticisms.
Runs on the current V2 data to produce honest numbers.
"""
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from ml_pipeline.train_models import TABULAR_FEATURES, GRAPH_FEATURES

print("=" * 60)
print("VALIDATION TESTS ON FINAL V2 DATA")
print("=" * 60)

train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
labels = pd.read_csv("data/raw/labels.csv")

all_features = [f for f in TABULAR_FEATURES + GRAPH_FEATURES if f in train.columns]
tab_features = [f for f in TABULAR_FEATURES if f in train.columns]
X_train, y_train = train[all_features], train["is_ring_member"]
X_test, y_test = test[all_features], test["is_ring_member"]

# ══════════════════════════════════════════════════
# TEST 1: Shuffled-Label Test
# ══════════════════════════════════════════════════
print("\n[TEST 1] Shuffled-Label Test")
np.random.seed(42)
y_shuffled = np.random.permutation(y_train)
shuffled_model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, eval_metric="logloss")
shuffled_model.fit(X_train, y_shuffled, verbose=False)
preds = shuffled_model.predict(X_test)
shuf_f1 = f1_score(y_test, preds)
print(f"  F1 on test with shuffled labels: {shuf_f1:.4f}")
if shuf_f1 < 0.10:
    print("  ✅ PASS — Model learns real signal, not noise")
else:
    print("  ⚠️ FAIL — Model may be exploiting data artifacts")

# ══════════════════════════════════════════════════
# TEST 2: Clean Mule vs Non-Mule Recall
# ══════════════════════════════════════════════════
print("\n[TEST 2] Clean Mule vs Non-Mule Recall")

# Train both models fresh
num_safe = (y_train == 0).sum()
num_ring = (y_train == 1).sum()
sw = num_safe / max(num_ring, 1)

tab_model = XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    scale_pos_weight=sw, min_child_weight=5, subsample=0.8,
    colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, eval_metric="logloss"
)
tab_model.fit(train[tab_features], y_train, verbose=False)
tab_preds = tab_model.predict(test[tab_features])

graph_model = XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    scale_pos_weight=sw, min_child_weight=5, subsample=0.8,
    colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, eval_metric="logloss"
)
graph_model.fit(train[all_features], y_train, verbose=False)
graph_preds = graph_model.predict(test[all_features])

# Merge labels to identify ring members and their types
test_with_labels = test.merge(
    labels[["customer_id", "ring_id", "customer_type"]],
    on="customer_id", how="left"
)
test_with_labels["tab_pred"] = tab_preds
test_with_labels["graph_pred"] = graph_preds

ring_test = test_with_labels[test_with_labels["is_ring_member"] == 1].copy()

print(f"  Total ring members in test: {len(ring_test)}")

# Check for clean mules by looking at customer_type
ring_test["is_clean_mule"] = ring_test["customer_type"].str.contains("clean", case=False, na=False)
clean_count = ring_test["is_clean_mule"].sum()

if clean_count > 0:
    clean = ring_test[ring_test["is_clean_mule"]]
    regular = ring_test[~ring_test["is_clean_mule"]]
    
    print(f"  Clean mules: {len(clean)} | Regular members: {len(regular)}")
    
    ct = int(clean["tab_pred"].sum())
    cg = int(clean["graph_pred"].sum())
    print(f"\n  CLEAN MULE recall:")
    print(f"    Tabular: {ct}/{len(clean)} = {clean['tab_pred'].mean():.3f}")
    print(f"    Graph:   {cg}/{len(clean)} = {clean['graph_pred'].mean():.3f}")
    
    rt = int(regular["tab_pred"].sum())
    rg = int(regular["graph_pred"].sum())
    print(f"\n  REGULAR MEMBER recall:")
    print(f"    Tabular: {rt}/{len(regular)} = {regular['tab_pred'].mean():.3f}")
    print(f"    Graph:   {rg}/{len(regular)} = {regular['graph_pred'].mean():.3f}")
else:
    print("  customer_type doesn't contain 'clean' tag. Using proxy: shared_device_users <= 1")
    # Proxy: ring members with very low device sharing = likely clean mules
    low_sharing = ring_test[ring_test["shared_device_users"] <= 1]
    high_sharing = ring_test[ring_test["shared_device_users"] > 1]
    
    print(f"  Low-sharing ring members (proxy clean mules): {len(low_sharing)}")
    print(f"  High-sharing ring members: {len(high_sharing)}")
    
    if len(low_sharing) > 0:
        lt = int(low_sharing["tab_pred"].sum())
        lg = int(low_sharing["graph_pred"].sum())
        print(f"\n  LOW-SHARING (proxy clean mule) recall:")
        print(f"    Tabular: {lt}/{len(low_sharing)} = {low_sharing['tab_pred'].mean():.3f}")
        print(f"    Graph:   {lg}/{len(low_sharing)} = {low_sharing['graph_pred'].mean():.3f}")
    
    if len(high_sharing) > 0:
        ht = int(high_sharing["tab_pred"].sum())
        hg = int(high_sharing["graph_pred"].sum())
        print(f"\n  HIGH-SHARING recall:")
        print(f"    Tabular: {ht}/{len(high_sharing)} = {high_sharing['tab_pred'].mean():.3f}")
        print(f"    Graph:   {hg}/{len(high_sharing)} = {high_sharing['graph_pred'].mean():.3f}")

# Overall comparison
print(f"\n  OVERALL TEST METRICS:")
print(f"    Tabular  → P: {precision_score(y_test, tab_preds):.3f}  R: {recall_score(y_test, tab_preds):.3f}  F1: {f1_score(y_test, tab_preds):.3f}")
print(f"    Graph    → P: {precision_score(y_test, graph_preds):.3f}  R: {recall_score(y_test, graph_preds):.3f}  F1: {f1_score(y_test, graph_preds):.3f}")

# ══════════════════════════════════════════════════
# TEST 3: Hold-Out-By-Ring-Type
# ══════════════════════════════════════════════════
print("\n\n[TEST 3] Hold-Out-By-Ring-Type Test")
print("  Training on 5 ring types, testing on 2 unseen types")

# Get ring type metadata
ring_meta = pd.read_csv("data/raw/ring_metadata.csv")
all_types = ring_meta["ring_type"].unique()
print(f"  All ring types: {list(all_types)}")

# Hold out stealth_ring and triangulation (the sneakiest types)
holdout_types = ["stealth_ring", "triangulation"]
train_types = [t for t in all_types if t not in holdout_types]
print(f"  Train types: {train_types}")
print(f"  Holdout types: {holdout_types}")

# Get ring_ids for each group
holdout_ring_ids = set(ring_meta[ring_meta["ring_type"].isin(holdout_types)]["ring_id"])
train_ring_ids = set(ring_meta[ring_meta["ring_type"].isin(train_types)]["ring_id"])

# Build full feature matrix with ring info
full_features = pd.read_csv("data/processed/feature_matrix.csv")
full_with_labels = full_features.merge(labels[["customer_id", "ring_id"]], on="customer_id", how="left")

# Split: ring members by ring_type, non-ring randomly
holdout_mask = full_with_labels["ring_id"].isin(holdout_ring_ids)
train_type_mask = full_with_labels["ring_id"].isin(train_ring_ids)
non_ring_mask = full_with_labels["ring_id"].isna()

# Training set: train-type ring members + 80% of non-ring
np.random.seed(42)
non_ring_indices = full_with_labels[non_ring_mask].index.values
np.random.shuffle(non_ring_indices)
nr_split = int(len(non_ring_indices) * 0.8)

type_train_idx = list(full_with_labels[train_type_mask].index) + list(non_ring_indices[:nr_split])
type_test_idx = list(full_with_labels[holdout_mask].index) + list(non_ring_indices[nr_split:])

type_train = full_features.loc[type_train_idx]
type_test = full_features.loc[type_test_idx]

X_type_train = type_train[tab_features]
y_type_train = type_train["is_ring_member"]
X_type_test = type_test[tab_features]
y_type_test = type_test["is_ring_member"]

print(f"\n  Type-train set: {len(type_train)} ({y_type_train.sum()} ring members)")
print(f"  Type-test set:  {len(type_test)} ({y_type_test.sum()} ring members)")

type_model = XGBClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    scale_pos_weight=(y_type_train == 0).sum() / max((y_type_train == 1).sum(), 1),
    min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=1.0, random_state=42, eval_metric="logloss"
)
type_model.fit(X_type_train, y_type_train, verbose=False)
type_preds = type_model.predict(X_type_test)

print(f"\n  Results on UNSEEN ring types ({holdout_types}):")
print(f"    Precision: {precision_score(y_type_test, type_preds):.3f}")
print(f"    Recall:    {recall_score(y_type_test, type_preds):.3f}")
print(f"    F1:        {f1_score(y_type_test, type_preds):.3f}")

# Per-type breakdown
for htype in holdout_types:
    h_rings = set(ring_meta[ring_meta["ring_type"] == htype]["ring_id"])
    h_members = full_with_labels[full_with_labels["ring_id"].isin(h_rings)]
    h_test_members = type_test.loc[type_test.index.isin(h_members.index)]
    if len(h_test_members) > 0:
        h_preds = type_model.predict(h_test_members[tab_features])
        h_recall = recall_score(h_test_members["is_ring_member"], h_preds)
        caught = int(h_preds.sum())
        total = len(h_test_members)
        print(f"    {htype}: {caught}/{total} caught (recall={h_recall:.3f})")

# ══════════════════════════════════════════════════
# TEST 4: Feature Importance Distribution
# ══════════════════════════════════════════════════
print("\n\n[TEST 4] Feature Importance (Top 10)")
importances = sorted(zip(all_features, graph_model.feature_importances_), key=lambda x: x[1], reverse=True)
for feat, imp in importances[:10]:
    bar = "█" * int(imp * 50)
    print(f"  {feat:<35} {imp:.4f} {bar}")

print("\n  Graph features specifically:")
for feat, imp in importances:
    if "graph" in feat:
        print(f"  {feat:<35} {imp:.4f}")

# ══════════════════════════════════════════════════
# TEST 5: Model probability output (for risk score fix)
# ══════════════════════════════════════════════════
print("\n\n[TEST 5] XGBoost predict_proba() Sample")
probas = tab_model.predict_proba(test[tab_features])[:, 1]
ring_probas = probas[y_test == 1]
safe_probas = probas[y_test == 0]
print(f"  Ring member probabilities: min={ring_probas.min():.3f} median={np.median(ring_probas):.3f} max={ring_probas.max():.3f}")
print(f"  Safe user probabilities:   min={safe_probas.min():.3f} median={np.median(safe_probas):.3f} max={safe_probas.max():.3f}")

print("\n" + "=" * 60)
print("DONE — Use these numbers honestly in your presentation.")
print("=" * 60)
