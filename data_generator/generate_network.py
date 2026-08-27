"""
Generates device, IP, and payment instrument mappings.

This is the CORE of our graph — it creates the connections:
  Customer → uses → Device
  Customer → connects from → IP
  Customer → pays with → Payment Instrument

Normal customers: own devices, own IPs, own cards
Family members:   shared IP (home WiFi), maybe shared device, own cards
Ring members:     shared devices + IPs + cards (multiple overlaps!)
"""
import random
from data_generator.utils import generate_id


def generate_device_mappings(all_customers, config):
    """
    Assign devices to customers.
    
    - Normal customers: each gets their own unique device
    - Family members: share a family device (30% chance) + have personal device
    - Ring members: use devices from their ring's shared pool
    
    Returns:
        devices: list of device dicts (device_id, device_type)
        customer_device_map: list of {customer_id, device_id} mappings
    """
    devices = {}        # device_id → device info
    customer_device_map = []
    device_counter = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]

        if cust_type == "ring_member":
            # Ring members use their assigned shared device
            device_id = customer["_assigned_device"]
            if device_id not in devices:
                devices[device_id] = {
                    "device_id": device_id,
                    "device_type": random.choice(["android", "ios", "windows", "mac"]),
                    "device_fingerprint": f"FP_{device_id}",
                }
            customer_device_map.append({
                "customer_id": cust_id,
                "device_id": device_id,
            })

        elif cust_type == "family":
            # Family members: always have a personal device
            personal_device = generate_id("D", device_counter)
            device_counter += 1
            devices[personal_device] = {
                "device_id": personal_device,
                "device_type": random.choice(["android", "ios"]),
                "device_fingerprint": f"FP_{personal_device}",
            }
            customer_device_map.append({
                "customer_id": cust_id,
                "device_id": personal_device,
            })

            # ALSO use family shared device sometimes (30%)
            if customer.get("_uses_shared_device", False):
                shared_dev = customer["_shared_device"]
                if shared_dev not in devices:
                    devices[shared_dev] = {
                        "device_id": shared_dev,
                        "device_type": random.choice(["android", "windows"]),
                        "device_fingerprint": f"FP_{shared_dev}",
                    }
                customer_device_map.append({
                    "customer_id": cust_id,
                    "device_id": shared_dev,
                })

        else:
            # Normal customer: gets their own device
            device_id = generate_id("D", device_counter)
            device_counter += 1
            devices[device_id] = {
                "device_id": device_id,
                "device_type": random.choice(["android", "ios", "windows", "mac"]),
                "device_fingerprint": f"FP_{device_id}",
            }
            customer_device_map.append({
                "customer_id": cust_id,
                "device_id": device_id,
            })

    return list(devices.values()), customer_device_map


def generate_ip_mappings(all_customers, config):
    """
    Assign IP addresses to customers.
    
    - Normal customers: each gets a unique home IP
    - Family members: share home WiFi IP
    - Office workers: share office WiFi IP
    - Ring members: use IPs from their ring's shared pool
    
    Returns:
        ip_addresses: list of IP dicts
        customer_ip_map: list of {customer_id, ip_id} mappings
    """
    ip_addresses = {}
    customer_ip_map = []
    ip_counter = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]

        if cust_type == "ring_member":
            ip_id = customer["_assigned_ip"]
            if ip_id not in ip_addresses:
                ip_addresses[ip_id] = {
                    "ip_id": ip_id,
                    "ip_address": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                    "ip_type": "vpn",   # Rings often use VPNs
                }
            customer_ip_map.append({"customer_id": cust_id, "ip_id": ip_id})

        elif cust_type in ("family", "office"):
            # Use the shared IP from their group
            shared_ip = customer.get("_shared_ip")
            if shared_ip:
                if shared_ip not in ip_addresses:
                    ip_type = "home" if cust_type == "family" else "office"
                    ip_addresses[shared_ip] = {
                        "ip_id": shared_ip,
                        "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
                        "ip_type": ip_type,
                    }
                customer_ip_map.append({"customer_id": cust_id, "ip_id": shared_ip})

        else:
            # Normal customer: unique IP
            ip_id = generate_id("IP", ip_counter)
            ip_counter += 1
            ip_addresses[ip_id] = {
                "ip_id": ip_id,
                "ip_address": f"103.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "ip_type": "home",
            }
            customer_ip_map.append({"customer_id": cust_id, "ip_id": ip_id})

    return list(ip_addresses.values()), customer_ip_map


def generate_payment_mappings(all_customers, config):
    """
    Assign payment instruments (cards, UPI) to customers.
    
    - Normal & family customers: each gets their OWN card (this is key!)
    - Ring members: share payment instruments from their ring's pool
    
    This is a CRITICAL difference:
    Family shares IP + device → normal
    Ring shares IP + device + CARD → suspicious!
    
    Returns:
        payment_instruments: list of payment dicts
        customer_payment_map: list of {customer_id, payment_id} mappings
    """
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

        else:
            # Normal + Family + Office: each person has their OWN payment method
            pay_id = generate_id("PAY", pay_counter)
            pay_counter += 1
            payment_instruments[pay_id] = {
                "payment_id": pay_id,
                "payment_type": random.choice(["credit_card", "debit_card", "upi", "netbanking"]),
                "payment_fingerprint": f"PF_{pay_id}",
            }
            customer_payment_map.append({"customer_id": cust_id, "payment_id": pay_id})

    return list(payment_instruments.values()), customer_payment_map
