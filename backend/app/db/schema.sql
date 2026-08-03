-- AEGIS Voice Guardian schema
-- Owner: Okoh Darius

CREATE TABLE IF NOT EXISTS trust_profile (
    user_id UUID PRIMARY KEY,
    known_recipients JSONB DEFAULT '[]',
    avg_transfer_amount NUMERIC,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trust_ledger (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES trust_profile(user_id),
    transcript TEXT,
    amount NUMERIC,
    recipient TEXT,
    risk_level TEXT,
    reasons JSONB,
    action TEXT, -- released | held | escalated
    created_at TIMESTAMP DEFAULT now()
);
