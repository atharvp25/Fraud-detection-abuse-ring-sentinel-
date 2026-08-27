"""
Configuration settings for the Synthetic Data Simulator.
Adjusting these values changes the size and difficulty of the dataset.
"""

DATASET_CONFIG = {
    # 1. Scale of the dataset
    "num_customers": 5000,
    "num_devices": 3500,
    "num_ips": 2500,
    "num_payment_instruments": 4000,

    # 2. Transaction settings
    "num_transactions_per_normal": (2, 12),  # min, max per normal customer
    "num_transactions_per_ring": (3, 8),     # min, max per ring member
    "normal_amount_range": (100, 4000),      # ₹
    "ring_amount_range": (1500, 9000),       # rings often make higher value transactions

    # 3. Legitimate Sharing (The "Good Guys" sharing stuff)
    "num_families": 150,
    "family_size_range": (2, 5),
    "num_offices": 50,
    "office_size_range": (5, 20),

    # 4. Abuse Rings (The "Bad Guys" we want to catch)
    "num_rings": 60,
    "ring_size_range": (4, 15),

    # 5. Behavior / Rules
    "normal_refund_rate": 0.05,              # 5% normal refund rate
    "family_refund_rate": 0.08,              # 8% family refund rate
    "ring_refund_rate": (0.40, 0.85),        # Rings refund 40% to 85% of transactions!
    
    # 6. Timing
    "data_period_days": 365,                 # Generate data over a 1 year period
    "ring_creation_window_hours": (1, 48),   # Ring accounts are created in quick bursts
}
