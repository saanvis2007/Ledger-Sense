"""Supabase Data Sync Utility for LedgerSense.

Uploads synthetic datasets and reconciliation records directly to Supabase.
Requires:
    pip install supabase

Usage:
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_KEY="your-service-role-key"
    python supabase/sync_data.py
"""

import os
import sys
import json
import pandas as pd

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None


def sync_to_supabase():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("[Supabase Sync] Note: SUPABASE_URL and SUPABASE_KEY environment variables are not set.")
        print("To push data to Supabase:")
        print("  1. Create a project at https://supabase.com")
        print("  2. Run the SQL in supabase/schema.sql in the SQL Editor")
        print("  3. Set environment variables:")
        print("     $env:SUPABASE_URL = 'https://xyz.supabase.co'")
        print("     $env:SUPABASE_KEY = 'your-api-key'")
        print("  4. Re-run: python supabase/sync_data.py")
        return False

    if not create_client:
        print("[Supabase Sync] Error: supabase package is not installed. Run: pip install supabase")
        return False

    client: Client = create_client(supabase_url, supabase_key)
    print(f"[Supabase Sync] Connected to {supabase_url}")

    # 1. Sync Internal Orders
    if os.path.exists("data/internal_orders.csv"):
        df = pd.read_csv("data/internal_orders.csv")
        records = df.to_dict(orient="records")
        client.table("internal_orders").upsert(records, on_conflict="order_id").execute()
        print(f"  Synced {len(records)} internal orders.")

    # 2. Sync Gateway Settlements
    if os.path.exists("data/razorpay_settlements.csv"):
        df = pd.read_csv("data/razorpay_settlements.csv")
        records = df.to_dict(orient="records")
        client.table("razorpay_settlements").upsert(records, on_conflict="payment_id").execute()
        print(f"  Synced {len(records)} gateway settlements.")

    # 3. Sync Bank Statements
    if os.path.exists("data/bank_statement.csv"):
        df = pd.read_csv("data/bank_statement.csv")
        records = df.to_dict(orient="records")
        client.table("bank_statements").insert(records).execute()
        print(f"  Synced {len(records)} bank statements.")

    # 4. Sync Reconciled Ledger
    if os.path.exists("data/reconciled_ledger.csv"):
        df = pd.read_csv("data/reconciled_ledger.csv")
        records = df.to_dict(orient="records")
        client.table("reconciliation_records").upsert(records, on_conflict="reconciliation_id").execute()
        print(f"  Synced {len(records)} reconciliation audit records.")

    print("[Supabase Sync] All datasets synchronized successfully.")
    return True


if __name__ == "__main__":
    sync_to_supabase()
