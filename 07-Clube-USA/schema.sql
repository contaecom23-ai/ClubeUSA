-- ClubeUSA Database Schema — Fase 0.1
-- Execute no Supabase SQL Editor (Database → SQL Editor → New query)
-- IMPORTANTE: rodar como superuser (o editor do Supabase usa service_role por padrão)

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- TABELA: users
-- Identidade + perfil + estado de auth
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT UNIQUE NOT NULL,
    password_hash                   TEXT NOT NULL,
    name                            TEXT NOT NULL,
    phone                           TEXT,
    state                           TEXT,           -- sigla US: CA, TX, FL...
    city                            TEXT,
    zip_code                        TEXT,

    -- Email confirmation
    email_confirmed_at              TIMESTAMPTZ,
    email_confirm_token             TEXT,
    email_confirm_token_expires_at  TIMESTAMPTZ,

    -- Password reset
    password_reset_token            TEXT,
    password_reset_token_expires_at TIMESTAMPTZ,

    -- Account state
    is_active                       BOOLEAN NOT NULL DEFAULT true,
    force_password_change           BOOLEAN NOT NULL DEFAULT false,

    -- Referral (Fase 0.2): colunas criadas agora para evitar ALTER TABLE destrutivo depois
    referral_code                   TEXT UNIQUE,
    referred_by_user_id             UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email          ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_referral_code  ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by    ON users(referred_by_user_id);

-- =============================================================
-- TABELA: refresh_tokens
-- Server-side token rotation (TTL curto + revogação explícita)
-- =============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 do token; o token raw nunca é salvo
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ             -- NULL = válido; preenchido = revogado
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id    ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- =============================================================
-- TABELA: events
-- Log de eventos de analytics — imutável (insert-only, sem update/delete)
-- =============================================================
CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL = evento anônimo ou usuário deletado
    event_type  TEXT NOT NULL,   -- user_registered | email_confirmed | user_login | referral_used
    metadata    JSONB,           -- payload arbitrário por tipo de evento
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_user_id    ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);

-- =============================================================
-- TRIGGER: updated_at automático em users
-- =============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- TABELA: promotions
-- Promoções/achados curados — leitura pública, escrita via admin
-- =============================================================
CREATE TABLE IF NOT EXISTS promotions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    url         TEXT NOT NULL,              -- link para o deal original (externo)
    image_url   TEXT,
    category    TEXT NOT NULL,              -- supermercado | restaurante | roupa | eletronica | servicos | saude | educacao | transporte | outros
    zip_code    TEXT,                       -- NULL = nacional / todos os ZIPs
    state       TEXT,                       -- NULL = nacional
    expires_at  TIMESTAMPTZ,               -- NULL = sem expiração
    is_featured BOOLEAN NOT NULL DEFAULT false,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_promotions_is_active  ON promotions(is_active);
CREATE INDEX IF NOT EXISTS idx_promotions_category   ON promotions(category);
CREATE INDEX IF NOT EXISTS idx_promotions_state      ON promotions(state);
CREATE INDEX IF NOT EXISTS idx_promotions_zip_code   ON promotions(zip_code);
CREATE INDEX IF NOT EXISTS idx_promotions_expires_at ON promotions(expires_at);

DROP TRIGGER IF EXISTS trg_promotions_updated_at ON promotions;
CREATE TRIGGER trg_promotions_updated_at
    BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- RLS (Row Level Security) — endgame, ativar após validação
-- Até lá: acesso exclusivamente server-side via service_role
-- =============================================================
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
-- (descomentar quando RLS estiver implementado com policies corretas)
