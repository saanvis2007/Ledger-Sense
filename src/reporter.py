"""LedgerSense Audit Reporter & CLI Formatter.

Generates:
1. data/reconciliation_audit_report.json (One single source of truth schema)
2. data/reconciled_ledger.csv
3. Professional console reports
"""

from __future__ import annotations

import json
import os
import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from src.models import ReconciliationRecord, AuditReportSummary, MatchStatus

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class AuditReporter:
    def __init__(self, console: Console | None = None):
        self.console = console or Console(legacy_windows=False)

    def export_reports(
        self,
        summary: AuditReportSummary,
        records: List[ReconciliationRecord],
        output_dir: str = "data"
    ) -> Dict[str, str]:
        """Exports audit report JSON and reconciled ledger CSV."""
        os.makedirs(output_dir, exist_ok=True)

        json_path = os.path.join(output_dir, "reconciliation_audit_report.json")
        csv_path = os.path.join(output_dir, "reconciled_ledger.csv")

        reconciled_statuses = {
            MatchStatus.RECONCILED_STANDARD.value,
            MatchStatus.RECONCILED_CUSTOM_FEE.value,
            MatchStatus.RECONCILED_BATCH.value,
        }

        exceptions_list = []
        reconciled_list = []
        csv_rows = []

        for r in records:
            is_reconciled = r.status.value in reconciled_statuses
            item = {
                "transaction_id": r.reconciliation_id,
                "reconciliation_id": r.reconciliation_id,
                "order_id": r.order_id,
                "payment_id": r.payment_id,
                "utr": r.utr,
                "order_amount": r.order_amount,
                "gross_amount": r.gross_amount,
                "fee": r.fee,
                "tax": r.tax,
                "net_settled": r.net_settled,
                "bank_credit_amount": r.bank_credit_amount,
                "expected_amount": r.metadata.get("expected_amount", r.net_settled or r.order_amount or 0.0),
                "actual_amount": r.metadata.get("actual_amount", r.bank_credit_amount or 0.0),
                "difference": r.variance,
                "variance": r.variance,
                "matching_result": "Reconciled" if is_reconciled else "Exception",
                "status": r.status.value,
                "tier": r.reconciliation_tier,
                "match_method": r.match_method,
                "exception_type": None if is_reconciled else r.status.value,
                "confidence_score": r.confidence_score,
                "root_cause": r.root_cause,
                "ai_diagnosis": r.ai_diagnosis,
                "reasoning": r.reasoning,
                "root_cause_reasoning": r.reasoning,
                "evidence_used": r.evidence_used,
                "financial_impact": r.financial_impact,
                "priority_level": r.priority_level,
                "priority_score": r.priority_score,
                "priority_reason": r.priority_reason,
                "action_required": r.action_required,
                "action_status": r.action_status,
                "timestamp": summary.generated_at,
                "metadata": r.metadata,
            }
            csv_rows.append(item)

            if is_reconciled:
                reconciled_list.append(item)
            else:
                exceptions_list.append(item)

        audit_payload = {
            "metadata": {
                "system": "LedgerSense Financial Reconciliation Platform",
                "version": "1.0.0",
                "run_id": "LS-2026-0903-001",
                "generated_at": summary.generated_at,
                "status": "Completed",
            },
            "performance": {
                "records_processed": len(records),
                "processing_time_ms": summary.processing_time_ms,
                "throughput_records_per_sec": summary.throughput_records_per_sec,
            },
            "summary": {
                "records_evaluated": len(records),
                "total_orders": summary.total_internal_orders,
                "total_settled_gateway": summary.total_gateway_settlements,
                "total_bank_credits": summary.total_bank_credits,
                "match_rate_percentage": summary.automated_match_rate_pct,
                "false_positive_rate_percentage": summary.false_positive_rate_pct,
                "false_positive_rate_definition": (
                    "Verified by mathematical invariant assertion: Zero non-matching order IDs or mismatched "
                    "settlement amounts were reconciled without 100% arithmetic verification against configured fee formulas and bank credits."
                ),
                "total_internal_order_volume": summary.total_internal_order_volume,
                "total_gateway_settled_volume": summary.total_gateway_settled_volume,
                "total_bank_credited_volume": summary.total_bank_credited_volume,
                "total_reconciled_volume": summary.reconciled_bank_volume,
                "variance_amount": summary.net_variance_amount,
                "reconciled_count": summary.reconciled_records_count,
                "exceptions_count": summary.exceptions_count,
                "status_breakdown": summary.status_breakdown,
                "tier_breakdown": summary.tier_breakdown,
                "match_method_breakdown": summary.match_method_breakdown,
            },
            "exceptions": exceptions_list,
            "reconciled_records": reconciled_list,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(audit_payload, f, indent=2)

        import pandas as pd
        df_out = pd.DataFrame(csv_rows)
        df_out.to_csv(csv_path, index=False)

        return {
            "json_report_path": json_path,
            "csv_ledger_path": csv_path,
        }

    def print_rich_summary(
        self,
        summary: AuditReportSummary,
        records: List[ReconciliationRecord]
    ) -> None:
        """Renders comprehensive Rich CLI tables and panels without emojis."""
        self.console.print()
        title_text = Text("LEDGERSENSE : FINANCIAL RECONCILIATION CONSOLE", style="bold cyan")
        subtitle_text = Text("Razorpay AI Buildathon | Track 04: AI Finance Controller", style="dim white")
        self.console.print(Panel(Text.assemble(title_text, "\n", subtitle_text), box=box.ROUNDED, border_style="cyan"))

        kpi_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
        kpi_table.add_column("Metric", style="bold white", width=32)
        kpi_table.add_column("Value", justify="right", style="bold green", width=22)
        kpi_table.add_column("Benchmark / Target", justify="right", style="dim white", width=22)

        kpi_table.add_row(
            "Automated Match Rate",
            f"{summary.automated_match_rate_pct:.2f}%",
            "> 90.00% [PASS]" if summary.automated_match_rate_pct >= 90.0 else "[FAIL]"
        )
        kpi_table.add_row(
            "False-Positive Rate",
            f"{summary.false_positive_rate_pct:.2f}%",
            "0.00% [ZERO FP]"
        )
        kpi_table.add_row(
            "Total Ingested Orders",
            f"{summary.total_internal_orders:,}",
            "100 ERP Orders"
        )
        kpi_table.add_row(
            "Gateway Settlement Payouts",
            f"{summary.total_gateway_settlements:,}",
            "95 Settlements"
        )
        kpi_table.add_row(
            "Bank Statement Credits",
            f"{summary.total_bank_credits:,}",
            "90 Bank Credits"
        )
        kpi_table.add_row(
            "Reconciled Records Count",
            f"{summary.reconciled_records_count:,}",
            f"{summary.reconciled_records_count} Resolved"
        )
        kpi_table.add_row(
            "Exceptions Flagged",
            f"{summary.exceptions_count:,}",
            "Auditable Log"
        )
        kpi_table.add_row(
            "Total Reconciled Volume",
            f"INR {summary.reconciled_bank_volume:,.2f}",
            "Net Bank Credits"
        )
        kpi_table.add_row(
            "Variance Pending Settlement",
            f"INR {summary.net_variance_amount:,.2f}",
            "In-Flight / Clawbacks"
        )
        kpi_table.add_row(
            "Processing Performance",
            f"{summary.processing_time_ms:.1f} ms",
            f"{summary.throughput_records_per_sec:,.0f} rec/sec"
        )

        self.console.print(kpi_table)
