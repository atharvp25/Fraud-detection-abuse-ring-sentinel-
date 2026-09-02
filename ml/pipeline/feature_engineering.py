"""
Feature Engineering — converts raw CSV tables into ONE feature matrix for ML.

This is the CRITICAL step:
  8 raw tables → JOIN + COUNT + AGGREGATE → 1 CSV (one row per customer, 20+ features)

The ML model only sees this final CSV. It never touches the raw tables.
"""
import os
import pandas as pd
import numpy as np


def load_raw_data(data_dir):
    """Load all raw CSV files into DataFrames."""
    data = {}
    files = [
        "customers", "transactions", "refunds",
        "customer_device_map", "customer_ip_map", "customer_payment_map",
        "labels"
    ]
    for f in files:
        filepath = os.path.join(data_dir, f"{f}.csv")
        data[f] = pd.read_csv(filepath)
        # Convert date columns
        if "created_at" in data[f].columns:
            data[f]["created_at"] = pd.to_datetime(data[f]["created_at"])
        if "timestamp" in data[f].columns:
            data[f]["timestamp"] = pd.to_datetime(data[f]["timestamp"])
        if "refund_timestamp" in data[f].columns:
            data[f]["refund_timestamp"] = pd.to_datetime(data[f]["refund_timestamp"])

    return data


