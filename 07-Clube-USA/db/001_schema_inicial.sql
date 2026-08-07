-- =============================================================
-- CLUBE USA — Schema Inicial (Fase 0.1)
-- Rodar no Supabase SQL Editor (como service_role / postgres)
-- RLS ativado como endgame; até lá, acesso 100% via backend
--   com service_role key (nunca expor anon key a dados sensíveis)
-- =============================================================

-- Extensão para UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------
-- USERS
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT        UNIQUE NOT NULL,
    password_hash                   TEXT        NOT NULL,
    is_email_confirmed              BOOLEAN     NOT NULL DEFAULT FALSE,
    -- token enviado no email; não é hash aqui (token de uso único, TTL 24h)
    -- para hardening futuro: armazenar bcrypt(token)
    confirmation_token              TEXT,
    confirmation_token_expires_at   TIMESTAMPTZ,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
    ON users (confirmation_token)
    WHERE confirmation_token IS NOT NULL;

-- ---------------------------------------------------------------
-- PROFILES  (1:1 com users)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name   TEXT,
    city        TEXT,
    state       TEXT,
    zip_code    TEXT,
    phone       TEXT,
    bio         TEXT        CHECK (char_length(bio) <= 500),
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id
    ON profiles (user_id);

-- ---------------------------------------------------------------
-- Trigger: atualiza updated_at automaticamente
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------
-- RLS (endgame — não ativar até migrar para acesso client-side)
-- Deixado aqui para referência; habilitar com cuidado:
--   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
--   ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
-- ---------------------------------------------------------------
