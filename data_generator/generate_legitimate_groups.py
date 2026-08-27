"""
Generates legitimate sharing groups — families and office workers.
These people share devices/IPs like abuse rings BUT they are innocent.
This is what makes our dataset HARD (not trivially solvable).
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year, random_date_within_window

fake = Faker('en_IN')


def generate_families(config, start_index):
    """
    Create family groups that SHARE devices and IPs (but are legitimate).
    
    Why families matter:
    - They share home WiFi (same IP)
    - They might share a tablet/laptop (same device)
    - BUT they have their own payment cards
    - AND their accounts were created months/years apart
    - AND they have normal refund rates
    
    If our model can't tell families from rings → our model is bad.
    
    Args:
        config: our DATASET_CONFIG
        start_index: where to start numbering customer IDs (after normal customers)
    
    Returns:
        customers: list of family member customer dicts
        shared_devices: dict mapping family_id → [device_ids they share]
        shared_ips: dict mapping family_id → ip_id they share
    """
    customers = []
    family_devices = {}  # family_id → list of shared device IDs
    family_ips = {}      # family_id → shared IP ID
    
    current_index = start_index

    for fam_id in range(config["num_families"]):
        # Each family gets a shared home WiFi IP
        shared_ip = f"IP_HOME_{fam_id:04d}"
        family_ips[fam_id] = shared_ip

        # Each family MIGHT share 1 device (like a family tablet)
        shared_device = f"D_FAM_{fam_id:04d}"
        family_devices[fam_id] = shared_device

        # Family size: 2 to 5 members
        family_size = random.randint(*config["family_size_range"])

        for member in range(family_size):
            customer_id = generate_id("C", current_index)
            name = fake.name()
            email_name = name.lower().replace(" ", ".").replace(".", "", 1)

            customer = {
                "customer_id": customer_id,
                "name": name,
                "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "phone": fake.phone_number(),
                # KEY DIFFERENCE: Family accounts are created MONTHS apart (not hours!)
                "created_at": random_date_past_year(days_back=config["data_period_days"]),
                "customer_type": "family",
                "ring_id": None,          # Families are NOT rings
                "_family_id": fam_id,     # Internal tracking (starts with _ = won't go to final data)
                "_shared_ip": shared_ip,
                "_shared_device": shared_device,
                "_uses_shared_device": member == 0 or random.random() < 0.3,  # 30% chance of using shared device
            }
            customers.append(customer)
            current_index += 1

    return customers, family_devices, family_ips


def generate_offices(config, start_index):
    """
    Create office worker groups that share ONLY an IP (office WiFi).
    
    Office workers:
    - Share the same office WiFi IP
    - Use their OWN phones/laptops (different devices)
    - Use their OWN payment methods
    - Have normal behavior
    
    This tests: can the model tell "same IP" apart from "same IP + same device + same card"?
    
    Returns:
        customers: list of office worker customer dicts
        office_ips: dict mapping office_id → shared IP
    """
    customers = []
    office_ips = {}
    
    current_index = start_index

    for office_id in range(config["num_offices"]):
        shared_ip = f"IP_OFFICE_{office_id:04d}"
        office_ips[office_id] = shared_ip

        office_size = random.randint(*config["office_size_range"])

        for worker in range(office_size):
            customer_id = generate_id("C", current_index)
            name = fake.name()
            email_name = name.lower().replace(" ", ".").replace(".", "", 1)

            customer = {
                "customer_id": customer_id,
                "name": name,
                "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "phone": fake.phone_number(),
                "created_at": random_date_past_year(days_back=config["data_period_days"]),
                "customer_type": "office",
                "ring_id": None,
                "_office_id": office_id,
                "_shared_ip": shared_ip,
            }
            customers.append(customer)
            current_index += 1

    return customers, office_ips
