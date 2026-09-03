"""Comprehensive Unit & Regression Test Suite for LedgerSense.

Verifies:
1. Synthetic data integrity and exact counts (100 internal, 95 gateway, 90 bank).
2. Tier 1 deterministic matching accuracy.
3. Razorpay fee formula invariant (2% MDR + 18% GST).
4. Tier 2 custom fee tier (1.5% MDR) detection.
5. Batch settlements collapsing multiple orders to single UTR credits.
6. In-flight settlement classification.
7. Phantom payment detection.
8. Chargeback / dispute clawback tagging.
9. SLA proof: >90% match rate, 0.0% false positives.
10. Engine idempotency.
11. Audit report JSON export schema conformance.
"""

import os
import json
import pytest
import pandas as pd

from src.generator import generate_synthetic_data
from src.reconciler import ReconciliationEngine
from src.reporter import AuditReporter
from src.models import MatchStatus


@pytest.fixture(scope="session")
def setup_test_data(tmp_path_factory):
    """Generates synthetic test datasets in a temporary directory."""
    temp_dir = str(tmp_path_factory.mktemp("ledgersense_data"))
    result = generate_synthetic_data(output_dir=temp_dir, seed=42)
    return temp_dir, result


def test_synthetic_data_integrity(setup_test_data):
    """Verifies that the generated datasets match exact target counts and schemas."""
    temp_dir, meta = setup_test_data

    # File existence
    assert os.path.exists(meta["internal_orders_path"])
    assert os.path.exists(meta["gateway_settlements_path"])
    assert os.path.exists(meta["bank_statement_path"])

    # Exact Row Counts
    df_internal = pd.read_csv(meta["internal_orders_path"])
    df_gateway = pd.read_csv(meta["gateway_settlements_path"])
    df_bank = pd.read_csv(meta["bank_statement_path"])

    assert len(df_internal) == 100, f"Expected 100 internal orders, got {len(df_internal)}"
    assert len(df_gateway) == 95, f"Expected 95 gateway settlements, got {len(df_gateway)}"
    assert len(df_bank) == 90, f"Expected 90 bank statement credits, got {len(df_bank)}"

    # Column integrity
    assert list(df_internal.columns) == ["order_id", "created_at", "amount", "status"]
    assert list(df_gateway.columns) == [
        "payment_id", "order_id", "gross_amount", "fee", "tax", "net_settled", "utr", "settlement_date"
    ]
    assert list(df_bank.columns) == ["txn_date", "narration", "utr", "credit_amount", "running_balance"]


def test_deterministic_tier1_matching(setup_test_data):
    """Validates that Tier 1 deterministic engine matches standard transactions exactly."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    engine.load_and_normalize()
    m_int, m_gw, m_bk = engine.run_tier_1_deterministic()

    assert len(m_int) == 82, f"Expected 82 Tier 1 internal matches, got {len(m_int)}"
    assert len(m_gw) == 82, f"Expected 82 Tier 1 gateway matches, got {len(m_gw)}"
    assert len(m_bk) == 82, f"Expected 82 Tier 1 bank matches, got {len(m_bk)}"

    # Invariant checks for each Tier 1 match
    for rec in engine.reconciliation_records:
        assert rec.status == MatchStatus.RECONCILED_STANDARD
        assert rec.confidence_score == 1.0
        assert rec.variance == 0.0
        # Standard Razorpay fee: 2% + 18% GST
        expected_fee = round(rec.gross_amount * 0.02, 2)
        expected_tax = round(expected_fee * 0.18, 2)
        expected_net = round(rec.gross_amount - expected_fee - expected_tax, 2)
        assert abs(rec.fee - expected_fee) < 0.01
        assert abs(rec.tax - expected_tax) < 0.01
        assert abs(rec.net_settled - expected_net) < 0.01
        assert abs(rec.bank_credit_amount - expected_net) < 0.01


def test_fee_tier_variation_detection(setup_test_data):
    """Verifies that 5 custom fee tier transactions are identified and reconciled."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    custom_fee_records = [
        r for r in engine.reconciliation_records if r.status == MatchStatus.RECONCILED_CUSTOM_FEE
    ]
    assert len(custom_fee_records) == 5, f"Expected 5 custom fee tier matches, got {len(custom_fee_records)}"

    for rec in custom_fee_records:
        assert rec.reconciliation_tier == "TIER_2_AI_REASONING"
        assert rec.confidence_score >= 0.98
        assert rec.variance == 0.0
        # Check custom fee ~1.5%
        eff_rate = rec.fee / rec.gross_amount
        assert abs(eff_rate - 0.015) < 0.002
        assert rec.metadata.get("tier_name") == "Enterprise 1.5% Custom MDR"


