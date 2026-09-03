# LedgerSense
### Two-Tier AI-Assisted Financial Reconciliation & Controller System
**Razorpay AI Buildathon | Track 04: AI Finance Controller**

---

## Executive Summary
**LedgerSense** is an AI-assisted financial reconciliation system designed for finance controllers to reconcile transactions across **Internal ERP Orders**, **Razorpay Gateway Settlements**, and **Bank Statement Credits**.

It implements a two-tier reconciliation architecture:
1. **Tier 1: High-Throughput Deterministic Matcher**: Handles instant 1:1:1 hash joins, validating order references, UTRs, and the standard Razorpay fee structure (**2.0% MDR + 18% GST** on MDR).
2. **Tier 2: AI-Assisted Exception Analysis & Reasoning Layer**: Operates on edge cases that fall outside standard 1:1:1 joins (such as contractual 1.5% enterprise fee tiers and multi-order batch settlement aggregations). Tier 2 provides:
   - **Explainable root-cause diagnosis**: Pinpoints transaction discrepancies such as dropped webhooks, customer disputes, or interbank clearing cycles.
   - **Exception prioritization**: Ranks unresolved cases (Critical, High, Medium, Low) based on financial exposure and urgency.
   - **Risk assessment**: Quantifies loss exposure and active evidentiary cutoff windows (e.g. 7-day dispute deadlines).
   - **Recommended controller actions**: Suggests concrete operational remediation steps for human finance operations controllers.

   *Note: All financial calculations and reconciliation matching are performed strictly by the deterministic rule engine, while AI-assisted reasoning is used for exception diagnosis, prioritization, and recommendations.*

---

## Performance and SLA Metrics
| Metric | LedgerSense Result | Benchmark / Target | Status |
|---|---|---|---|
| **Automated Match Rate** | **90.91%** | > 90.00% | PASS |
| **False-Positive Rate** | **0.00%** | 0.00% | ZERO FP |
| **Reconciled Records** | **90 / 99** | Complete resolution | PASS |
| **Pending Exceptions** | **9** | Audited with Root Cause | AUDITED |
| **Test Suite** | **10 / 10 Passing** | 100% Pass Rate | VERIFIED |

---

## System Architecture

```
                               ┌────────────────────────┐
                               │  Multi-Source Data In  │
                               └───────────┬────────────┘
                                           │
          ┌────────────────────────────────┼───────────────────────────────┐
          │                                │                               │
┌─────────▼──────────┐          ┌──────────▼───────────┐         ┌─────────▼──────────┐
│  Internal Orders   │          │ Razorpay Settlements │         │   Bank Statement   │
│   (100 records)    │          │     (95 records)     │         │    (90 records)    │
└─────────┬──────────┘          └──────────┬───────────┘         └─────────┬──────────┘
          │                                │                               │
          └────────────────────────────────┼───────────────────────────────┘
                                           │
                                           ▼
                 ┌──────────────────────────────────────────────────┐
                 │       Tier 1: Deterministic Rule Matcher         │
                 │   - Exact 1:1:1 join on Order ID & UTR           │
                 │   - Razorpay standard MDR formula verification   │
                 └──────────────┬────────────────────┬──────────────┘
                                │                    │
                        [Matches: 82]         [Unmatched Pool: 17]
                                │                    │
                                ▼                    ▼
                 ┌──────────────────────┐  ┌─────────────────────────────────┐
                 │ RECONCILED_STANDARD  │  │  Tier 2: AI Exception Reasoner  │
                 │  (100% Confidence)   │  │  - Custom Fee Tier (1.5% MDR)   │
                 └──────────────────────┘  │  - Multi-Order Batch Collapse   │
                                           │  - In-Flight T+1 Settlements    │
                                           │  - Phantom Gateway Payments     │
                                           │  - Dispute / Clawback Tagging   │
                                           └────────────────┬────────────────┘
                                                            │
                                  ┌─────────────────────────┴────────────────────────┐
                                  │                                                  │
                           [Resolved: 8]                                      [Exceptions: 9]
                                  │                                                  │
                 ┌────────────────┴──────────────────┐              ┌────────────────┴─────────────────┐
                 │ - RECONCILED_CUSTOM_FEE (5)       │              │ - IN_FLIGHT_SETTLEMENT (4)       │
                 │ - RECONCILED_BATCH (3)            │              │ - UNREGISTERED_ORDER (2)         │
                 └───────────────────────────────────┘              │ - CHARGEBACK_DEDUCTION (3)       │
                                                                    └──────────────────────────────────┘
```

