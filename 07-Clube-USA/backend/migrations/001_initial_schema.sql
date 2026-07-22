-- Migration 001: schema inicial do Clube USA
-- Aplique no Supabase via SQL Editor com a service_role key.
-- Nao contém dados sensíveis; segredo fica apenas nas env vars.

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------
-- Tabela: users (entidade central de autenticação)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT        UNIQUE NOT NULL,
    password_hash   TEXT        NOT NULL,
    full_name       TEXT        NOT NULL,
    email_confirmed BOOLEAN     NOT NULL DEFAULT false,
    -- token temporário para confirmar email (nulo após confirmação)
    email_confirmation_token    TEXT    UNIQUE,
    email_confirmation_expires_at TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- Tabela: profiles (dados adicionais 1:1 com users)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    zip_code    TEXT,
    city        TEXT,
    state_code  CHAR(2),        -- código de estado dos EUA, ex: "FL"
    phone       TEXT,
    bio         TEXT        CHECK (length(bio) <= 500),
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- Tabela: refresh_tokens (rotação de sessão)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT        UNIQUE NOT NULL,   -- SHA-256 do token; nunca armazenar plaintext
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,                   -- null = ainda válido
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------
-- Índices
-- -----------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
    ON users(email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
    ON refresh_tokens(token_hash);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
    ON refresh_tokens(user_id);

-- -----------------------------------------------------------------------
-- Função: atualizar updated_at automaticamente
-- -----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
