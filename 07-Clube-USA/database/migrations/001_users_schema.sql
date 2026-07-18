-- Migration 001: Users and refresh tokens schema
-- Fase 0.1 — Cadastro + perfil mínimo + email confirmado
--
-- Execute on Supabase SQL Editor or via psql.
-- RLS is disabled for now (server-side access via service_role).
-- Enable RLS per table as a future hardening step (Fase 0.x endgame).

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   TEXT UNIQUE NOT NULL,
    email_confirmed         BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token     TEXT,                           -- raw token (cryptographically random, not a password)
    email_confirm_sent_at   TIMESTAMPTZ,
    password_hash           TEXT NOT NULL,
    full_name               TEXT NOT NULL,
    phone                   TEXT,
    zip_code                TEXT,
    city                    TEXT,
    state                   TEXT,
    -- tracks >=1 real action for "cadastro válido" (Fase 0.4)
    actions_count           INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partial index: fast lookup of unconfirmed tokens (only rows with pending token)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON users (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Refresh tokens — one row per active session; one-time-use
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,       -- cryptographically random, stored directly (not a password)
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,               -- set when consumed; row kept briefly for replay detection
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token   ON refresh_tokens (token);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_updated_at ON users;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMIT;