def build_tabular_features(data):
    """
    Build features from raw tables WITHOUT graph.
    These are the features for our baseline XGBoost model.
    """
    customers = data["customers"]
    transactions = data["transactions"]
    refunds = data["refunds"]
    device_map = data["customer_device_map"]
    ip_map = data["customer_ip_map"]
    payment_map = data["customer_payment_map"]
    labels = data["labels"]

    # Start with customer_id as our base
    features = customers[["customer_id"]].copy()

    # ──────────────────────────────────────────────
    # FEATURE GROUP 1: Account-level features
    # ──────────────────────────────────────────────
    now = pd.Timestamp.now()
    features["account_age_days"] = (now - customers["created_at"]).dt.days

    # ──────────────────────────────────────────────
    # FEATURE GROUP 2: Transaction features
    # ──────────────────────────────────────────────

    # Total transactions per customer
    txn_counts = transactions.groupby("customer_id").size().reset_index(name="total_transactions")
    features = features.merge(txn_counts, on="customer_id", how="left")
    features["total_transactions"] = features["total_transactions"].fillna(0).astype(int)

    # Total refunds per customer
    refund_counts = refunds.groupby("customer_id").size().reset_index(name="total_refunds")
    features = features.merge(refund_counts, on="customer_id", how="left")
    features["total_refunds"] = features["total_refunds"].fillna(0).astype(int)

    # Refund rate = refunds / transactions (THE key signal)
    features["refund_rate"] = np.where(
        features["total_transactions"] > 0,
        features["total_refunds"] / features["total_transactions"],
        0.0
    )

    # Average transaction amount
    avg_amount = transactions.groupby("customer_id")["amount"].mean().reset_index(name="avg_transaction_amount")
    features = features.merge(avg_amount, on="customer_id", how="left")
    features["avg_transaction_amount"] = features["avg_transaction_amount"].fillna(0.0)

    # Max single transaction
    max_amount = transactions.groupby("customer_id")["amount"].max().reset_index(name="max_transaction_amount")
    features = features.merge(max_amount, on="customer_id", how="left")
    features["max_transaction_amount"] = features["max_transaction_amount"].fillna(0.0)

    # Total transaction amount
    total_amount = transactions.groupby("customer_id")["amount"].sum().reset_index(name="total_amount_spent")
    features = features.merge(total_amount, on="customer_id", how="left")
    features["total_amount_spent"] = features["total_amount_spent"].fillna(0.0)

    # Transaction velocity (transactions per day since account creation)
    features["transaction_velocity"] = np.where(
        features["account_age_days"] > 0,
        features["total_transactions"] / features["account_age_days"],
        features["total_transactions"]
    )

    # ──────────────────────────────────────────────
    # FEATURE GROUP 3: Transaction timing features
    # ──────────────────────────────────────────────

    # Time span of transactions (days between first and last transaction)
    txn_timespan = transactions.groupby("customer_id")["timestamp"].agg(["min", "max"])
    txn_timespan["txn_timespan_days"] = (txn_timespan["max"] - txn_timespan["min"]).dt.days
    txn_timespan = txn_timespan["txn_timespan_days"].reset_index()
    features = features.merge(txn_timespan, on="customer_id", how="left")
    features["txn_timespan_days"] = features["txn_timespan_days"].fillna(0).astype(int)

    # ──────────────────────────────────────────────
    # FEATURE GROUP 4: Device/IP/Payment count features
    # ──────────────────────────────────────────────

    # How many unique devices does this customer use?
    devices_per_customer = device_map.groupby("customer_id")["device_id"].nunique().reset_index(name="num_devices_used")
    features = features.merge(devices_per_customer, on="customer_id", how="left")
    features["num_devices_used"] = features["num_devices_used"].fillna(0).astype(int)

    # How many unique IPs?
    ips_per_customer = ip_map.groupby("customer_id")["ip_id"].nunique().reset_index(name="num_ips_used")
    features = features.merge(ips_per_customer, on="customer_id", how="left")
    features["num_ips_used"] = features["num_ips_used"].fillna(0).astype(int)

    # How many unique payment instruments?
    payments_per_customer = payment_map.groupby("customer_id")["payment_id"].nunique().reset_index(name="num_payments_used")
    features = features.merge(payments_per_customer, on="customer_id", how="left")
    features["num_payments_used"] = features["num_payments_used"].fillna(0).astype(int)

    # ──────────────────────────────────────────────
    # FEATURE GROUP 5: SHARED entity counts
    # "How many OTHER customers share my devices/IPs/cards?"
    # ──────────────────────────────────────────────

    shared_devices = _count_shared_entities(device_map, "device_id")
    features = features.merge(shared_devices, on="customer_id", how="left")
    features["shared_device_users"] = features["shared_device_users"].fillna(0).astype(int)

    shared_ips = _count_shared_entities(ip_map, "ip_id")
    features = features.merge(shared_ips, on="customer_id", how="left")
    features["shared_ip_users"] = features["shared_ip_users"].fillna(0).astype(int)

    shared_payments = _count_shared_entities(payment_map, "payment_id")
    features = features.merge(shared_payments, on="customer_id", how="left")
    features["shared_payment_users"] = features["shared_payment_users"].fillna(0).astype(int)

    # Avg accounts per device/IP/payment
    avg_accts_device = _avg_accounts_per_entity(device_map, "device_id")
    features = features.merge(avg_accts_device, on="customer_id", how="left")
    features["avg_accounts_per_device"] = features["avg_accounts_per_device"].fillna(1.0)

    avg_accts_ip = _avg_accounts_per_entity(ip_map, "ip_id")
    features = features.merge(avg_accts_ip, on="customer_id", how="left")
    features["avg_accounts_per_ip"] = features["avg_accounts_per_ip"].fillna(1.0)

    avg_accts_pay = _avg_accounts_per_entity(payment_map, "payment_id")
    features = features.merge(avg_accts_pay, on="customer_id", how="left")
    features["avg_accounts_per_payment"] = features["avg_accounts_per_payment"].fillna(1.0)

    # ──────────────────────────────────────────────
    # Add labels (what we're trying to predict)
    # ──────────────────────────────────────────────
    features = features.merge(
        labels[["customer_id", "is_ring_member"]],
        on="customer_id",
        how="left"
    )

    # ──────────────────────────────────────────────
    # NOISE INJECTION — makes the dataset realistic
    # In real-world data, measurements are never perfect.
    # This prevents any single feature from being a cheat code.
    # ──────────────────────────────────────────────
    features = inject_noise(features)

    return features


