"""
Generates transactions and refunds for all customers.

Normal customers: small amounts, spread over months, low refund rate (5%)
Family members:   small amounts, spread over months, low refund rate (8%)
Ring members:     higher amounts, burst timing, HIGH refund rate (40-85%)
"""
import random
from datetime import timedelta
from data_generator.utils import random_date_within_window


def generate_transactions(all_customers, config):
    """
    Create transactions for every customer.
    
    The transaction patterns differ based on customer type:
    - Normal/Family: spread over months, varied amounts, few refunds
    - Ring members: burst of transactions in short period, higher amounts, many refunds
    
    Returns:
        transactions: list of transaction dicts
        refunds: list of refund dicts (subset of transactions that were refunded)
    """
    transactions = []
    refunds = []
    txn_index = 0

    for customer in all_customers:
        cust_id = customer["customer_id"]
        cust_type = customer["customer_type"]
        created_at = customer["created_at"]

        # Decide how many transactions this customer makes
        if cust_type == "ring_member":
            num_txns = random.randint(*config["num_transactions_per_ring"])
            amount_range = config["ring_amount_range"]
            refund_rate = customer.get("_refund_rate", 0.5)
        else:
            num_txns = random.randint(*config["num_transactions_per_normal"])
            amount_range = config["normal_amount_range"]
            if cust_type == "family":
                refund_rate = config["family_refund_rate"]
            else:
                refund_rate = config["normal_refund_rate"]

        for t in range(num_txns):
            txn_id = f"TXN_{txn_index:06d}"

            # WHEN does the transaction happen?
            if cust_type == "ring_member":
                # Ring transactions happen in a BURST — within days of account creation
                txn_date = random_date_within_window(created_at, min_hours=0, max_hours=72)
            else:
                # Normal transactions spread over months after account creation
                days_after = random.randint(1, max(30, config["data_period_days"] - 30))
                txn_date = created_at + timedelta(days=days_after)

            # HOW MUCH is the transaction?
            amount = round(random.uniform(*amount_range), 2)

            # Is this transaction REFUNDED?
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

            # If refunded, create a refund record too
            if is_refunded:
                refund = {
                    "refund_id": f"REF_{txn_index:06d}",
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "refund_amount": amount,  # Full refund
                    "refund_reason": random.choice([
                        "item_not_received",
                        "defective_product",
                        "wrong_item",
                        "changed_mind",
                        "unauthorized_transaction",
                    ]),
                    "refund_timestamp": txn_date + timedelta(days=random.randint(1, 7)),
                }
                refunds.append(refund)

            txn_index += 1

    return transactions, refunds
