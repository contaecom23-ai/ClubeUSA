-- Migration 007: housing — quartos, roommates, casas para alugar
-- Rodar APÓS 006_jobs.sql

CREATE TABLE IF NOT EXISTS housing (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title               TEXT        NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    description         TEXT        NOT NULL CHECK (char_length(description) BETWEEN 1 AND 2000),
    listing_type        TEXT        NOT NULL
                            CHECK (listing_type IN ('quarto_disponivel', 'precisa_quarto', 'casa_disponivel')),
    zip_code            TEXT        CHECK (zip_code ~ '^\d{5}$'),
    city                TEXT        CHECK (char_length(city) <= 80),
    state               TEXT        CHECK (state ~ '^[A-Z]{2}$'),
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    rent_monthly_cents  INTEGER     CHECK (rent_monthly_cents IS NULL OR rent_monthly_cents >= 0),
    bedrooms            SMALLINT    CHECK (bedrooms IS NULL OR bedrooms BETWEEN 0 AND 20),
    bathrooms           REAL        CHECK (bathrooms IS NULL OR bathrooms BETWEEN 0 AND 20),
    furnished           BOOLEAN     NOT NULL DEFAULT false,
    utilities_included  BOOLEAN     NOT NULL DEFAULT false,
    pets_allowed        BOOLEAN,
    available_from      TIMESTAMPTZ,
    contact_email       TEXT,
    contact_phone       TEXT,
    image_url           TEXT,
    expires_at          TIMESTAMPTZ,
    active              BOOLEAN     NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para os filtros mais comuns
CREATE INDEX IF NOT EXISTS idx_housing_active_created
    ON housing (active, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_housing_listing_type
    ON housing (listing_type) WHERE active = true;

CREATE INDEX IF NOT EXISTS idx_housing_state
    ON housing (state) WHERE active = true AND state IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_housing_zip
    ON housing (zip_code) WHERE active = true AND zip_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_housing_coords
    ON housing (latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Trigger para updated_at automático
CREATE OR REPLACE FUNCTION update_housing_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_housing_updated_at ON housing;
CREATE TRIGGER trg_housing_updated_at
    BEFORE UPDATE ON housing
    FOR EACH ROW EXECUTE FUNCTION update_housing_updated_at();

-- RLS: habilitado; acesso de leitura via service_role (backend) apenas
ALTER TABLE housing ENABLE ROW LEVEL SECURITY;

-- Política: service_role tem acesso total (backend usa service_role)
CREATE POLICY housing_service_role_all ON housing
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
