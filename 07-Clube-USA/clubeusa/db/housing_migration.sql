-- ============================================================
--  housing_migration.sql — Clube USA — Fase 1.5
--  Moradia: quartos, roommates, apartamentos, casas (seed manual)
--  Aplicar no Supabase SQL Editor após schema.sql e jobs_migration.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS housing_listings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    listing_type        VARCHAR(20) NOT NULL DEFAULT 'room'
                        CHECK (listing_type IN ('room','roommate','apartment','house')),
    price_monthly       NUMERIC(8,2) NOT NULL CHECK (price_monthly >= 0),
    utilities_included  BOOLEAN NOT NULL DEFAULT FALSE,
    location_city       TEXT,
    location_state      VARCHAR(2),
    zip_code            VARCHAR(10),
    bedrooms            SMALLINT,
    bathrooms           NUMERIC(3,1),
    gender_preference   VARCHAR(10) NOT NULL DEFAULT 'any'
                        CHECK (gender_preference IN ('any','male','female')),
    pets_allowed        BOOLEAN NOT NULL DEFAULT FALSE,
    move_in_date        DATE,
    contact_email       TEXT,
    contact_phone       TEXT,
    contact_whatsapp    TEXT,
    posted_by           UUID REFERENCES members(id) ON DELETE SET NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_housing_active  ON housing_listings (is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_housing_zip     ON housing_listings (zip_code);
CREATE INDEX IF NOT EXISTS idx_housing_state   ON housing_listings (location_state);
CREATE INDEX IF NOT EXISTS idx_housing_type    ON housing_listings (listing_type);
CREATE INDEX IF NOT EXISTS idx_housing_price   ON housing_listings (price_monthly);

-- update_updated_at() definida em schema.sql
CREATE TRIGGER trg_housing_updated
    BEFORE UPDATE ON housing_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS: membros autenticados leem listagens ativas; service_role escreve.
ALTER TABLE housing_listings ENABLE ROW LEVEL SECURITY;

CREATE POLICY housing_authenticated_read ON housing_listings
    FOR SELECT
    USING (
        is_active = TRUE
        AND (expires_at IS NULL OR expires_at > NOW())
    );
