"""
Generates 7 types of ABUSE RINGS based on real-world fraud research.

Each type has DIFFERENT signals, so no single feature can catch all of them.
This forces the ML model to learn complex combinations.

Types:
  1. RaaS (Refunding-as-a-Service)  — high refunds, NO device sharing
  2. Slow-Burn                      — normal behavior then sudden abuse
  3. Device Farm                    — massive device sharing, VPN for IPs
  4. Triangulation                  — shared stolen cards, LOW refund rate
  5. Promo Abuse                    — new user promo exploit, VERY LOW refund
  6. Classic Ring                   — everything shared, everything suspicious
  7. Stealth Ring                   — minimal signals everywhere
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year, random_date_within_window

fake = Faker('en_IN')

# ══════════════════════════════════════════════════
# Ring type definitions — each has unique characteristics
# ══════════════════════════════════════════════════

RING_TYPES = {
    "raas": {
        "description": "Refunding-as-a-Service: organized refund fraud, different devices/IPs",
        "device_sharing": "none",       # each member uses own device
        "ip_sharing": "none",           # each member uses own IP
        "payment_sharing": "low",       # rarely share cards
        "refund_rate": (0.60, 0.90),    # VERY high refund rate
        "txn_timing": "spread",         # transactions spread over 2-6 weeks
        "txn_spread_days": (14, 42),    # how many days transactions span
        "account_age": "medium",        # accounts are 10-60 days old
        "account_age_days": (10, 60),
        "creation_pattern": "spread",   # accounts created over days, not hours
        "creation_spread_days": (3, 14),
    },
    "slow_burn": {
        "description": "Sleeper fraud: normal behavior for weeks, then sudden abuse",
        "device_sharing": "medium",
        "ip_sharing": "medium",
        "payment_sharing": "medium",
        "refund_rate": (0.30, 0.45),    # Medium overall (diluted by early normal txns)
        "txn_timing": "slow_burn",      # first 70% normal, last 30% abuse
        "txn_spread_days": (30, 90),
        "account_age": "old",           # 30-90 days old (looks established)
        "account_age_days": (30, 90),
        "creation_pattern": "spread",
        "creation_spread_days": (5, 30),
    },
    "device_farm": {
        "description": "Emulator/phone rack: many accounts, few devices, VPN rotation",
        "device_sharing": "very_high",  # 2-3 devices for 15-30 accounts
        "ip_sharing": "none",           # VPN rotation = different IPs
        "payment_sharing": "none",      # different stolen cards
        "refund_rate": (0.30, 0.50),
        "txn_timing": "spread",          # was burst, now spread to add difficulty
        "txn_spread_days": (2, 14),      # was (1, 5)
        "account_age": "new",
        "account_age_days": (1, 7),
        "creation_pattern": "burst",
        "creation_spread_days": (0, 1),
    },
    "triangulation": {
        "description": "Stolen card fulfillment: shared payment, normal behavior otherwise",
        "device_sharing": "none",
        "ip_sharing": "none",
        "payment_sharing": "very_high", # 1-2 stolen cards across all members
        "refund_rate": (0.05, 0.15),    # LOW refund! (chargebacks come later from bank)
        "txn_timing": "spread",
        "txn_spread_days": (7, 30),
        "account_age": "medium",
        "account_age_days": (7, 45),
        "creation_pattern": "spread",
        "creation_spread_days": (2, 10),
    },
    "promo_abuse": {
        "description": "New user promo exploit: many accounts to get signup bonuses",
        "device_sharing": "high",       # creating from same phone
        "ip_sharing": "medium",
        "payment_sharing": "none",      # different cards to look different
        "refund_rate": (0.03, 0.10),    # VERY LOW — they want the promo, not refunds
        "txn_timing": "spread",         # spread to add difficulty
        "txn_spread_days": (2, 7),      # was (1, 3)
        "account_age": "new",
        "account_age_days": (1, 5),
        "creation_pattern": "burst",
        "creation_spread_days": (0, 1),
        "amount_range": (50, 500),      # Small amounts (just enough for promo)
    },
    "classic_ring": {
        "description": "Traditional abuse ring: shares everything, high refund rate",
        "device_sharing": "high",
        "ip_sharing": "high",
        "payment_sharing": "high",
        "refund_rate": (0.50, 0.80),
        "txn_timing": "spread",         # spread to add difficulty
        "txn_spread_days": (2, 10),     # was (1, 5)
        "account_age": "new",
        "account_age_days": (1, 7),
        "creation_pattern": "burst",
        "creation_spread_days": (0, 1),
    },
    "stealth_ring": {
        "description": "Minimal signals: intentionally flies under the radar",
        "device_sharing": "low",
        "ip_sharing": "low",
        "payment_sharing": "low",
        "refund_rate": (0.20, 0.35),    # Only slightly elevated
        "txn_timing": "spread",
        "txn_spread_days": (14, 60),
        "account_age": "medium",
        "account_age_days": (14, 60),
        "creation_pattern": "spread",
        "creation_spread_days": (7, 30),
    },
}


def _get_shared_count(sharing_level, ring_size):
    """Decide how many shared entities based on sharing level."""
    if sharing_level == "very_high":
        return random.randint(1, max(2, ring_size // 8))
    elif sharing_level == "high":
        return random.randint(1, max(3, ring_size // 4))
    elif sharing_level == "medium":
        return random.randint(max(2, ring_size // 3), max(4, ring_size // 2))
    elif sharing_level == "low":
        return random.randint(max(3, ring_size // 2), ring_size)
    else:  # "none" — each member gets their own
        return ring_size  # one entity per member = no sharing


def generate_abuse_rings(config, start_index):
    """
    Create abuse ring members across all 7 ring types.
    Each type has fundamentally different signals.
    """
    customers = []
    ring_metadata = {}
    current_index = start_index
    ring_id_counter = 0

    for ring_type_name, num_rings in config["num_rings_per_type"].items():
        ring_type = RING_TYPES[ring_type_name]
        size_range = config["ring_size_ranges"][ring_type_name]

        for _ in range(num_rings):
            ring_size = random.randint(*size_range)

            # How many shared entities?
            num_shared_devices = _get_shared_count(ring_type["device_sharing"], ring_size)
            num_shared_ips = _get_shared_count(ring_type["ip_sharing"], ring_size)
            num_shared_payments = _get_shared_count(ring_type["payment_sharing"], ring_size)

            # Create shared entity IDs
            shared_devices = [f"D_RING_{ring_id_counter:04d}_{d}" for d in range(num_shared_devices)]
            shared_ips = [f"IP_RING_{ring_id_counter:04d}_{ip}" for ip in range(num_shared_ips)]
            shared_payments = [f"PAY_RING_{ring_id_counter:04d}_{p}" for p in range(num_shared_payments)]

            # Account creation timing
            if ring_type["creation_pattern"] == "burst":
                base_date = random_date_past_year(days_back=config["account_age_days"]
                    if "account_age_days" not in ring_type
                    else ring_type["account_age_days"][1] + 30)
                creation_window_days = ring_type["creation_spread_days"]
            else:
                base_date = random_date_past_year(days_back=ring_type["account_age_days"][1] + 60)
                creation_window_days = ring_type["creation_spread_days"]

            refund_rate = random.uniform(*ring_type["refund_rate"])

            # Store ring metadata
            ring_metadata[ring_id_counter] = {
                "ring_type": ring_type_name,
                "ring_size": ring_size,
                "shared_devices": shared_devices,
                "shared_ips": shared_ips,
                "shared_payments": shared_payments,
                "refund_rate": refund_rate,
                "base_creation_date": base_date,
                "num_shared_devices": num_shared_devices,
                "num_shared_ips": num_shared_ips,
                "num_shared_payments": num_shared_payments,
            }

            # Generate each member
            for member in range(ring_size):
                customer_id = generate_id("C", current_index)
                name = fake.name()
                email_name = name.lower().replace(" ", ".").replace(".", "", 1)

                # Creation date based on pattern
                if ring_type["creation_pattern"] == "burst":
                    min_h = creation_window_days[0] * 24
                    max_h = creation_window_days[1] * 24
                    created_at = random_date_within_window(base_date, min_h, max_h)
                else:
                    from datetime import timedelta
                    days_offset = random.randint(creation_window_days[0], creation_window_days[1])
                    created_at = base_date + timedelta(days=days_offset)

                # 25% of ring members are "clean mules" — they use PERSONAL
                # devices/IPs/payments instead of shared ring infrastructure.
                # They are part of the ring but invisible to device-sharing rules.
                is_clean_member = random.random() < 0.25

                if is_clean_member:
                    # Clean member: own device, own IP, own payment
                    assigned_device = f"D_CLEAN_{current_index}"
                    assigned_ip = f"IP_CLEAN_{current_index}"
                    assigned_payment = f"PAY_CLEAN_{current_index}"
                else:
                    assigned_device = random.choice(shared_devices)
                    assigned_ip = random.choice(shared_ips)
                    assigned_payment = random.choice(shared_payments)

                customer = {
                    "customer_id": customer_id,
                    "name": name,
                    "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                    "phone": fake.phone_number(),
                    "created_at": created_at,
                    "customer_type": "ring_member",
                    "ring_id": f"RING_{ring_id_counter:04d}",
                    "_ring_type": ring_type_name,
                    "_is_clean_member": is_clean_member,
                    "_assigned_device": assigned_device,
                    "_assigned_ip": assigned_ip,
                    "_assigned_payment": assigned_payment,
                    "_refund_rate": refund_rate,
                    "_txn_timing": ring_type["txn_timing"],
                    "_txn_spread_days": ring_type["txn_spread_days"],
                    "_amount_range": ring_type.get("amount_range", None),
                }
                customers.append(customer)
                current_index += 1

            ring_id_counter += 1

    return customers, ring_metadata
