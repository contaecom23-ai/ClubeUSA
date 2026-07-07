-- Fase 1.1: Promoções/Achados — carro-chefe da plataforma
-- Admin cria via X-Admin-Key; usuários visualizam sem autenticação.
CREATE TABLE IF NOT EXISTS promotions (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title         TEXT        NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    description   TEXT        NOT NULL CHECK (char_length(description) BETWEEN 1 AND 1000),
    store         TEXT        NOT NULL CHECK (char_length(store) BETWEEN 1 AND 100),
    category      TEXT        NOT NULL,
    zip_code      TEXT        CHECK (zip_code IS NULL OR zip_code ~ '^\d{5}$'),
    expires_at    TIMESTAMPTZ,
    discount_url  TEXT        CHECK (discount_url IS NULL OR discount_url ~* '^https?://'),
    discount_code TEXT        CHECK (discount_code IS NULL OR char_length(discount_code) <= 50),
    image_url     TEXT        CHECK (image_url IS NULL OR image_url ~* '^https?://'),
    active        BOOLEAN     NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para listagem pública: ativas, mais recentes primeiro
CREATE INDEX IF NOT EXISTS idx_promotions_active_created
    ON promotions (created_at DESC)
    WHERE active = true;

-- Trigger updated_at automático
CREATE OR REPLACE FUNCTION update_promotions_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_promotions_updated_at ON promotions;
CREATE TRIGGER trg_promotions_updated_at
    BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION update_promotions_updated_at();

-- RLS: habilitado sem policies — somente service_role acessa (mesmo padrão das outras tabelas)
ALTER TABLE promotions ENABLE ROW LEVEL SECURITY;
