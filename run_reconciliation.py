"""CLI Entry Point for LedgerSense Autonomous Reconciliation Agent.

Usage:
    python run_reconciliation.py [--seed 42] [--force-regen]
"""

import argparse
import sys
import os

from src.generator import generate_synthetic_data
from src.reconciler import ReconciliationEngine
from src.reporter import AuditReporter


def main():
    parser = argparse.ArgumentParser(description="LedgerSense Autonomous Reconciliation Agent")
    parser.add_argument("--data-dir", default="data", help="Directory containing CSV inputs and audit reports")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic data generation")
    parser.add_argument("--force-regen", action="store_true", help="Force regenerate synthetic data CSVs")
    args = parser.parse_args()

    internal_csv = os.path.join(args.data_dir, "internal_orders.csv")
    gateway_csv = os.path.join(args.data_dir, "razorpay_settlements.csv")
    bank_csv = os.path.join(args.data_dir, "bank_statement.csv")

    # Step 1: Ensure synthetic datasets exist
    data_exists = (
        os.path.exists(internal_csv)
        and os.path.exists(gateway_csv)
        and os.path.exists(bank_csv)
    )

    if args.force_regen or not data_exists:
        print(f"[LedgerSense] Generating synthetic datasets in '{args.data_dir}' (seed={args.seed})...")
        generate_synthetic_data(output_dir=args.data_dir, seed=args.seed)

    # Step 2: Initialize and run Two-Tier Reconciliation Engine
    print("[LedgerSense] Initializing Two-Tier Reconciliation Engine...")
    engine = ReconciliationEngine(
        internal_orders_path=internal_csv,
        gateway_settlements_path=gateway_csv,
        bank_statement_path=bank_csv,
    )

    summary = engine.reconcile()

    # Step 3: Export Audit Artifacts
    reporter = AuditReporter()
    paths = reporter.export_reports(summary, engine.reconciliation_records, output_dir=args.data_dir)

    # Step 4: Render Rich Terminal Dashboard
    reporter.print_rich_summary(summary, engine.reconciliation_records)

    print("\n[LedgerSense] Audit Artifacts Exported Successfully:")
    print(f"  • JSON Audit Report : {paths['json_report_path']}")
    print(f"  • Reconciled Ledger : {paths['csv_ledger_path']}")
    print("  • Streamlit Web UI  : streamlit run app.py\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
