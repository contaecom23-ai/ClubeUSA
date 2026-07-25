-- Migracao 002: Busca por ZIP + raio (Fase 1.2)
-- Execute DEPOIS de 001_initial_schema.sql
-- Seguro para re-executar (IF NOT EXISTS / IF NOT EXISTS ja tratado pelo ADD COLUMN IF NOT EXISTS)

-- =============================================================
-- Adiciona coordenadas geográficas às promoções existentes
-- NULL = promoção nacional (sem ZIP específico)
-- =============================================================
ALTER TABLE promotions
ADD COLUMN IF NOT EXISTS latitude  DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;

-- Index parcial: só indexa promoções com coordenadas (economiza espaço)
CREATE INDEX IF NOT EXISTS idx_promotions_geo
    ON promotions (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- =============================================================
-- Tabela de centroides de ZIP codes dos EUA
-- Populada via script: scripts/seed_zip_codes.py
-- ~33k registros (~2MB) — leve e sem dependência de PostGIS
-- =============================================================
CREATE TABLE IF NOT EXISTS zip_codes (
    zip       TEXT PRIMARY KEY,
    city      TEXT,
    state     TEXT NOT NULL,
    latitude  DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_zip_codes_state ON zip_codes (state);

COMMENT ON TABLE  zip_codes IS 'Centroides de ZIP codes dos EUA. Use scripts/seed_zip_codes.py para popular.';
COMMENT ON COLUMN promotions.latitude  IS 'Centroide da promoção. NULL = promoção nacional.';
COMMENT ON COLUMN promotions.longitude IS 'Centroide da promoção. NULL = promoção nacional.';
