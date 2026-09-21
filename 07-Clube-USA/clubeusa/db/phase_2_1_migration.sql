-- ============================================================
--  Phase 2.1 migration — local business subscription
--  Non-destructive: CREATE TABLE IF NOT EXISTS
--
--  Run in Supabase SQL Editor before deploying Phase 2.1 code.
-- ============================================================

CREATE TABLE IF NOT EXISTS businesses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_hash          TEXT NOT NULL UNIQUE,
    phone_enc           TEXT NOT NULL,
    email_hash          TEXT UNIQUE,
    email_enc           TEXT,
    name                TEXT NOT NULL,
    owner_name          TEXT,
    zip_code            VARCHAR(10),
    city                TEXT,
    state               VARCHAR(50),
    category            VARCHAR(50),
    description         TEXT,
    website             TEXT,
    plan                VARCHAR(20) NOT NULL DEFAULT 'free'
                        CHECK (plan IN ('free','basic','premium')),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','active','suspended','rejected')),
    stripe_customer_id  TEXT UNIQUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_businesses_phone    ON businesses (phone_hash);
CREATE INDEX IF NOT EXISTS idx_businesses_zip      ON businesses (zip_code) WHERE zip_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses (category) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_businesses_status   ON businesses (status);

-- Reuse the existing update_updated_at() trigger function from schema.sql
CREATE TRIGGER IF NOT EXISTS trg_businesses_updated
    BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS: businesses may only read/update their own row
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;

CREATE POLICY businesses_select_own ON businesses
    FOR SELECT USING (id = auth.uid());

CREATE POLICY businesses_update_own ON businesses
    FOR UPDATE USING (id = auth.uid())
    WITH CHECK (
        plan    = (SELECT plan    FROM businesses WHERE id = auth.uid()) AND
        status  = (SELECT status  FROM businesses WHERE id = auth.uid())
    );
