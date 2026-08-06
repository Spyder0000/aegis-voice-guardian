-- AEGIS Voice Guardian PostgreSQL schema
-- Owner: Okoh Darius

BEGIN;

CREATE TABLE IF NOT EXISTS trust_profile (
    user_id VARCHAR(128) PRIMARY KEY,
    known_recipients JSONB NOT NULL DEFAULT '[]'::jsonb,
    recipient_transfer_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    avg_transfer_amount NUMERIC(18, 2) NOT NULL DEFAULT 0
        CHECK (avg_transfer_amount >= 0),
    largest_transfer_amount NUMERIC(18, 2) NOT NULL DEFAULT 0
        CHECK (largest_transfer_amount >= 0),
    transfer_count INTEGER NOT NULL DEFAULT 0
        CHECK (transfer_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (jsonb_typeof(known_recipients) = 'array'),
    CHECK (jsonb_typeof(recipient_transfer_counts) = 'object')
);

CREATE TABLE IF NOT EXISTS trust_ledger (
    id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL
        REFERENCES trust_profile(user_id) ON DELETE RESTRICT,
    transcript TEXT,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0),
    recipient TEXT NOT NULL CHECK (length(trim(recipient)) > 0),
    risk_level VARCHAR(16) NOT NULL
        CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    action VARCHAR(16) NOT NULL
        CHECK (action IN ('released', 'held', 'escalated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ledger_transaction_action UNIQUE (transaction_id, action),
    CHECK (jsonb_typeof(reasons) = 'array')
);

CREATE INDEX IF NOT EXISTS idx_trust_ledger_user_created
    ON trust_ledger (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trust_ledger_transaction
    ON trust_ledger (transaction_id);
CREATE INDEX IF NOT EXISTS idx_trust_ledger_risk_action
    ON trust_ledger (risk_level, action);

COMMIT;
