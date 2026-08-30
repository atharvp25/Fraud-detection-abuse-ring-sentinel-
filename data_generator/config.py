"""
Configuration settings for the Synthetic Data Simulator.
V2 — Based on real-world fraud research. 7 ring types, 10k customers, harder edge cases.
"""

DATASET_CONFIG = {
    # 1. Scale of the dataset (increased to ~10k)
    "num_customers": 7000,          # base normal customers
    "num_devices": 5000,
    "num_ips": 3500,
    "num_payment_instruments": 6000,

    # 2. Transaction settings
    "num_transactions_per_normal": (3, 15),
    "num_transactions_per_ring": (3, 12),
    "normal_amount_range": (50, 5000),
    "ring_amount_range": (500, 12000),

    # 3. Legitimate Sharing (The "Good Guys" who look suspicious)
    "num_families": 200,
    "family_size_range": (2, 5),
    "num_offices": 60,
    "office_size_range": (5, 20),
    "num_student_hostels": 50,
    "hostel_size_range": (12, 30),
    "num_corporate_card_groups": 40,
    "corporate_card_group_size_range": (3, 10),

    # 4. Abuse Rings — 7 real-world types
    "num_rings_per_type": {
        "raas":            10,  # Refunding-as-a-Service
        "slow_burn":       10,  # Sleeper / dormant fraud
        "device_farm":      8,  # Emulator / phone rack
        "triangulation":    8,  # Stolen card fulfillment
        "promo_abuse":      8,  # Coupon / new user promo abuse
        "classic_ring":    12,  # Traditional ring (high sharing, high refund)
        "stealth_ring":    10,  # Minimal signals, hardest to catch
    },

    # 5. Ring size ranges per type
    "ring_size_ranges": {
        "raas":            (5, 10),
        "slow_burn":       (4, 8),
        "device_farm":     (15, 30),
        "triangulation":   (3, 5),
        "promo_abuse":     (10, 30),
        "classic_ring":    (4, 12),
        "stealth_ring":    (3, 6),
    },

    # 6. Behavior
    "normal_refund_rate": 0.05,
    "family_refund_rate": 0.08,

    # 7. Noise settings (makes the data harder)
    "noisy_normal_pct": 0.10,           # 10% of normals have elevated refund (12-20%)
    "noisy_normal_refund_range": (0.12, 0.20),
    "random_ip_sharing_pct": 0.05,      # 5% of normals randomly share an IP

    # 8. Timing
    "data_period_days": 365,
    "ring_creation_window_hours": (1, 48),
}
