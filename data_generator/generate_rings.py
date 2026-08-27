"""
Generates ABUSE RINGS — the bad guys our system needs to catch.

5 different ring types to create variety:
  Type A: Device Ring    — many accounts share few devices
  Type B: Payment Ring   — many accounts share same card/UPI
  Type C: Refund Abuser  — buy-refund-repeat pattern
  Type D: Account Farm   — burst account creation, similar behavior
  Type E: Stealth Ring   — fewer signals, harder to catch (tests model limits)
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year, random_date_within_window

fake = Faker('en_IN')

# The 5 ring types and their characteristics
RING_TYPES = {
    "device_ring": {
        "description": "Many accounts sharing very few devices",
        "device_sharing": "high",     # 1-2 devices for entire ring
        "ip_sharing": "medium",       # 1-3 IPs
        "payment_sharing": "low",     # each member might have own card
        "refund_rate": (0.35, 0.65),
    },
    "payment_ring": {
        "description": "Many accounts sharing same payment instruments",
        "device_sharing": "medium",
        "ip_sharing": "medium",
        "payment_sharing": "high",    # 1-2 cards for entire ring
        "refund_rate": (0.40, 0.70),
    },
    "refund_abuser": {
        "description": "Buy-refund-repeat across multiple accounts",
        "device_sharing": "medium",
        "ip_sharing": "low",
        "payment_sharing": "medium",
        "refund_rate": (0.60, 0.90),  # Very high refund rate!
    },
    "account_farm": {
        "description": "Burst of accounts created in minutes",
        "device_sharing": "high",
        "ip_sharing": "high",         # All from same IP
        "payment_sharing": "medium",
        "refund_rate": (0.30, 0.55),
    },
    "stealth_ring": {
        "description": "Fewer signals — the hardest type to detect",
        "device_sharing": "low",      # More devices = looks more normal
        "ip_sharing": "low",
        "payment_sharing": "low",
        "refund_rate": (0.25, 0.45),  # Lower refund rate = harder to spot
    },
}


def _get_shared_count(sharing_level, ring_size):
    """
    Based on sharing level (high/medium/low), decide how many shared entities to create.
    High sharing = fewer entities shared among more people = more suspicious.
    """
    if sharing_level == "high":
        return random.randint(1, max(2, ring_size // 5))       # 1-2 for a ring of 10
    elif sharing_level == "medium":
        return random.randint(2, max(3, ring_size // 3))       # 2-3 for a ring of 10
    else:  # low
        return random.randint(max(3, ring_size // 2), ring_size)  # 5+ for a ring of 10


def generate_abuse_rings(config, start_index):
    """
    Create abuse ring members across all 5 ring types.
    
    Key characteristics that make rings different from families:
    1. Accounts created within HOURS (not months)
    2. Share MULTIPLE entity types (device + IP + card, not just IP)
    3. HIGH refund rates
    4. Higher transaction amounts
    5. Similar transaction timing patterns
    
    Args:
        config: our DATASET_CONFIG
        start_index: where to start numbering customer IDs
    
    Returns:
        customers: list of ring member customer dicts
        ring_metadata: dict with info about each ring (devices, IPs, cards, type)
    """
    customers = []
    ring_metadata = {}
    
    current_index = start_index
    ring_type_names = list(RING_TYPES.keys())

    for ring_id in range(config["num_rings"]):
        # Assign a ring type (cycle through all 5 types evenly)
        ring_type_name = ring_type_names[ring_id % len(ring_type_names)]
        ring_type = RING_TYPES[ring_type_name]

        # How many members in this ring?
        ring_size = random.randint(*config["ring_size_range"])

        # How many shared entities? (depends on ring type)
        num_shared_devices = _get_shared_count(ring_type["device_sharing"], ring_size)
        num_shared_ips = _get_shared_count(ring_type["ip_sharing"], ring_size)
        num_shared_payments = _get_shared_count(ring_type["payment_sharing"], ring_size)

        # Create the shared entity IDs
        shared_devices = [f"D_RING_{ring_id:04d}_{d}" for d in range(num_shared_devices)]
        shared_ips = [f"IP_RING_{ring_id:04d}_{ip}" for ip in range(num_shared_ips)]
        shared_payments = [f"PAY_RING_{ring_id:04d}_{p}" for p in range(num_shared_payments)]

        # All ring accounts are created in a SHORT time window (burst!)
        # Pick a random base date in the recent past (last 90 days)
        base_creation_date = random_date_past_year(days_back=90)
        min_hours, max_hours = config["ring_creation_window_hours"]

        # Pick the refund rate for this specific ring
        refund_rate = random.uniform(*ring_type["refund_rate"])

        # Store ring metadata (we'll use this later for analysis)
        ring_metadata[ring_id] = {
            "ring_type": ring_type_name,
            "ring_size": ring_size,
            "shared_devices": shared_devices,
            "shared_ips": shared_ips,
            "shared_payments": shared_payments,
            "refund_rate": refund_rate,
            "base_creation_date": base_creation_date,
        }

        # Generate each member of the ring
        for member in range(ring_size):
            customer_id = generate_id("C", current_index)
            name = fake.name()
            email_name = name.lower().replace(" ", ".").replace(".", "", 1)

            customer = {
                "customer_id": customer_id,
                "name": name,
                "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "phone": fake.phone_number(),
                # KEY: Created within hours of each other (not months!)
                "created_at": random_date_within_window(base_creation_date, min_hours, max_hours),
                "customer_type": "ring_member",
                "ring_id": f"RING_{ring_id:04d}",   # Which ring they belong to
                # Internal tracking for device/IP/payment assignment
                "_ring_type": ring_type_name,
                "_assigned_device": random.choice(shared_devices),
                "_assigned_ip": random.choice(shared_ips),
                "_assigned_payment": random.choice(shared_payments),
                "_refund_rate": refund_rate,
            }
            customers.append(customer)
            current_index += 1

    return customers, ring_metadata
