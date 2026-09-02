import pandas as pd, joblib, os, numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, accuracy_score

processed = 'data/processed'
models_dir = 'models'

train = pd.read_csv(os.path.join(processed, 'train.csv'))
val = pd.read_csv(os.path.join(processed, 'validation.csv'))
test = pd.read_csv(os.path.join(processed, 'test.csv'))
features = pd.read_csv(os.path.join(processed, 'feature_matrix.csv'))

print('=== DATASET STATS ===')
print(f'Total customers: {len(features)}')
ring_count = features.is_ring_member.sum()
safe_count = (features.is_ring_member==0).sum()
print(f'Ring members: {ring_count} ({features.is_ring_member.mean()*100:.1f}%)')
print(f'Safe users: {safe_count} ({(1-features.is_ring_member.mean())*100:.1f}%)')
print(f'Train: {len(train)} | Val: {len(val)} | Test: {len(test)}')
exclude = ["customer_id", "is_ring_member"]
feat_cols = [c for c in features.columns if c not in exclude]
print(f'Features: {len(feat_cols)}')
print()

print('=== FEATURES ===')
for c in feat_cols:
    print(f'  {c}')
print()

eval_results = pd.read_csv(os.path.join(processed, 'evaluation_results.csv'))
# Clean emoji from model names for safe printing
eval_results['model'] = eval_results['model'].apply(lambda x: x.encode('ascii', 'ignore').decode('ascii').strip())
print('=== EVALUATION RESULTS ===')
print(eval_results.to_string(index=False))
print()

saved = joblib.load(os.path.join(models_dir, 'xgboost_tabular.pkl'))
model = saved['model']
feats = saved['features']
X_test = test[[f for f in feats if f in test.columns]]
y_test = test['is_ring_member']
preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:,1]

tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
print('=== XGBOOST TABULAR (TEST SET) ===')
print(f'Accuracy: {accuracy_score(y_test, preds):.4f}')
print(f'Precision: {precision_score(y_test, preds):.4f}')
print(f'Recall: {recall_score(y_test, preds):.4f}')
print(f'F1: {f1_score(y_test, preds):.4f}')
print(f'TP={tp} FP={fp} FN={fn} TN={tn}')
print()

importance = sorted(zip(feats, model.feature_importances_), key=lambda x: x[1], reverse=True)
print('=== FEATURE IMPORTANCE ===')
for f, v in importance:
    print(f'  {f:35s} {v:.4f}')
print()

raw_dir = 'data/raw'
rings = pd.read_csv(os.path.join(raw_dir, 'ring_metadata.csv'))
print('=== RING STATS ===')
print(f'Total rings: {len(rings)}')
print(f'Ring types: {rings.ring_type.value_counts().to_dict()}')
print(f'Avg ring size: {rings.ring_size.mean():.1f}')
print(f'Min ring size: {rings.ring_size.min()}')
print(f'Max ring size: {rings.ring_size.max()}')
print()

# Graph model too
graph_path = os.path.join(models_dir, 'xgboost_graph.pkl')
if os.path.exists(graph_path):
    saved_g = joblib.load(graph_path)
    model_g = saved_g['model']
    feats_g = saved_g['features']
    avail = [f for f in feats_g if f in test.columns]
    preds_g = model_g.predict(test[avail])
    tn2, fp2, fn2, tp2 = confusion_matrix(y_test, preds_g).ravel()
    print('=== XGBOOST GRAPH (TEST SET) ===')
    print(f'Precision: {precision_score(y_test, preds_g):.4f}')
    print(f'Recall: {recall_score(y_test, preds_g):.4f}')
    print(f'F1: {f1_score(y_test, preds_g):.4f}')
    print(f'TP={tp2} FP={fp2} FN={fn2} TN={tn2}')

# Iso forest
iso_path = os.path.join(models_dir, 'isolation_forest.pkl')
if os.path.exists(iso_path):
    saved_i = joblib.load(iso_path)
    model_i = saved_i['model']
    feats_i = saved_i['features']
    avail_i = [f for f in feats_i if f in test.columns]
    iso_raw = model_i.predict(test[avail_i])
    iso_preds = np.where(iso_raw == -1, 1, 0)
    tn3, fp3, fn3, tp3 = confusion_matrix(y_test, iso_preds).ravel()
    print()
    print('=== ISOLATION FOREST (TEST SET) ===')
    print(f'Precision: {precision_score(y_test, iso_preds):.4f}')
    print(f'Recall: {recall_score(y_test, iso_preds):.4f}')
    print(f'F1: {f1_score(y_test, iso_preds):.4f}')
    print(f'TP={tp3} FP={fp3} FN={fn3} TN={tn3}')
