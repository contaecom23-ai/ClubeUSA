-- ============================================================
--  jobs_migration.sql — Clube USA — Fase 1.4
--  Vagas de emprego (seed manual nas primeiras semanas)
--  Aplicar no Supabase SQL Editor apos schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS job_listings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    description     TEXT NOT NULL,
    location_city   TEXT,
    location_state  VARCHAR(2),
    zip_code        VARCHAR(10),
    job_type        VARCHAR(20) NOT NULL DEFAULT 'full_time'
                    CHECK (job_type IN ('full_time','part_time','contract','gig','internship')),
    salary_min      INTEGER,
    salary_max      INTEGER,
    salary_period   VARCHAR(10) DEFAULT 'hour'
                    CHECK (salary_period IN ('hour','week','month','year')),
    contact_email   TEXT,
    contact_url     TEXT,
    posted_by       UUID REFERENCES members(id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_active ON job_listings (is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_zip    ON job_listings (zip_code);
CREATE INDEX IF NOT EXISTS idx_jobs_type   ON job_listings (job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_state  ON job_listings (location_state);

CREATE TRIGGER trg_jobs_updated
    BEFORE UPDATE ON job_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS: membros autenticados leem vagas ativas, apenas server-side (service_role) escreve.
ALTER TABLE job_listings ENABLE ROW LEVEL SECURITY;

CREATE POLICY jobs_authenticated_read ON job_listings
    FOR SELECT
    USING (
        is_active = TRUE
        AND (expires_at IS NULL OR expires_at > NOW())
    );
