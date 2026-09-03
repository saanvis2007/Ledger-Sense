-- LedgerSense Supabase Schema
-- Track 04: AI Finance Controller | Razorpay AI Buildathon

-- 1. Internal Orders (ERP / Platform Data)
CREATE TABLE IF NOT EXISTS internal_orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(32) NOT NULL,
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_internal_orders_order_id ON internal_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_internal_orders_status ON internal_orders(status);

-- 2. Razorpay Settlements (Payment Gateway Data)
CREATE TABLE IF NOT EXISTS razorpay_settlements (
    id BIGSERIAL PRIMARY KEY,
    payment_id VARCHAR(64) UNIQUE NOT NULL,
    order_id VARCHAR(128) NOT NULL,
    gross_amount NUMERIC(12, 2) NOT NULL,
    fee NUMERIC(12, 2) NOT NULL,
    tax NUMERIC(12, 2) NOT NULL,
    net_settled NUMERIC(12, 2) NOT NULL,
    utr VARCHAR(64) NOT NULL,
    settlement_date TIMESTAMP WITH TIME ZONE NOT NULL,
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gateway_order_id ON razorpay_settlements(order_id);
CREATE INDEX IF NOT EXISTS idx_gateway_utr ON razorpay_settlements(utr);

-- 3. Bank Statement (Bank Account Credits)
CREATE TABLE IF NOT EXISTS bank_statements (
    id BIGSERIAL PRIMARY KEY,
    txn_date DATE NOT NULL,
    narration TEXT NOT NULL,
    utr VARCHAR(64) NOT NULL,
    credit_amount NUMERIC(12, 2) NOT NULL,
    running_balance NUMERIC(14, 2) NOT NULL,
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bank_utr ON bank_statements(utr);

-- 4. Reconciled Ledger Audit Records
CREATE TABLE IF NOT EXISTS reconciliation_records (
    id BIGSERIAL PRIMARY KEY,
    reconciliation_id VARCHAR(128) UNIQUE NOT NULL,
    order_id VARCHAR(128),
    payment_id VARCHAR(64),
    utr VARCHAR(64),
    order_amount NUMERIC(12, 2),
    gross_amount NUMERIC(12, 2),
    fee NUMERIC(12, 2),
    tax NUMERIC(12, 2),
    net_settled NUMERIC(12, 2),
    bank_credit_amount NUMERIC(12, 2),
    variance NUMERIC(12, 2) DEFAULT 0.00,
    status VARCHAR(64) NOT NULL,
    tier VARCHAR(64) NOT NULL,
    confidence_score NUMERIC(4, 2) NOT NULL,
    root_cause_reasoning TEXT NOT NULL,
    action_required TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    reconciled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rec_status ON reconciliation_records(status);
CREATE INDEX IF NOT EXISTS idx_rec_tier ON reconciliation_records(tier);
CREATE INDEX IF NOT EXISTS idx_rec_utr ON reconciliation_records(utr);

-- 5. Audit Run Summaries
CREATE TABLE IF NOT EXISTS audit_summaries (
    id BIGSERIAL PRIMARY KEY,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    total_internal_orders INT NOT NULL,
    total_gateway_settlements INT NOT NULL,
    total_bank_credits INT NOT NULL,
    reconciled_records_count INT NOT NULL,
    exceptions_count INT NOT NULL,
    automated_match_rate_pct NUMERIC(6, 2) NOT NULL,
    false_positive_rate_pct NUMERIC(6, 2) NOT NULL,
    total_internal_order_volume NUMERIC(14, 2) NOT NULL,
    total_gateway_settled_volume NUMERIC(14, 2) NOT NULL,
    total_bank_credited_volume NUMERIC(14, 2) NOT NULL,
    reconciled_bank_volume NUMERIC(14, 2) NOT NULL,
    net_variance_amount NUMERIC(14, 2) NOT NULL,
    status_breakdown JSONB NOT NULL,
    tier_breakdown JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE internal_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE razorpay_settlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_summaries ENABLE ROW LEVEL SECURITY;

-- Read-only policy for authenticated or anon key
CREATE POLICY "Allow read access to all users" ON reconciliation_records FOR SELECT USING (true);
CREATE POLICY "Allow read access to audit summary" ON audit_summaries FOR SELECT USING (true);
