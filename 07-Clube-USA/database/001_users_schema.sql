-- Migration 001: Initial users table for Clube USA (Fase 0.1)
-- Run this in the Supabase SQL editor ONCE, in order.
-- Never run destructively without owner approval (see DECISOES.md).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT        UNIQUE NOT NULL,
    password_hash                   TEXT        NOT NULL,
    full_name                       TEXT        NOT NULL,
    zip_code                        TEXT,
    email_confirmed                 BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirmation_token        TEXT,
    email_confirmation_expires_at   TIMESTAMPTZ,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on every row change
CREATE OR REPLACE FUNCTION _set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION _set_updated_at();

-- Fast email lookup (login, register duplicate check)
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

-- Fast token lookup during email confirmation
CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
    ON users (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- Row Level Security
-- All DB access goes through our FastAPI with service_role key (bypasses RLS).
-- RLS blocks any accidental direct client access via anon/authenticated roles.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "block_direct_client_select" ON users FOR SELECT USING (FALSE);
CREATE POLICY "block_direct_client_insert" ON users FOR INSERT WITH CHECK (FALSE);
CREATE POLICY "block_direct_client_update" ON users FOR UPDATE USING (FALSE);
CREATE POLICY "block_direct_client_delete" ON users FOR DELETE USING (FALSE);
-- Note: service_role key bypasses all RLS → our API can still read/write.
-- When we implement per-user JWT auth (Fase futura), we replace the USING (FALSE)
-- policies above with USING (id = auth.uid()) for the authenticated role only.
