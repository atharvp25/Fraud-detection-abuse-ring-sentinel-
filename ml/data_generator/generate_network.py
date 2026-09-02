"""
Generates device, IP, and payment instrument mappings.
V2 — Handles student hostels (shared lab devices), corporate cards (shared payment),
and random IP sharing noise for normal customers.
"""
import random
from data_generator.utils import generate_id


def generate_device_mappings(all_customers, config):
    """Assign devices to customers based on their type."""
    devices = {}
    customer_device_map = []
    device_counter = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]

        if cust_type == "ring_member":
            device_id = customer["_assigned_device"]
            if device_id not in devices:
                devices[device_id] = {
                    "device_id": device_id,
                    "device_type": random.choice(["android", "ios", "windows", "mac"]),
                    "device_fingerprint": f"FP_{device_id}",
                }
            customer_device_map.append({"customer_id": cust_id, "device_id": device_id})

        elif cust_type in ("family", "student"):
            # Personal device
            personal_device = generate_id("D", device_counter)
            device_counter += 1
            devices[personal_device] = {
                "device_id": personal_device,
                "device_type": random.choice(["android", "ios"]),
                "device_fingerprint": f"FP_{personal_device}",
            }
            customer_device_map.append({"customer_id": cust_id, "device_id": personal_device})

            # Shared device (family tablet or hostel lab computer)
            if customer.get("_uses_shared_device", False):
                shared_dev = customer["_shared_device"]
                if shared_dev not in devices:
                    devices[shared_dev] = {
                        "device_id": shared_dev,
                        "device_type": random.choice(["android", "windows"]),
                        "device_fingerprint": f"FP_{shared_dev}",
                    }
                customer_device_map.append({"customer_id": cust_id, "device_id": shared_dev})

        else:
            # Normal, office, corporate: own device
            device_id = generate_id("D", device_counter)
            device_counter += 1
            devices[device_id] = {
                "device_id": device_id,
                "device_type": random.choice(["android", "ios", "windows", "mac"]),
                "device_fingerprint": f"FP_{device_id}",
            }
            customer_device_map.append({"customer_id": cust_id, "device_id": device_id})

    return list(devices.values()), customer_device_map


def generate_ip_mappings(all_customers, config):
    """Assign IP addresses to customers."""
    ip_addresses = {}
    customer_ip_map = []
    ip_counter = 0

    # Collect all normal customer IPs for random sharing later
    normal_ips = []

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]

        if cust_type == "ring_member":
            ip_id = customer["_assigned_ip"]
            if ip_id not in ip_addresses:
                ip_addresses[ip_id] = {
                    "ip_id": ip_id,
                    "ip_address": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                    "ip_type": "vpn",
                }
            customer_ip_map.append({"customer_id": cust_id, "ip_id": ip_id})

        elif cust_type in ("family", "office", "student"):
            shared_ip = customer.get("_shared_ip")
            if shared_ip:
                if shared_ip not in ip_addresses:
                    ip_type = {"family": "home", "office": "office", "student": "campus"}.get(cust_type, "home")
                    ip_addresses[shared_ip] = {
                        "ip_id": shared_ip,
                        "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
                        "ip_type": ip_type,
                    }
                customer_ip_map.append({"customer_id": cust_id, "ip_id": shared_ip})

        else:
            # Normal + corporate: unique IP
            ip_id = generate_id("IP", ip_counter)
            ip_counter += 1
            ip_addresses[ip_id] = {
                "ip_id": ip_id,
                "ip_address": f"103.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "ip_type": "home",
            }
            customer_ip_map.append({"customer_id": cust_id, "ip_id": ip_id})
            normal_ips.append(ip_id)

    # Add random IP sharing noise: 5% of normal customers share an IP with another random normal
    sharing_pct = config.get("random_ip_sharing_pct", 0.05)
    normal_customers = [c for c in all_customers if c["customer_type"] == "normal"]
    num_to_share = int(len(normal_customers) * sharing_pct)

    if normal_ips and num_to_share > 0:
        for _ in range(num_to_share):
            random_customer = random.choice(normal_customers)
            random_ip = random.choice(normal_ips)
            # Add a second IP mapping (public WiFi, coffee shop, etc.)
            customer_ip_map.append({
                "customer_id": random_customer["customer_id"],
                "ip_id": random_ip,
            })

    return list(ip_addresses.values()), customer_ip_map


def generate_payment_mappings(all_customers, config):
    """Assign payment instruments to customers."""
    payment_instruments = {}
    customer_payment_map = []
    pay_counter = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]

        if cust_type == "ring_member":
            pay_id = customer["_assigned_payment"]
            if pay_id not in payment_instruments:
                payment_instruments[pay_id] = {
                    "payment_id": pay_id,
                    "payment_type": random.choice(["credit_card", "debit_card", "upi"]),
                    "payment_fingerprint": f"PF_{pay_id}",
                }
            customer_payment_map.append({"customer_id": cust_id, "payment_id": pay_id})

        elif cust_type == "corporate":
            # Corporate employees share a company card
            shared_pay = customer.get("_shared_payment")
            if shared_pay:
                if shared_pay not in payment_instruments:
                    payment_instruments[shared_pay] = {
                        "payment_id": shared_pay,
                        "payment_type": "credit_card",
                        "payment_fingerprint": f"PF_{shared_pay}",
                    }
                customer_payment_map.append({"customer_id": cust_id, "payment_id": shared_pay})
            # They also have their own personal card for some purchases
            personal_pay = generate_id("PAY", pay_counter)
            pay_counter += 1
            payment_instruments[personal_pay] = {
                "payment_id": personal_pay,
                "payment_type": random.choice(["debit_card", "upi"]),
                "payment_fingerprint": f"PF_{personal_pay}",
            }
            customer_payment_map.append({"customer_id": cust_id, "payment_id": personal_pay})

        else:
            # Normal, family, office, student: own payment method
            pay_id = generate_id("PAY", pay_counter)
            pay_counter += 1
            payment_instruments[pay_id] = {
                "payment_id": pay_id,
                "payment_type": random.choice(["credit_card", "debit_card", "upi", "netbanking"]),
                "payment_fingerprint": f"PF_{pay_id}",
            }
            customer_payment_map.append({"customer_id": cust_id, "payment_id": pay_id})

    return list(payment_instruments.values()), customer_payment_map
