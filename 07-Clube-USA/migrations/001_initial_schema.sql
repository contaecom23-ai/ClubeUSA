-- Clube USA — Migration 001: Schema inicial
-- Execute via Supabase SQL Editor (Dashboard > SQL Editor > New Query)

-- Extensão para UUID gerado no servidor
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- TABELA: users
-- Todos os dados são isolados por user_id (multi-tenant).
-- Acesso apenas server-side com service_role key.
-- RLS será habilitado quando toda query estiver via backend.
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email                    TEXT         NOT NULL UNIQUE,
    password_hash            TEXT         NOT NULL,
    full_name                TEXT,
    city                     TEXT,
    state_abbr               CHAR(2),     -- sigla do estado dos EUA (ex: "FL", "TX")
    email_confirmed          BOOLEAN      NOT NULL DEFAULT FALSE,
    email_confirm_token      TEXT,
    email_confirm_expires_at TIMESTAMPTZ,
    is_active                BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_confirm_token
    ON users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================
-- TABELA: rate_limits
-- Controle simples de brute-force (IP ou email como chave).
-- Janela: entradas com created_at > NOW() - interval são contadas.
-- Para escala (10k+), migrar para Redis.
-- =============================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    key        TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_key_created
    ON rate_limits(key, created_at);

-- Limpeza periódica via cron do Supabase (pg_cron) - configurar após deploy:
-- SELECT cron.schedule('limpar-rate-limits', '0 * * * *',
--   $$DELETE FROM rate_limits WHERE created_at < NOW() - INTERVAL '1 hour'$$);
