"""
Main script — runs the entire data generation pipeline.

Usage:
    python -m data_generator.run_generator

This creates all CSV files in data/raw/ and prints dataset statistics.
"""
import os
import random
import pandas as pd
from datetime import datetime

from data_generator.config import DATASET_CONFIG
from data_generator.generate_customers import generate_normal_customers
from data_generator.generate_legitimate_groups import generate_families, generate_offices
from data_generator.generate_rings import generate_abuse_rings
from data_generator.generate_transactions import generate_transactions
from data_generator.generate_network import (
    generate_device_mappings,
    generate_ip_mappings,
    generate_payment_mappings,
)

# Set random seed for reproducibility (same seed = same dataset every time)
SEED = 42
random.seed(SEED)


def run():
    config = DATASET_CONFIG
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("🛡️  ABUSE-RING SENTINEL — Dataset Generator")
    print("=" * 60)

    # ─────────────────────────────────────────────
    # STEP 1: Generate all customer types
    # ─────────────────────────────────────────────
    print("\n[1/6] Generating normal customers...")
    normal_customers = generate_normal_customers(config)
    print(f"       ✅ {len(normal_customers)} normal customers created")

    print("\n[2/6] Generating legitimate groups (families + offices)...")
    start_idx = len(normal_customers)
    family_customers, family_devices, family_ips = generate_families(config, start_idx)
    
    start_idx += len(family_customers)
    office_customers, office_ips = generate_offices(config, start_idx)
    print(f"       ✅ {len(family_customers)} family members ({config['num_families']} families)")
    print(f"       ✅ {len(office_customers)} office workers ({config['num_offices']} offices)")

    print("\n[3/6] Generating abuse rings...")
    start_idx += len(office_customers)
    ring_customers, ring_metadata = generate_abuse_rings(config, start_idx)
    print(f"       ✅ {len(ring_customers)} ring members ({config['num_rings']} rings)")

    # Combine all customers
    all_customers = normal_customers + family_customers + office_customers + ring_customers
    print(f"\n       📊 Total customers: {len(all_customers)}")

    # ─────────────────────────────────────────────
    # STEP 2: Generate device/IP/payment mappings
    # ─────────────────────────────────────────────
    print("\n[4/6] Generating device, IP, and payment mappings...")
    devices, customer_device_map = generate_device_mappings(all_customers, config)
    ip_addresses, customer_ip_map = generate_ip_mappings(all_customers, config)
    payment_instruments, customer_payment_map = generate_payment_mappings(all_customers, config)
    print(f"       ✅ {len(devices)} devices")
    print(f"       ✅ {len(ip_addresses)} IP addresses")
    print(f"       ✅ {len(payment_instruments)} payment instruments")

    # ─────────────────────────────────────────────
    # STEP 3: Generate transactions and refunds
    # ─────────────────────────────────────────────
    print("\n[5/6] Generating transactions and refunds...")
    transactions, refunds = generate_transactions(all_customers, config)
    print(f"       ✅ {len(transactions)} transactions")
    print(f"       ✅ {len(refunds)} refunds")

    # ─────────────────────────────────────────────
    # STEP 4: Prepare clean DataFrames and save CSVs
    # ─────────────────────────────────────────────
    print("\n[6/6] Saving CSV files...")

    # Clean customer data (remove internal _ fields before saving)
    clean_customers = []
    for c in all_customers:
        clean_customers.append({
            "customer_id": c["customer_id"],
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "created_at": c["created_at"],
            "customer_type": c["customer_type"],
            "ring_id": c["ring_id"],
        })

    # Save all CSVs
    pd.DataFrame(clean_customers).to_csv(os.path.join(output_dir, "customers.csv"), index=False)
    pd.DataFrame(transactions).to_csv(os.path.join(output_dir, "transactions.csv"), index=False)
    pd.DataFrame(refunds).to_csv(os.path.join(output_dir, "refunds.csv"), index=False)
    pd.DataFrame(devices).to_csv(os.path.join(output_dir, "devices.csv"), index=False)
    pd.DataFrame(ip_addresses).to_csv(os.path.join(output_dir, "ip_addresses.csv"), index=False)
    pd.DataFrame(payment_instruments).to_csv(os.path.join(output_dir, "payment_instruments.csv"), index=False)
    pd.DataFrame(customer_device_map).to_csv(os.path.join(output_dir, "customer_device_map.csv"), index=False)
    pd.DataFrame(customer_ip_map).to_csv(os.path.join(output_dir, "customer_ip_map.csv"), index=False)
    pd.DataFrame(customer_payment_map).to_csv(os.path.join(output_dir, "customer_payment_map.csv"), index=False)

    # Save labels separately (for ML training)
    labels = []
    for c in all_customers:
        labels.append({
            "customer_id": c["customer_id"],
            "is_ring_member": 1 if c["customer_type"] == "ring_member" else 0,
            "ring_id": c["ring_id"],
            "customer_type": c["customer_type"],
        })
    pd.DataFrame(labels).to_csv(os.path.join(output_dir, "labels.csv"), index=False)

    # Save ring metadata
    ring_meta_list = []
    for rid, meta in ring_metadata.items():
        ring_meta_list.append({
            "ring_id": f"RING_{rid:04d}",
            "ring_type": meta["ring_type"],
            "ring_size": meta["ring_size"],
            "num_shared_devices": len(meta["shared_devices"]),
            "num_shared_ips": len(meta["shared_ips"]),
            "num_shared_payments": len(meta["shared_payments"]),
            "refund_rate": round(meta["refund_rate"], 3),
        })
    pd.DataFrame(ring_meta_list).to_csv(os.path.join(output_dir, "ring_metadata.csv"), index=False)

    print(f"       ✅ All CSVs saved to: {output_dir}")

    # ─────────────────────────────────────────────
    # STEP 5: Print summary statistics
    # ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 DATASET SUMMARY")
    print("=" * 60)

    total = len(all_customers)
    n_normal = len(normal_customers)
    n_family = len(family_customers)
    n_office = len(office_customers)
    n_ring = len(ring_customers)

    print(f"\nCustomers:          {total}")
    print(f"  ├── Normal:       {n_normal} ({n_normal/total*100:.1f}%)")
    print(f"  ├── Family:       {n_family} ({n_family/total*100:.1f}%)")
    print(f"  ├── Office:       {n_office} ({n_office/total*100:.1f}%)")
    print(f"  └── Ring Members: {n_ring} ({n_ring/total*100:.1f}%)")

    print(f"\nTransactions:       {len(transactions)}")
    print(f"Refunds:            {len(refunds)} ({len(refunds)/len(transactions)*100:.1f}% overall)")

    print(f"\nDevices:            {len(devices)}")
    print(f"IP Addresses:       {len(ip_addresses)}")
    print(f"Payment Instruments:{len(payment_instruments)}")

    print(f"\nAbuse Rings:        {config['num_rings']}")
    print(f"Ring Types:")
    for rtype in set(m["ring_type"] for m in ring_metadata.values()):
        count = sum(1 for m in ring_metadata.values() if m["ring_type"] == rtype)
        print(f"  ├── {rtype}: {count} rings")

    print(f"\nFiles saved:")
    for f in os.listdir(output_dir):
        fpath = os.path.join(output_dir, f)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"  ├── {f} ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print("✅ Dataset generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    run()