---

## Injected Financial Edge Cases Handled

| Scenario | Count | Detection Mechanism | Diagnostic and Controller Action |
|---|:---:|---|---|
| **Standard Matches** | **82** | Tier 1 Deterministic | 1:1:1 exact join on `order_id` and `utr`. Verifies `fee == gross * 2%`, `tax == fee * 18%`, `net == gross - fee - tax == bank_credit`. |
| **Fee Tier Variations** | **5** | Tier 2 Custom MDR Heuristic | Flags transactions where effective rate is **1.5%** instead of 2.0%. Calculates fee savings and reconciles against bank credit. |
| **Batch Settlements** | **3** | Tier 2 Multi-Order Collapse | Collapses 2 internal orders per batch into 1 gateway payout and 1 single bank credit UTR. Confirms `sum(net_settled) == bank_credit`. |
| **In-Flight Settlements** | **4** | Tier 2 Clearing Cycle Tracker | Gateway settled today, awaiting bank credit under standard **T+1 interbank clearing cycle**. Auto-monitor next 24-48h. |
| **Phantom Payments** | **2** | Tier 2 Webhook Anomaly Reasoner | Payments captured in Razorpay with no matching internal order. Diagnoses dropped webhook or checkout bypass; prompts ERP order backfill. |
| **Chargeback Deductions** | **3** | Tier 2 Dispute Monitor | Internal orders flagged as `DISPUTED`. Withheld by processor; prompts Proof of Delivery upload before deadline. |

---

## Quickstart Guide

### 1. Installation
```bash
cd LedgerSense
pip install -r requirements.txt
```

### 2. Run Autonomous Reconciliation CLI
```bash
python run_reconciliation.py
```
This executes the 2-tier engine, prints a Rich terminal summary, and exports:
- `data/reconciliation_audit_report.json`
- `data/reconciled_ledger.csv`

### 3. Run Automated Test Suite
```bash
python -m pytest -v tests/test_reconciliation.py
```
*The current test suite contains 10 deterministic validation tests, all passing in the latest verified run.*

### 4. Launch Streamlit Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser to inspect metrics, filter ledger rows, explore the Exception Inspection Drawer, and download audit packages.

---

## Project Structure
```
LedgerSense/
├── data/
│   ├── internal_orders.csv               # 100 ERP orders
│   ├── razorpay_settlements.csv          # 95 Gateway settlements
│   ├── bank_statement.csv                # 90 Bank statement credits
│   ├── reconciliation_audit_report.json  # Machine-readable audit summary
│   └── reconciled_ledger.csv             # Full unified ledger with audit reasoning
├── src/
│   ├── __init__.py
│   ├── models.py                         # Pydantic schemas and MatchStatus enum
│   ├── generator.py                      # Deterministic synthetic data generator (seed=42)
│   ├── reconciler.py                     # Two-tier reconciliation engine
│   └── reporter.py                       # Audit report exporter and Rich CLI printer
├── tests/
│   ├── __init__.py
│   └── test_reconciliation.py           # 10 comprehensive unit and regression tests
├── app.py                                # Streamlit Controller Dashboard
├── run_reconciliation.py                 # CLI entry point
├── requirements.txt                      # Project dependencies
└── README.md                             # Documentation and architecture guide
```

---

## Auditing and Compliance
Every reconciliation run produces an immutable audit record containing:
- Ingestion counts and total currency volumes across all 3 ledgers.
- Automated match rate percentage and mathematical false-positive verification.
- Explicit line-item exception classification with root-cause explanations and suggested controller remedies.
