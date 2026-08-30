"""
Generates transactions and refunds for all customers.
V2 — Different transaction patterns per ring type + noise for normal customers.

Ring types have DIFFERENT timing:
  - RaaS:          spread over 2-6 weeks (looks normal!)
  - Slow-Burn:     first 70% normal, last 30% abuse burst
  - Device Farm:   1-5 day burst
  - Triangulation: spread over 1-4 weeks
  - Promo Abuse:   1-3 day burst, small amounts
  - Classic Ring:  1-5 day burst
  - Stealth Ring:  spread over 2-8 weeks

Normal customers also have NOISE:
  - 10% have slightly elevated refund rates (12-20%)
  - New users may have short transaction spans (like ring burst)
"""
import random
from datetime import timedelta
from data_generator.utils import random_date_within_window


def generate_transactions(all_customers, config):
    """Create transactions for every customer with realistic patterns."""
    transactions = []
    refunds = []
    txn_index = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]
        created_at = customer["created_at"]

        if cust_type == "ring_member":
            # ── RING MEMBER TRANSACTIONS ──
            num_txns = random.randint(*config["num_transactions_per_ring"])
            ring_type = customer.get("_ring_type", "classic_ring")
            txn_timing = customer.get("_txn_timing", "burst")
            txn_spread = customer.get("_txn_spread_days", (1, 5))
            refund_rate = customer.get("_refund_rate", 0.5)
            amount_range = customer.get("_amount_range") or config["ring_amount_range"]

            # Slow-burn: extra normal transactions before the abuse phase
            if txn_timing == "slow_burn":
                num_normal_txns = int(num_txns * 0.7)
                num_abuse_txns = num_txns - num_normal_txns

                # Phase 1: Normal behavior (spread over weeks, low refund, normal amounts)
                for t in range(num_normal_txns):
                    txn_id = f"TXN_{txn_index:06d}"
                    days_after = random.randint(1, txn_spread[1])
                    txn_date = created_at + timedelta(days=days_after)
                    amount = round(random.uniform(*config["normal_amount_range"]), 2)
                    is_refunded = random.random() < 0.06  # Normal refund rate in phase 1

                    transaction = {
                        "transaction_id": txn_id,
                        "customer_id": cust_id,
                        "amount": amount,
                        "timestamp": txn_date,
                        "status": "refunded" if is_refunded else "success",
                        "merchant_id": f"MERCH_{random.randint(1, 50):04d}",
                    }
                    transactions.append(transaction)
                    if is_refunded:
                        refunds.append(_create_refund(txn_id, cust_id, amount, txn_date))
                    txn_index += 1

                # Phase 2: Abuse burst (concentrated, high refund, high amounts)
                abuse_start = created_at + timedelta(days=txn_spread[1] - 5)
                for t in range(num_abuse_txns):
                    txn_id = f"TXN_{txn_index:06d}"
                    txn_date = random_date_within_window(abuse_start, 0, 72)
                    amount = round(random.uniform(*amount_range), 2)
                    is_refunded = random.random() < min(refund_rate * 1.8, 0.95)

                    transaction = {
                        "transaction_id": txn_id,
                        "customer_id": cust_id,
                        "amount": amount,
                        "timestamp": txn_date,
                        "status": "refunded" if is_refunded else "success",
                        "merchant_id": f"MERCH_{random.randint(1, 50):04d}",
                    }
                    transactions.append(transaction)
                    if is_refunded:
                        refunds.append(_create_refund(txn_id, cust_id, amount, txn_date))
                    txn_index += 1

            else:
                # All other ring types: timing based on txn_timing setting
                for t in range(num_txns):
                    txn_id = f"TXN_{txn_index:06d}"

                    if txn_timing == "burst":
                        max_hours = txn_spread[1] * 24
                        txn_date = random_date_within_window(created_at, 0, max_hours)
                    else:  # "spread"
                        days_after = random.randint(txn_spread[0], txn_spread[1])
                        txn_date = created_at + timedelta(days=days_after)

                    amount = round(random.uniform(*amount_range), 2)
                    is_refunded = random.random() < refund_rate

                    transaction = {
                        "transaction_id": txn_id,
                        "customer_id": cust_id,
                        "amount": amount,
                        "timestamp": txn_date,
                        "status": "refunded" if is_refunded else "success",
                        "merchant_id": f"MERCH_{random.randint(1, 50):04d}",
                    }
                    transactions.append(transaction)
                    if is_refunded:
                        refunds.append(_create_refund(txn_id, cust_id, amount, txn_date))
                    txn_index += 1

        else:
            # ── NORMAL / FAMILY / OFFICE TRANSACTIONS ──
            num_txns = random.randint(*config["num_transactions_per_normal"])
            amount_range = config["normal_amount_range"]

            # Determine refund rate (with noise for some normals)
            if cust_type == "family":
                refund_rate = config["family_refund_rate"]
            elif customer.get("_noisy", False):
                # Noisy normal: slightly elevated refund rate
                refund_rate = random.uniform(*config["noisy_normal_refund_range"])
            else:
                refund_rate = config["normal_refund_rate"]

            # Some new normal customers also have short transaction spans
            is_new_user = customer.get("_is_new_user", False)

            for t in range(num_txns):
                txn_id = f"TXN_{txn_index:06d}"

                if is_new_user:
                    # New user burst: transactions within first 5 days
                    txn_date = random_date_within_window(created_at, 0, 120)
                else:
                    # Normal: spread over months
                    days_after = random.randint(1, max(30, config["data_period_days"] - 30))
                    txn_date = created_at + timedelta(days=days_after)

                amount = round(random.uniform(*amount_range), 2)

                # Power shoppers: occasional higher amounts
                if customer.get("_power_shopper", False) and random.random() < 0.3:
                    amount = round(random.uniform(3000, 10000), 2)

                is_refunded = random.random() < refund_rate

                transaction = {
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "amount": amount,
                    "timestamp": txn_date,
                    "status": "refunded" if is_refunded else "success",
                    "merchant_id": f"MERCH_{random.randint(1, 50):04d}",
                }
                transactions.append(transaction)
                if is_refunded:
                    refunds.append(_create_refund(txn_id, cust_id, amount, txn_date))
                txn_index += 1

    return transactions, refunds


def _create_refund(txn_id, cust_id, amount, txn_date):
    """Helper to create a refund record."""
    return {
        "refund_id": f"REF_{txn_id.split('_')[1]}",
        "transaction_id": txn_id,
        "customer_id": cust_id,
        "refund_amount": amount,
        "refund_reason": random.choice([
            "item_not_received",
            "defective_product",
            "wrong_item",
            "changed_mind",
            "unauthorized_transaction",
        ]),
        "refund_timestamp": txn_date + timedelta(days=random.randint(1, 7)),
    }
