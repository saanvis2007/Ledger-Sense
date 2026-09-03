from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    RECONCILED_STANDARD = "RECONCILED_STANDARD"
    RECONCILED_CUSTOM_FEE = "RECONCILED_CUSTOM_FEE"
    RECONCILED_BATCH = "RECONCILED_BATCH"
    IN_FLIGHT_SETTLEMENT = "IN_FLIGHT_SETTLEMENT"
    CHARGEBACK_DEDUCTION = "CHARGEBACK_DEDUCTION"
    UNREGISTERED_ORDER = "UNREGISTERED_ORDER"
    UNMATCHED_DISCREPANCY = "UNMATCHED_DISCREPANCY"


class InternalOrder(BaseModel):
    order_id: str
    created_at: str
    amount: float
    status: str


class RazorpaySettlement(BaseModel):
    payment_id: str
    order_id: str
    gross_amount: float
    fee: float
    tax: float
    net_settled: float
    utr: str
    settlement_date: str


class BankCredit(BaseModel):
    txn_date: str
    narration: str
    utr: str
    credit_amount: float
    running_balance: float


class ReconciliationRecord(BaseModel):
    model_config = {"extra": "allow"}

    reconciliation_id: str
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    utr: Optional[str] = None
    order_amount: Optional[float] = None
    gross_amount: Optional[float] = None
    fee: Optional[float] = None
    tax: Optional[float] = None
    net_settled: Optional[float] = None
    bank_credit_amount: Optional[float] = None
    variance: float = 0.0
    status: MatchStatus
    reconciliation_tier: str = "TIER_1_DETERMINISTIC"
    match_method: str = "Rule-Based"  # "Rule-Based", "Assisted", "Exception Review"
    confidence_score: float = 1.0
    root_cause: str = "Standard 1:1:1 Match"
    ai_diagnosis: str = ""
    reasoning: str
    evidence_used: List[str] = Field(default_factory=list)
    financial_impact: str = "Neutral"
    priority_level: str = "Low"  # "Critical", "High", "Medium", "Low"
    priority_score: int = 20
    priority_reason: str = ""
    action_required: Optional[str] = None
    action_status: str = "Completed / No Action"  # "Completed / No Action", "Pending Review", "Reviewed", "Approved / Resolved", "Rejected / Escalated"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditReportSummary(BaseModel):
    model_config = {"extra": "allow"}

    generated_at: str
    total_internal_orders: int
    total_gateway_settlements: int
    total_bank_credits: int
    reconciled_records_count: int
    exceptions_count: int
    automated_match_rate_pct: float
    false_positive_rate_pct: float
    total_internal_order_volume: float
    total_gateway_settled_volume: float
    total_bank_credited_volume: float
    reconciled_bank_volume: float
    net_variance_amount: float
    processing_time_ms: float = 0.0
    throughput_records_per_sec: float = 0.0
    status_breakdown: Dict[str, int]
    tier_breakdown: Dict[str, int]
    match_method_breakdown: Dict[str, int] = Field(default_factory=dict)
