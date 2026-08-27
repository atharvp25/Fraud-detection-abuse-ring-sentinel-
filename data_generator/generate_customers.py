"""
Generates normal individual customers.
These are the 70% of users who have their own devices, IPs, and cards.
They behave normally — low refund rates, spread-out account creation.
"""
import random
from faker import Faker
from data_generator.utils import generate_id, random_date_past_year

fake = Faker('en_IN')  # Indian locale for realistic Indian names


def generate_normal_customers(config):
    """
    Create normal, independent customers.
    
    Each customer gets:
    - A unique ID (C0001, C0002, ...)
    - A realistic Indian name and email
    - A phone number
    - A created_at date spread randomly over the past year
    
    Returns: list of customer dictionaries
    """
    customers = []
    num = config["num_customers"]

    for i in range(num):
        customer_id = generate_id("C", i)
        name = fake.name()

        # Create a simple email from the name (lowercase, no spaces)
        email_name = name.lower().replace(" ", ".").replace(".", "", 1)
        email = f"{email_name}{random.randint(1, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"

        customer = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "phone": fake.phone_number(),
            "created_at": random_date_past_year(days_back=config["data_period_days"]),
            "customer_type": "normal",  # This helps us track who is who
            "ring_id": None,            # Normal customers don't belong to any ring
        }
        customers.append(customer)

    return customers
