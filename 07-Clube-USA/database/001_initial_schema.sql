-- ============================================================
-- Clube USA - Schema inicial (Fase 0.1)
-- Fonte de verdade: todo insert/query deve estar alinhado aqui.
-- Rode no Supabase SQL Editor ou via psql com service_role.
-- ============================================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT UNIQUE NOT NULL,
    email_confirmed                 BOOLEAN DEFAULT FALSE NOT NULL,
    email_confirmation_token        TEXT,
    email_confirmation_expires_at   TIMESTAMPTZ,
    password_hash                   TEXT NOT NULL,

    -- Perfil mínimo (Fase 0.1)
    full_name                       TEXT,
    zip_code                        TEXT,
    phone                           TEXT,

    -- Controle
    is_active                       BOOLEAN DEFAULT TRUE NOT NULL,
    created_at                      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at                      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_login_at                   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_email_confirmation_token ON users (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- ------------------------------------------------------------
-- REFRESH TOKENS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    revoked_at  TIMESTAMPTZ,
    user_agent  TEXT,
    ip_address  TEXT
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);

-- ------------------------------------------------------------
-- AUTO-UPDATE updated_at
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ------------------------------------------------------------
-- RLS (Row Level Security) — endgame; desabilitado por enquanto.
-- O backend acessa via service_role, que bypassa RLS.
-- Quando ativar RLS, descomentar e revisar as políticas.
-- ------------------------------------------------------------
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY users_self ON users
--     FOR ALL USING (id = auth.uid());
-- CREATE POLICY refresh_tokens_self ON refresh_tokens
--     FOR ALL USING (user_id = auth.uid());
