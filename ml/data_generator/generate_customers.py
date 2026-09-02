"""
Generates normal individual customers.
V2 — Added noise variations: new user bursts, power shoppers, elevated refund normals.
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year

fake = Faker('en_IN')


def generate_normal_customers(config):
    """
    Create normal customers with realistic noise variations.
    
    Noise types (make the dataset harder):
    - 10% have slightly elevated refund rates (12-20%) — just unlucky shoppers
    - 5% are "new users" who buy in bursts (short txn span like ring members)
    - 3% are "power shoppers" with high transaction counts and occasional big purchases
    """
    customers = []
    num = config["num_customers"]
    noisy_pct = config.get("noisy_normal_pct", 0.10)

    for i in range(num):
        customer_id = generate_id("C", i)
        name = fake.name()
        email_name = name.lower().replace(" ", ".").replace(".", "", 1)
        email = f"{email_name}{random.randint(1, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"

        # Decide noise type
        roll = random.random()
        is_noisy = roll < noisy_pct           # 10% elevated refund
        is_new_user = 0.10 < roll < 0.30      # 20% new user burst (was 5%)
        is_power_shopper = 0.30 < roll < 0.33  # 3% power shopper

        # New users have recent account creation
        if is_new_user:
            created_at = random_date_past_year(days_back=14)  # Created within last 2 weeks
        else:
            created_at = random_date_past_year(days_back=config["data_period_days"])

        customer = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "phone": fake.phone_number(),
            "created_at": created_at,
            "customer_type": "normal",
            "ring_id": None,
            "_noisy": is_noisy,
            "_is_new_user": is_new_user,
            "_power_shopper": is_power_shopper,
        }
        customers.append(customer)

    return customers