def inject_noise(features):
    """
    Add Gaussian noise to numerical features to simulate real-world imprecision.
    
    Why this matters:
    - Synthetic data has perfectly clean separations between classes
    - Real data is messy — device fingerprints can fail, IP tracking is imprecise,
      refund counts have edge cases (partial refunds, cancelled refunds, etc.)
    - Without noise, XGBoost finds a single feature that perfectly separates classes
    - With noise, the model must use COMBINATIONS of features (which is realistic)
    
    Noise levels:
    - High noise (20%) for sharing features (these are inherently uncertain in real life)
    - Medium noise (15%) for transaction features  
    - Low noise (5%) for count features
    """
    np.random.seed(42)  # Reproducible noise

    # High noise: sharing metrics (real-world device fingerprinting is unreliable)
    high_noise_cols = [
        "avg_accounts_per_device", "avg_accounts_per_ip", "avg_accounts_per_payment",
        "shared_device_users", "shared_ip_users", "shared_payment_users",
    ]

    # Medium noise: transaction behavior
    medium_noise_cols = [
        "refund_rate", "avg_transaction_amount", "max_transaction_amount",
        "transaction_velocity", "total_amount_spent",
    ]

    # Low noise: simple counts and dates
    low_noise_cols = [
        "total_transactions", "total_refunds", "txn_timespan_days",
        "num_devices_used", "num_ips_used", "num_payments_used",
        "account_age_days",
    ]

    for col in high_noise_cols:
        if col in features.columns:
            noise = np.random.normal(0, 0.20, len(features))  # ±20%
            features[col] = features[col] * (1 + noise)
            features[col] = features[col].clip(lower=0)  # No negative values

    for col in medium_noise_cols:
        if col in features.columns:
            noise = np.random.normal(0, 0.15, len(features))  # ±15%
            features[col] = features[col] * (1 + noise)
            features[col] = features[col].clip(lower=0)

    for col in low_noise_cols:
        if col in features.columns:
            noise = np.random.normal(0, 0.05, len(features))  # ±5%
            features[col] = features[col] * (1 + noise)
            features[col] = features[col].clip(lower=0)

    # Cap refund_rate at 1.0 (can't have more than 100% refund rate)
    if "refund_rate" in features.columns:
        features["refund_rate"] = features["refund_rate"].clip(upper=1.0)

    print("       🔀 Gaussian noise injected into all features")

    return features


def _count_shared_entities(mapping_df, entity_col):
    """
    For each customer, count how many OTHER customers share at least one entity.
    """
    entity_to_customers = mapping_df.groupby(entity_col)["customer_id"].apply(set).to_dict()

    customer_shared = {}
    for _, row in mapping_df.iterrows():
        cust = row["customer_id"]
        entity = row[entity_col]
        others = entity_to_customers.get(entity, set()) - {cust}
        if cust not in customer_shared:
            customer_shared[cust] = set()
        customer_shared[cust].update(others)

    col_name = f"shared_{entity_col.replace('_id', '')}_users"
    result = pd.DataFrame([
        {"customer_id": cust, col_name: len(others)}
        for cust, others in customer_shared.items()
    ])
    return result


def _avg_accounts_per_entity(mapping_df, entity_col):
    """
    For each customer, calculate the average number of accounts per entity they use.
    """
    entity_counts = mapping_df.groupby(entity_col)["customer_id"].nunique().reset_index(name="count")
    merged = mapping_df.merge(entity_counts, on=entity_col)
    result = merged.groupby("customer_id")["count"].mean().reset_index()
    result.columns = ["customer_id", f"avg_accounts_per_{entity_col.replace('_id', '')}"]
    return result


