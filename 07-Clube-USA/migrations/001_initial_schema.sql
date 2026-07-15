-- Fase 0.1: Tabela de usuários e perfil mínimo
-- Executar uma única vez no Supabase SQL Editor ou via psql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id                        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                     TEXT        UNIQUE NOT NULL,
    password_hash             TEXT        NOT NULL,
    full_name                 TEXT        NOT NULL,
    zip_code                  TEXT,
    email_confirmed           BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirm_token       TEXT        UNIQUE,
    email_confirm_expires_at  TIMESTAMPTZ,
    is_active                 BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Auto-atualizar updated_at em qualquer UPDATE
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
