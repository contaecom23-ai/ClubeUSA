-- ============================================================
-- Clube USA — Migração 001: Schema inicial
-- Execute no Supabase: Dashboard > SQL Editor > Run
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================
-- Tabela: users
-- ==============================
CREATE TABLE IF NOT EXISTS users (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   VARCHAR(255) UNIQUE NOT NULL,
    password_hash           VARCHAR(255) NOT NULL,
    full_name               VARCHAR(255) NOT NULL,
    phone                   VARCHAR(50),
    state_us                VARCHAR(2),
    city                    VARCHAR(100),
    zip_code                VARCHAR(10),
    is_email_confirmed      BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirm_token     VARCHAR(255),
    email_confirm_expires_at TIMESTAMPTZ,
    is_active               BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================
-- Tabela: refresh_tokens
-- ==============================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at  TIMESTAMPTZ,
    user_agent  VARCHAR(500),
    ip_address  VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
    ON refresh_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
    ON refresh_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at
    ON refresh_tokens(expires_at)
    WHERE revoked_at IS NULL;

-- ==============================
-- RLS (Row Level Security) — ENDGAME
-- Habilitar após validar o modelo de dados.
-- Por enquanto: acesso apenas via service_role no servidor.
-- ==============================
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
