-- Fase 1.4: Empregos — seed manual nas primeiras semanas
-- Admin cria via X-Admin-Key; usuários visualizam sem autenticação.
-- Vagas com zip_code recebem lat/lng auto-preenchido pelo backend (via tabela zip_codes).
CREATE TABLE IF NOT EXISTS jobs (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title         TEXT        NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    company       TEXT        NOT NULL CHECK (char_length(company) BETWEEN 1 AND 100),
    description   TEXT        NOT NULL CHECK (char_length(description) BETWEEN 1 AND 2000),
    category      TEXT        NOT NULL,
    job_type      TEXT        NOT NULL,
    zip_code      TEXT        CHECK (zip_code IS NULL OR zip_code ~ '^\d{5}$'),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    salary_range  TEXT        CHECK (salary_range IS NULL OR char_length(salary_range) <= 100),
    apply_url     TEXT        CHECK (apply_url IS NULL OR apply_url ~* '^https?://'),
    contact_email TEXT        CHECK (contact_email IS NULL OR contact_email ~* '^[^@]+@[^@]+\.[^@]+$'),
    active        BOOLEAN     NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at    TIMESTAMPTZ,

    CONSTRAINT jobs_category_valid CHECK (
        category IN ('construcao','limpeza','restaurante','motorista','cuidado',
                     'beleza','vendas','escritorio','tecnologia','saude','outros')
    ),
    CONSTRAINT jobs_job_type_valid CHECK (
        job_type IN ('full_time','part_time','contract','gig')
    )
);

-- Listagem pública: ativas, mais recentes primeiro
CREATE INDEX IF NOT EXISTS idx_jobs_active_created
    ON jobs (created_at DESC)
    WHERE active = true;

-- Filtro por categoria (frequente no frontend)
CREATE INDEX IF NOT EXISTS idx_jobs_category
    ON jobs (category)
    WHERE active = true;

-- Busca geográfica Haversine (filtragem em Python no MVP)
-- Índice por zip para lookup rápido
CREATE INDEX IF NOT EXISTS idx_jobs_zip_code
    ON jobs (zip_code)
    WHERE active = true AND zip_code IS NOT NULL;

-- Trigger updated_at
CREATE OR REPLACE FUNCTION update_jobs_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON jobs;
CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_jobs_updated_at();

-- RLS: habilitado sem policies — somente service_role acessa (mesmo padrão das outras tabelas)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
