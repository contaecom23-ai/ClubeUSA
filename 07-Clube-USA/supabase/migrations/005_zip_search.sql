-- Fase 1.2: Busca por ZIP + raio 1-5 milhas
-- Tabela de lookup de coordenadas por ZIP code (US Census ZCTA centroids)
-- Seed: data/seed_zip_codes.sql (principais ZIPs comunidades brasileiras)
CREATE TABLE IF NOT EXISTS zip_codes (
    zip        TEXT    PRIMARY KEY CHECK (zip ~ '^\d{5}$'),
    city       TEXT    NOT NULL,
    state      TEXT    NOT NULL CHECK (char_length(state) = 2),
    latitude   FLOAT8  NOT NULL,
    longitude  FLOAT8  NOT NULL
);

-- Adicionar coordenadas desnormalizadas na tabela de promoções.
-- Preenchidas automaticamente no insert (service layer) via lookup em zip_codes.
-- Desnormalização intencional para evitar join custoso em cada busca geográfica.
ALTER TABLE promotions
    ADD COLUMN IF NOT EXISTS latitude  FLOAT8,
    ADD COLUMN IF NOT EXISTS longitude FLOAT8;

-- Índice para promoções locais (com coordenadas)
CREATE INDEX IF NOT EXISTS idx_promotions_geo
    ON promotions (latitude, longitude)
    WHERE active = true AND latitude IS NOT NULL;

-- RLS: somente service_role acessa — padrão do projeto
ALTER TABLE zip_codes ENABLE ROW LEVEL SECURITY;
