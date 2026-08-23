-- ============================================================
--  zip_search_migration.sql — Fase 1.2
--  Adiciona suporte a busca por ZIP + raio geografico
--  NAO destrutivo: ALTER TABLE apenas adiciona colunas
-- ============================================================

-- Coordenadas geograficas nos deals (para deals locais)
ALTER TABLE deals
    ADD COLUMN IF NOT EXISTS zip_code  VARCHAR(10),
    ADD COLUMN IF NOT EXISTS lat       NUMERIC(9,6),
    ADD COLUMN IF NOT EXISTS lng       NUMERIC(9,6),
    ADD COLUMN IF NOT EXISTS is_local  BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_deals_zip    ON deals (zip_code) WHERE zip_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deals_local  ON deals (is_local) WHERE is_local = TRUE;

-- ZIP do membro (definido no perfil; lat/lng preenchidos apos geocoding)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS zip_code  VARCHAR(10),
    ADD COLUMN IF NOT EXISTS member_lat NUMERIC(9,6),
    ADD COLUMN IF NOT EXISTS member_lng NUMERIC(9,6);

CREATE INDEX IF NOT EXISTS idx_members_zip ON members (zip_code) WHERE zip_code IS NOT NULL;
