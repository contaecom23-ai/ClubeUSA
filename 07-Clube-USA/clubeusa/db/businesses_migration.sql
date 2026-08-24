-- Migration: Phase 2.1 — Business Directory
-- Creates businesses table with premium subscription support

CREATE TABLE IF NOT EXISTS businesses (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id                UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    name                    TEXT NOT NULL CHECK (char_length(name) BETWEEN 2 AND 100),
    description             TEXT CHECK (char_length(description) <= 1000),
    category                VARCHAR(50) NOT NULL,
    zip_code                VARCHAR(5) NOT NULL,
    city                    TEXT,
    state                   VARCHAR(50),
    website                 TEXT,
    phone_enc               TEXT,
    plan                    VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'premium')),
    stripe_customer_id      TEXT UNIQUE,
    stripe_subscription_id  TEXT UNIQUE,
    premium_started_at      TIMESTAMPTZ,
    premium_expires_at      TIMESTAMPTZ,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_businesses_owner_id   ON businesses (owner_id);
CREATE INDEX IF NOT EXISTS idx_businesses_zip_code   ON businesses (zip_code);
CREATE INDEX IF NOT EXISTS idx_businesses_category   ON businesses (category);
CREATE INDEX IF NOT EXISTS idx_businesses_plan       ON businesses (plan);
CREATE INDEX IF NOT EXISTS idx_businesses_is_active  ON businesses (is_active);

-- Reuse existing update_updated_at() function from members table
CREATE TRIGGER trg_businesses_updated
    BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;

-- Public directory: anyone can see active businesses
CREATE POLICY businesses_select ON businesses
    FOR SELECT USING (is_active = TRUE OR owner_id = auth.uid());

-- Only owner can insert their own business
CREATE POLICY businesses_insert ON businesses
    FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Only owner can update their own business
CREATE POLICY businesses_update ON businesses
    FOR UPDATE USING (owner_id = auth.uid());
