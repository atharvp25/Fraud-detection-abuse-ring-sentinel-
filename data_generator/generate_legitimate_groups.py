"""
Generates legitimate sharing groups — families, offices, hostels, and corporate card users.
V2 — Added student hostels (shared IP + device) and corporate card groups (shared payment).
These are the HARDEST edge cases — they look like fraud but are innocent.
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year, random_date_within_window

fake = Faker('en_IN')


def generate_families(config, start_index):
    """
    Family groups: share home WiFi (IP) + maybe a tablet (device), own cards.
    Normal behavior, accounts created months apart.
    """
    customers = []
    family_devices = {}
    family_ips = {}
    current_index = start_index

    for fam_id in range(config["num_families"]):
        shared_ip = f"IP_HOME_{fam_id:04d}"
        shared_device = f"D_FAM_{fam_id:04d}"
        family_ips[fam_id] = shared_ip
        family_devices[fam_id] = shared_device

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
                "created_at": random_date_past_year(days_back=config["data_period_days"]),
                "customer_type": "family",
                "ring_id": None,
                "_family_id": fam_id,
                "_shared_ip": shared_ip,
                "_shared_device": shared_device,
                "_uses_shared_device": member == 0 or random.random() < 0.3,
            }
            customers.append(customer)
            current_index += 1

    return customers, family_devices, family_ips


def generate_offices(config, start_index):
    """
    Office workers: share ONLY office WiFi (IP). Own devices, own cards.
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


def generate_student_hostels(config, start_index):
    """
    Student hostel: share WiFi (IP) AND computer lab devices.
    Looks VERY suspicious (shared IP + shared device), but is legitimate.
    This is the hardest false-positive case.
    """
    customers = []
    hostel_ips = {}
    hostel_devices = {}
    current_index = start_index

    for hostel_id in range(config["num_student_hostels"]):
        shared_ip = f"IP_HOSTEL_{hostel_id:04d}"
        # Computer lab has only 2-3 shared devices (creates HIGH sharing = overlaps with device_farm)
        lab_devices = [f"D_LAB_{hostel_id:04d}_{d}" for d in range(random.randint(2, 3))]

        hostel_ips[hostel_id] = shared_ip
        hostel_devices[hostel_id] = lab_devices

        hostel_size = random.randint(*config["hostel_size_range"])
        for student in range(hostel_size):
            customer_id = generate_id("C", current_index)
            name = fake.name()
            email_name = name.lower().replace(" ", ".").replace(".", "", 1)

            customer = {
                "customer_id": customer_id,
                "name": name,
                "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "phone": fake.phone_number(),
                "created_at": random_date_past_year(days_back=config["data_period_days"]),
                "customer_type": "student",
                "ring_id": None,
                "_hostel_id": hostel_id,
                "_shared_ip": shared_ip,
                "_shared_device": random.choice(lab_devices),  # uses one of the lab computers
                "_uses_shared_device": random.random() < 0.80,  # 80% use lab (creates overlap with device_farm)
            }
            customers.append(customer)
            current_index += 1

    return customers, hostel_devices, hostel_ips


def generate_corporate_card_groups(config, start_index):
    """
    Corporate card users: multiple employees share a company credit card.
    Looks suspicious (shared payment instrument!), but is legitimate.
    Different devices, different IPs, normal refund rate.
    """
    customers = []
    corp_payments = {}
    current_index = start_index

    for corp_id in range(config["num_corporate_card_groups"]):
        shared_payment = f"PAY_CORP_{corp_id:04d}"
        corp_payments[corp_id] = shared_payment

        group_size = random.randint(*config["corporate_card_group_size_range"])
        for emp in range(group_size):
            customer_id = generate_id("C", current_index)
            name = fake.name()
            email_name = name.lower().replace(" ", ".").replace(".", "", 1)

            customer = {
                "customer_id": customer_id,
                "name": name,
                "email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "phone": fake.phone_number(),
                "created_at": random_date_past_year(days_back=config["data_period_days"]),
                "customer_type": "corporate",
                "ring_id": None,
                "_corp_id": corp_id,
                "_shared_payment": shared_payment,
            }
            customers.append(customer)
            current_index += 1

    return customers, corp_payments
