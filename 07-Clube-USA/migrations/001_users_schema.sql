-- Fase 0.1: Usuários, perfis mínimos e confirmação de email
-- FONTE DE VERDADE — todo insert/query deve cruzar com este schema

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid()

-- Tabela principal de usuários
CREATE TABLE IF NOT EXISTS users (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                     TEXT UNIQUE NOT NULL,
    password_hash             TEXT NOT NULL,
    name                      TEXT NOT NULL,
    estado                    CHAR(2),           -- estado americano (FL, TX, NY ...)
    cidade                    TEXT,
    whatsapp                  TEXT,              -- opcional, sem formatação
    email_confirmed           BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token       TEXT UNIQUE,       -- token one-time; NULL após confirmação
    email_confirm_expires_at  TIMESTAMPTZ,
    is_active                 BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at             TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token ON users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Refresh tokens (armazenados para permitir revogação)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token   ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

COMMIT;
