-- ============================================================
--  jobs_migration.sql — Clube USA Fase 1.4 (Empregos)
--  Rode DEPOIS de schema.sql
-- ============================================================

-- ============================================================
--  jobs — vagas de emprego (seed manual pelo admin, Fase 1.4)
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title            TEXT NOT NULL,
    company          TEXT NOT NULL,
    description      TEXT NOT NULL,
    city             TEXT,
    state_code       VARCHAR(2),
    zip_code         VARCHAR(10),
    employment_type  VARCHAR(20) NOT NULL DEFAULT 'full_time'
                     CHECK (employment_type IN ('full_time','part_time','contract','temp')),
    category         VARCHAR(30) NOT NULL DEFAULT 'other'
                     CHECK (category IN (
                         'construction','cleaning','food_service','retail',
                         'healthcare','tech','transportation','domestic','other'
                     )),
    salary_min       NUMERIC(10,2),
    salary_max       NUMERIC(10,2),
    salary_period    VARCHAR(10) DEFAULT 'hour'
                     CHECK (salary_period IN ('hour','week','month','year')),
    contact_url      TEXT,            -- link externo para candidatura (publico)
    language         VARCHAR(2) NOT NULL DEFAULT 'pt' CHECK (language IN ('pt','es')),
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at       TIMESTAMPTZ,
    posted_by_admin  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_active   ON jobs (is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_jobs_zip      ON jobs (zip_code);
CREATE INDEX IF NOT EXISTS idx_jobs_state    ON jobs (state_code);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs (category);
CREATE INDEX IF NOT EXISTS idx_jobs_created  ON jobs (created_at DESC);

CREATE TRIGGER trg_jobs_updated
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS: jobs são públicos para leitura; writes via service_role apenas
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY jobs_public_select ON jobs
    FOR SELECT USING (
        is_active = TRUE
        AND (expires_at IS NULL OR expires_at > NOW())
    );