def test_batch_settlement_resolution(setup_test_data):
    """Verifies that multiple internal orders correctly collapse to single UTR credits."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    batch_records = [
        r for r in engine.reconciliation_records if r.status == MatchStatus.RECONCILED_BATCH
    ]
    assert len(batch_records) == 3, f"Expected 3 batch settlement matches, got {len(batch_records)}"

    for rec in batch_records:
        assert rec.reconciliation_tier == "TIER_2_AI_REASONING"
        assert rec.metadata.get("batch_order_count") == 2
        assert rec.variance == 0.0
        # Bank credit matches net settled
        assert abs(rec.bank_credit_amount - rec.net_settled) < 0.01
        assert "batch settlement" in rec.reasoning.lower()


def test_in_flight_settlement_detection(setup_test_data):
    """Verifies that in-flight gateway settlements are tagged with T+1 explanation."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    inflight_records = [
        r for r in engine.reconciliation_records if r.status == MatchStatus.IN_FLIGHT_SETTLEMENT
    ]
    assert len(inflight_records) >= 3
    for rec in inflight_records:
        r_lower = rec.reasoning.lower()
        assert "t+1" in r_lower or "pending" in r_lower or "clearing" in r_lower
        assert rec.action_required is not None


def test_phantom_gateway_payment_detection(setup_test_data):
    """Verifies that missing internal orders (phantom gateway payments) are flagged."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    phantom_records = [
        r for r in engine.reconciliation_records if r.status == MatchStatus.UNREGISTERED_ORDER
    ]
    assert len(phantom_records) == 2, f"Expected 2 phantom payments, got {len(phantom_records)}"
    for rec in phantom_records:
        r_lower = rec.reasoning.lower()
        assert "unregistered" in r_lower or "phantom" in r_lower
        assert rec.order_amount == 0.0


def test_chargeback_deduction_tagging(setup_test_data):
    """Verifies that disputed orders are tagged as CHARGEBACK_DEDUCTION."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    chargeback_records = [
        r for r in engine.reconciliation_records if r.status == MatchStatus.CHARGEBACK_DEDUCTION
    ]
    assert len(chargeback_records) == 3, f"Expected 3 chargeback deductions, got {len(chargeback_records)}"
    for rec in chargeback_records:
        r_lower = rec.reasoning.lower()
        assert "dispute" in r_lower or "chargeback" in r_lower
        assert "Proof of Delivery" in rec.action_required


def test_reconciliation_match_rate_and_accuracy(setup_test_data):
    """Asserts that automated match rate exceeds 90% and false-positive rate is zero."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()

    # Core target metrics
    assert summary.automated_match_rate_pct > 90.0, (
        f"Match rate {summary.automated_match_rate_pct}% did not exceed 90.0% threshold"
    )
    assert summary.false_positive_rate_pct == 0.0, "Expected zero false positives"
    assert summary.reconciled_records_count == 90
    assert summary.exceptions_count == 9


def test_idempotency(setup_test_data):
    """Verifies that running reconciliation multiple times produces identical results."""
    temp_dir, meta = setup_test_data
    engine1 = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary1 = engine1.reconcile()

    engine2 = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary2 = engine2.reconcile()

    assert summary1.automated_match_rate_pct == summary2.automated_match_rate_pct
    assert summary1.reconciled_records_count == summary2.reconciled_records_count
    assert summary1.exceptions_count == summary2.exceptions_count
    assert summary1.status_breakdown == summary2.status_breakdown
    assert summary1.tier_breakdown == summary2.tier_breakdown
    assert len(engine1.reconciliation_records) == len(engine2.reconciliation_records)


def test_audit_report_export(setup_test_data):
    """Verifies JSON audit report structure and CSV ledger export."""
    temp_dir, meta = setup_test_data
    engine = ReconciliationEngine(
        internal_orders_path=meta["internal_orders_path"],
        gateway_settlements_path=meta["gateway_settlements_path"],
        bank_statement_path=meta["bank_statement_path"],
    )
    summary = engine.reconcile()
    reporter = AuditReporter()
    paths = reporter.export_reports(summary, engine.reconciliation_records, output_dir=temp_dir)

    assert os.path.exists(paths["json_report_path"])
    assert os.path.exists(paths["csv_ledger_path"])

    with open(paths["json_report_path"], "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "summary" in data
    assert "exceptions" in data
    assert "reconciled_records" in data

    assert data["summary"]["match_rate_percentage"] > 90.0
    assert len(data["exceptions"]) == 9
    assert len(data["reconciled_records"]) == 90

    df_csv = pd.read_csv(paths["csv_ledger_path"])
    assert len(df_csv) == 99
    assert "root_cause_reasoning" in df_csv.columns
    assert "action_required" in df_csv.columns
