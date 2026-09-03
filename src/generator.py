"""Synthetic Financial Data Generator for LedgerSense.

Generates realistic 3-way financial ledgers:
1. Internal Orders (ERP / Platform database) - 100 records
2. Razorpay Settlements (Payment Gateway) - 95 records
3. Bank Statement (Bank account credits) - 90 records

Injected Edge Cases:
- 82 Standard Matches (1:1:1 match with 2% MDR + 18% GST)
- 5 Fee Tier Variations (1.5% custom fee instead of 2.0%)
- 3 Batch Settlements (2 orders combined into 1 UTR bank credit)
- 3 Chargeback / Refund deductions (disputed/refunded orders)
- 2 Missing Internal Orders (Phantom gateway payments)
- Pending / In-flight settlements (settled in gateway, not yet cleared in bank)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd


def generate_synthetic_data(output_dir: str = "data", seed: int = 42) -> dict[str, str]:
    """Generates deterministic synthetic financial datasets."""
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    base_date = datetime(2026, 8, 20, 10, 0, 0)

    internal_orders = []
    razorpay_settlements = []
    bank_statements = []

    running_balance = 2_500_000.00  # Initial account balance ₹25,00,000

    # -------------------------------------------------------------
    # 1. 82 Standard Matches (1:1:1 Join, 2% MDR + 18% GST)
    # -------------------------------------------------------------
    for i in range(1, 83):
        order_id = f"ORD_STD_{i:04d}"
        payment_id = f"pay_std_{i:04d}"
        utr = f"UTR9026STD{i:04d}"

        amount = round(random.uniform(500, 18000), 2)
        order_time = base_date + timedelta(hours=i * 2, minutes=random.randint(0, 50))
        settlement_time = order_time + timedelta(hours=random.randint(12, 24))
        bank_time = settlement_time + timedelta(hours=random.randint(4, 12))

        # Standard MDR formula: 2% fee + 18% GST on fee
        fee = round(amount * 0.02, 2)
        tax = round(fee * 0.18, 2)
        net_settled = round(amount - (fee + tax), 2)

        # Internal Order
        internal_orders.append({
            "order_id": order_id,
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "status": "SUCCESS"
        })

        # Razorpay Settlement
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": amount,
            "fee": fee,
            "tax": tax,
            "net_settled": net_settled,
            "utr": utr,
            "settlement_date": settlement_time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # Bank Credit
        running_balance = round(running_balance + net_settled, 2)
        bank_statements.append({
            "txn_date": bank_time.strftime("%Y-%m-%d"),
            "narration": f"CMS/RAZORPAY SETTLEMENT/{utr}/MDR2PCT",
            "utr": utr,
            "credit_amount": net_settled,
            "running_balance": running_balance
        })

    # -------------------------------------------------------------
    # 2. 5 Fee Tier Variations (1:1:1 Join, 1.5% Custom MDR + 18% GST)
    # -------------------------------------------------------------
    for i in range(1, 6):
        order_id = f"ORD_FEE_{i:03d}"
        payment_id = f"pay_fee_{i:03d}"
        utr = f"UTR9026FEE{i:03d}"

        amount = round(random.uniform(20000, 75000), 2)
        order_time = base_date + timedelta(days=7, hours=i * 3)
        settlement_time = order_time + timedelta(hours=14)
        bank_time = settlement_time + timedelta(hours=6)

        # Custom Enterprise Fee: 1.5% fee + 18% GST on fee
        fee = round(amount * 0.015, 2)
        tax = round(fee * 0.18, 2)
        net_settled = round(amount - (fee + tax), 2)

        internal_orders.append({
            "order_id": order_id,
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "status": "SUCCESS"
        })

        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": amount,
            "fee": fee,
            "tax": tax,
            "net_settled": net_settled,
            "utr": utr,
            "settlement_date": settlement_time.strftime("%Y-%m-%d %H:%M:%S")
        })

        running_balance = round(running_balance + net_settled, 2)
        bank_statements.append({
            "txn_date": bank_time.strftime("%Y-%m-%d"),
            "narration": f"CMS/RAZORPAY SETTLEMENT/{utr}/CUSTOM_TIER",
            "utr": utr,
            "credit_amount": net_settled,
            "running_balance": running_balance
        })

    # -------------------------------------------------------------
    # 3. 3 Batch Settlements (2 orders combined into 1 UTR bank credit)
    #    Total: 6 internal orders, 3 gateway settlement entries, 3 bank credits.
    # -------------------------------------------------------------
    for i in range(1, 4):
        utr = f"UTR9026BAT{i:03d}"
        order_id_1 = f"ORD_BAT_{i:02d}A"
        order_id_2 = f"ORD_BAT_{i:02d}B"
        payment_id = f"pay_bat_{i:03d}"

        amt_1 = round(random.uniform(4000, 12000), 2)
        amt_2 = round(random.uniform(3000, 9000), 2)
        combined_gross = round(amt_1 + amt_2, 2)

        fee = round(combined_gross * 0.02, 2)
        tax = round(fee * 0.18, 2)
        net_settled = round(combined_gross - (fee + tax), 2)

        order_time = base_date + timedelta(days=9, hours=i * 4)
        settlement_time = order_time + timedelta(hours=18)
        bank_time = settlement_time + timedelta(hours=8)

        # 2 Internal Orders per batch
        internal_orders.append({
            "order_id": order_id_1,
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amt_1,
            "status": "SUCCESS"
        })
        internal_orders.append({
            "order_id": order_id_2,
            "created_at": (order_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amt_2,
            "status": "SUCCESS"
        })

        # 1 Combined Gateway Settlement entry with dual order reference
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": f"{order_id_1}+{order_id_2}",
            "gross_amount": combined_gross,
            "fee": fee,
            "tax": tax,
            "net_settled": net_settled,
            "utr": utr,
            "settlement_date": settlement_time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # 1 Bank Statement Credit combining both orders
        running_balance = round(running_balance + net_settled, 2)
        bank_statements.append({
            "txn_date": bank_time.strftime("%Y-%m-%d"),
            "narration": f"CMS/RAZORPAY BATCH PAYOUT/{utr}/MULTI_ORDER",
            "utr": utr,
            "credit_amount": net_settled,
            "running_balance": running_balance
        })

    # Subtotals so far:
    # Internal: 82 + 5 + 6 = 93
    # Gateway: 82 + 5 + 3 = 90
    # Bank: 82 + 5 + 3 = 90 (Target 90 reached!)

    # -------------------------------------------------------------
    # 4. Pending / In-Flight Settlements (in Internal & Gateway, NOT in Bank)
    # -------------------------------------------------------------
    for i in range(1, 4):
        order_id = f"ORD_INF_{i:03d}"
        payment_id = f"pay_inf_{i:03d}"
        utr = f"UTR9026INF{i:03d}"

        amount = round(random.uniform(3000, 14000), 2)
        fee = round(amount * 0.02, 2)
        tax = round(fee * 0.18, 2)
        net_settled = round(amount - (fee + tax), 2)

        order_time = base_date + timedelta(days=13, hours=18 + i)
        settlement_time = order_time + timedelta(hours=2)

        # In internal orders
        internal_orders.append({
            "order_id": order_id,
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "status": "SUCCESS"
        })

        # In gateway settlements (settled in gateway, awaiting bank clearing T+1)
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": amount,
            "fee": fee,
            "tax": tax,
            "net_settled": net_settled,
            "utr": utr,
            "settlement_date": settlement_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Add 1 additional recent in-flight internal order awaiting gateway capture
    internal_orders.append({
        "order_id": "ORD_INF_004",
        "created_at": (base_date + timedelta(days=13, hours=23)).strftime("%Y-%m-%d %H:%M:%S"),
        "amount": 5400.00,
        "status": "SUCCESS"
    })

    # Subtotals:
    # Internal: 93 + 4 = 97
    # Gateway: 90 + 3 = 93
    # Bank: 90

    # -------------------------------------------------------------
    # 5. 2 Missing Internal Orders (Phantom Gateway Payments)
    #    (Recorded in Gateway, but missing in Internal ERP orders)
    # -------------------------------------------------------------
    for i in range(1, 3):
        payment_id = f"pay_phantom_{i:03d}"
        phantom_order_id = f"ORD_PHANTOM_{i:03d}"
        utr = f"UTR9026PHN{i:03d}"

        amount = round(random.uniform(4000, 8500), 2)
        fee = round(amount * 0.02, 2)
        tax = round(fee * 0.18, 2)
        net_settled = round(amount - (fee + tax), 2)
        settlement_time = base_date + timedelta(days=12, hours=i * 4)

        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": phantom_order_id,
            "gross_amount": amount,
            "fee": fee,
            "tax": tax,
            "net_settled": net_settled,
            "utr": utr,
            "settlement_date": settlement_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Gateway count: 93 + 2 = 95 (Target 95 reached!)

    # -------------------------------------------------------------
    # 6. 3 Chargeback / Refund Deductions (disputed orders in internal)
    # -------------------------------------------------------------
    for i in range(1, 4):
        order_id = f"ORD_CHG_{i:03d}"
        amount = round(random.uniform(1500, 6000), 2)
        order_time = base_date + timedelta(days=6, hours=i * 5)

        internal_orders.append({
            "order_id": order_id,
            "created_at": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "status": "DISPUTED"
        })

    # Internal count: 97 + 3 = 100 (Target 100 reached!)

    df_internal = pd.DataFrame(internal_orders)
    df_gateway = pd.DataFrame(razorpay_settlements)
    df_bank = pd.DataFrame(bank_statements)

    internal_path = os.path.join(output_dir, "internal_orders.csv")
    gateway_path = os.path.join(output_dir, "razorpay_settlements.csv")
    bank_path = os.path.join(output_dir, "bank_statement.csv")

    df_internal.to_csv(internal_path, index=False)
    df_gateway.to_csv(gateway_path, index=False)
    df_bank.to_csv(bank_path, index=False)

    return {
        "internal_orders_path": internal_path,
        "gateway_settlements_path": gateway_path,
        "bank_statement_path": bank_path,
        "internal_orders_count": len(df_internal),
        "gateway_settlements_count": len(df_gateway),
        "bank_statements_count": len(df_bank)
    }


if __name__ == "__main__":
    result = generate_synthetic_data()
    print("Generated Datasets:")
    print(f"Internal Orders: {result['internal_orders_count']} rows -> {result['internal_orders_path']}")
    print(f"Gateway Settlements: {result['gateway_settlements_count']} rows -> {result['gateway_settlements_path']}")
    print(f"Bank Statement Credits: {result['bank_statements_count']} rows -> {result['bank_statement_path']}")