def save_feature_matrix(features, output_dir):
    """
    Save the feature matrix and create train/val/test splits.
    
    CRITICAL: Uses GROUPED splitting by ring_id to prevent data leakage.
    All members of the same ring go into the SAME split.
    The model is tested on rings it has NEVER seen during training.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load labels to get ring_id for grouped splitting
    raw_dir = os.path.join(os.path.dirname(output_dir), "raw")
    labels = pd.read_csv(os.path.join(raw_dir, "labels.csv"))
    
    # Merge ring_id into features for splitting
    features_with_ring = features.merge(
        labels[["customer_id", "ring_id", "customer_type"]], 
        on="customer_id", how="left"
    )

    features.to_csv(os.path.join(output_dir, "feature_matrix.csv"), index=False)
    print(f"✅ Full feature matrix saved: {len(features)} rows × {len(features.columns)} columns")

    # ── GROUPED SPLIT BY RING_ID (Primary Evaluation) ──
    # All members of the same ring go into the SAME split.
    # All 7 ring types are represented in train and test.
    # This prevents data leakage while testing on unseen ring instances.
    
    ring_ids = features_with_ring[features_with_ring["ring_id"].notna()]["ring_id"].unique()
    np.random.seed(42)
    np.random.shuffle(ring_ids)
    
    # Split rings: 70% train, 15% val, 15% test
    n_rings = len(ring_ids)
    train_ring_end = int(n_rings * 0.70)
    val_ring_end = int(n_rings * 0.85)
    
    train_rings = set(ring_ids[:train_ring_end])
    val_rings = set(ring_ids[train_ring_end:val_ring_end])
    test_rings = set(ring_ids[val_ring_end:])
    
    print(f"\n   Grouped split by ring_id (prevents data leakage):")
    print(f"   Train rings: {len(train_rings)} | Val rings: {len(val_rings)} | Test rings: {len(test_rings)}")
    
    # Step 2: Assign ring members to their group's split
    def assign_split(row):
        if pd.notna(row["ring_id"]):
            if row["ring_id"] in train_rings:
                return "train"
            elif row["ring_id"] in val_rings:
                return "val"
            elif row["ring_id"] in test_rings:
                return "test"
        return None  # Non-ring members assigned later
    
    features_with_ring["split"] = features_with_ring.apply(assign_split, axis=1)
    
    # Step 3: Randomly assign non-ring customers (70/15/15)
    non_ring_mask = features_with_ring["split"].isna()
    non_ring_indices = features_with_ring[non_ring_mask].index.values
    np.random.shuffle(non_ring_indices)
    
    n_non_ring = len(non_ring_indices)
    nr_train_end = int(n_non_ring * 0.70)
    nr_val_end = int(n_non_ring * 0.85)
    
    features_with_ring.loc[non_ring_indices[:nr_train_end], "split"] = "train"
    features_with_ring.loc[non_ring_indices[nr_train_end:nr_val_end], "split"] = "val"
    features_with_ring.loc[non_ring_indices[nr_val_end:], "split"] = "test"
    
    # Step 4: Extract splits (drop the helper columns)
    cols_to_keep = features.columns.tolist()
    
    train = features_with_ring[features_with_ring["split"] == "train"][cols_to_keep].reset_index(drop=True)
    val = features_with_ring[features_with_ring["split"] == "val"][cols_to_keep].reset_index(drop=True)
    test = features_with_ring[features_with_ring["split"] == "test"][cols_to_keep].reset_index(drop=True)
    
    train.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    val.to_csv(os.path.join(output_dir, "validation.csv"), index=False)
    test.to_csv(os.path.join(output_dir, "test.csv"), index=False)

    n = len(features)
    print(f"\n✅ Train:      {len(train)} rows ({len(train)/n*100:.1f}%)")
    print(f"✅ Validation: {len(val)} rows ({len(val)/n*100:.1f}%)")
    print(f"✅ Test:       {len(test)} rows ({len(test)/n*100:.1f}%)")

    for name, split in [("Train", train), ("Val", val), ("Test", test)]:
        ring_pct = split["is_ring_member"].mean() * 100
        print(f"   {name} ring member %: {ring_pct:.1f}%")
    
    # Verify no leakage
    train_cids = set(train[train["is_ring_member"] == 1]["customer_id"])
    test_cids = set(test[test["is_ring_member"] == 1]["customer_id"])
    train_rids = set(features_with_ring[features_with_ring["split"] == "train"]["ring_id"].dropna())
    test_rids = set(features_with_ring[features_with_ring["split"] == "test"]["ring_id"].dropna())
    overlap = train_rids & test_rids
    print(f"\n   🔒 Leakage check: {len(overlap)} rings overlap train/test (should be 0)")

    return train, val, test


if __name__ == "__main__":
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed")

    print("=" * 60)
    print("🔧 Feature Engineering Pipeline")
    print("=" * 60)

    print("\n[1/3] Loading raw data...")
    data = load_raw_data(raw_dir)
    for name, df in data.items():
        print(f"       {name}: {len(df)} rows")

    print("\n[2/3] Building tabular features...")
    features = build_tabular_features(data)

    print(f"\n       📊 Feature Matrix: {len(features)} customers × {len(features.columns)} features")
    print(f"\n       Features created:")
    for col in features.columns:
        if col not in ["customer_id", "is_ring_member"]:
            print(f"         ├── {col}")

    print("\n[3/3] Saving feature matrix and splits...")
    save_feature_matrix(features, processed_dir)

    print("\n" + "=" * 60)
    print("✅ Feature engineering complete!")
    print("=" * 60)
