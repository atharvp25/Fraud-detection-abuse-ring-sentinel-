"""
Main script — runs the entire V2 data generation pipeline.
V2 — 10k customers, 7 ring types, student hostels, corporate cards, noise.

Usage:
    python -m ml.data_generator.run_generator
"""
import os
import random
import pandas as pd

from ml.data_generator.config import DATASET_CONFIG
from ml.data_generator.generate_customers import generate_normal_customers
from ml.data_generator.generate_legitimate_groups import (
    generate_families, generate_offices,
    generate_student_hostels, generate_corporate_card_groups,
)
from ml.data_generator.generate_rings import generate_abuse_rings
from ml.data_generator.generate_transactions import generate_transactions
from ml.data_generator.generate_network import (
    generate_device_mappings,
    generate_ip_mappings,
    generate_payment_mappings,
)

SEED = 42
random.seed(SEED)


def run():
    config = DATASET_CONFIG
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("🛡️  ABUSE-RING SENTINEL — Dataset Generator V2")
    print("=" * 60)

    # ─── STEP 1: Generate all customer types ───
    print("\n[1/6] Generating normal customers...")
    normal_customers = generate_normal_customers(config)
    print(f"       ✅ {len(normal_customers)} normal customers")

    print("\n[2/6] Generating legitimate groups...")
    start_idx = len(normal_customers)
    family_customers, family_devices, family_ips = generate_families(config, start_idx)

    start_idx += len(family_customers)
    office_customers, office_ips = generate_offices(config, start_idx)

    start_idx += len(office_customers)
    student_customers, hostel_devices, hostel_ips = generate_student_hostels(config, start_idx)

    start_idx += len(student_customers)
    corporate_customers, corp_payments = generate_corporate_card_groups(config, start_idx)

    print(f"       ✅ {len(family_customers)} family members ({config['num_families']} families)")
    print(f"       ✅ {len(office_customers)} office workers ({config['num_offices']} offices)")
    print(f"       ✅ {len(student_customers)} students ({config['num_student_hostels']} hostels)")
    print(f"       ✅ {len(corporate_customers)} corporate card users ({config['num_corporate_card_groups']} groups)")

    print("\n[3/6] Generating abuse rings (7 types)...")
    start_idx += len(corporate_customers)
    ring_customers, ring_metadata = generate_abuse_rings(config, start_idx)
    print(f"       ✅ {len(ring_customers)} ring members")

    # Print per-type breakdown
    type_counts = {}
    for meta in ring_metadata.values():
        rtype = meta["ring_type"]
        type_counts[rtype] = type_counts.get(rtype, 0) + meta["ring_size"]
    for rtype, count in type_counts.items():
        print(f"          ├── {rtype}: {count} members")

    # Combine all customers
    all_customers = (normal_customers + family_customers + office_customers +
                     student_customers + corporate_customers + ring_customers)
    print(f"\n       📊 Total customers: {len(all_customers)}")

    # ─── STEP 2: Generate mappings ───
    print("\n[4/6] Generating device, IP, and payment mappings...")
    devices, customer_device_map = generate_device_mappings(all_customers, config)
    ip_addresses, customer_ip_map = generate_ip_mappings(all_customers, config)
    payment_instruments, customer_payment_map = generate_payment_mappings(all_customers, config)
    print(f"       ✅ {len(devices)} devices")
    print(f"       ✅ {len(ip_addresses)} IP addresses")
    print(f"       ✅ {len(payment_instruments)} payment instruments")

    # ─── STEP 3: Generate transactions ───
    print("\n[5/6] Generating transactions and refunds...")
    transactions, refunds = generate_transactions(all_customers, config)
    print(f"       ✅ {len(transactions)} transactions")
    print(f"       ✅ {len(refunds)} refunds")

    # ─── STEP 4: Save CSVs ───
    print("\n[6/6] Saving CSV files...")

    # Clean customer data
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

    pd.DataFrame(clean_customers).to_csv(os.path.join(output_dir, "customers.csv"), index=False)
    pd.DataFrame(transactions).to_csv(os.path.join(output_dir, "transactions.csv"), index=False)
    pd.DataFrame(refunds).to_csv(os.path.join(output_dir, "refunds.csv"), index=False)
    pd.DataFrame(devices).to_csv(os.path.join(output_dir, "devices.csv"), index=False)
    pd.DataFrame(ip_addresses).to_csv(os.path.join(output_dir, "ip_addresses.csv"), index=False)
    pd.DataFrame(payment_instruments).to_csv(os.path.join(output_dir, "payment_instruments.csv"), index=False)
    pd.DataFrame(customer_device_map).to_csv(os.path.join(output_dir, "customer_device_map.csv"), index=False)
    pd.DataFrame(customer_ip_map).to_csv(os.path.join(output_dir, "customer_ip_map.csv"), index=False)
    pd.DataFrame(customer_payment_map).to_csv(os.path.join(output_dir, "customer_payment_map.csv"), index=False)

    # Labels
    labels = []
    for c in all_customers:
        labels.append({
            "customer_id": c["customer_id"],
            "is_ring_member": 1 if c["customer_type"] == "ring_member" else 0,
            "ring_id": c["ring_id"],
            "customer_type": c["customer_type"],
        })
    pd.DataFrame(labels).to_csv(os.path.join(output_dir, "labels.csv"), index=False)

    # Ring metadata
    ring_meta_list = []
    for rid, meta in ring_metadata.items():
        ring_meta_list.append({
            "ring_id": f"RING_{rid:04d}",
            "ring_type": meta["ring_type"],
            "ring_size": meta["ring_size"],
            "num_shared_devices": meta["num_shared_devices"],
            "num_shared_ips": meta["num_shared_ips"],
            "num_shared_payments": meta["num_shared_payments"],
            "refund_rate": round(meta["refund_rate"], 3),
        })
    pd.DataFrame(ring_meta_list).to_csv(os.path.join(output_dir, "ring_metadata.csv"), index=False)

    print(f"       ✅ All CSVs saved to: {output_dir}")

    # ─── STEP 5: Summary ───
    print("\n" + "=" * 60)
    print("📊 DATASET SUMMARY (V2)")
    print("=" * 60)

    total = len(all_customers)
    n_normal = len(normal_customers)
    n_family = len(family_customers)
    n_office = len(office_customers)
    n_student = len(student_customers)
    n_corporate = len(corporate_customers)
    n_ring = len(ring_customers)
    n_legit_sharing = n_family + n_office + n_student + n_corporate

    print(f"\nCustomers:              {total}")
    print(f"  ├── Normal:           {n_normal} ({n_normal/total*100:.1f}%)")
    print(f"  ├── Family:           {n_family} ({n_family/total*100:.1f}%)")
    print(f"  ├── Office:           {n_office} ({n_office/total*100:.1f}%)")
    print(f"  ├── Student:          {n_student} ({n_student/total*100:.1f}%)")
    print(f"  ├── Corporate Card:   {n_corporate} ({n_corporate/total*100:.1f}%)")
    print(f"  └── Ring Members:     {n_ring} ({n_ring/total*100:.1f}%)")
    print(f"\n  Legitimate sharing:   {n_legit_sharing} ({n_legit_sharing/total*100:.1f}%)")

    print(f"\nTransactions:           {len(transactions)}")
    print(f"Refunds:                {len(refunds)} ({len(refunds)/len(transactions)*100:.1f}% overall)")

    print(f"\nDevices:                {len(devices)}")
    print(f"IP Addresses:           {len(ip_addresses)}")
    print(f"Payment Instruments:    {len(payment_instruments)}")

    print(f"\nAbuse Rings:            {sum(config['num_rings_per_type'].values())} total")
    print(f"Ring Types:")
    for rtype, count in config['num_rings_per_type'].items():
        members = type_counts.get(rtype, 0)
        print(f"  ├── {rtype}: {count} rings ({members} members)")

    print(f"\nFiles saved:")
    for f in sorted(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, f)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"  ├── {f} ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print("✅ Dataset V2 generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    run()
