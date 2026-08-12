-- Fase 0.1: Cadastro + perfil mínimo + email confirmado
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor > New query)
-- Safe to re-run (uses IF NOT EXISTS / CREATE OR REPLACE)

CREATE TABLE IF NOT EXISTS users (
  id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email                   TEXT        UNIQUE NOT NULL,
  password_hash           TEXT        NOT NULL,
  first_name              TEXT        NOT NULL,
  last_name               TEXT        NOT NULL,
  zip_code                TEXT,
  email_confirmed         BOOLEAN     NOT NULL DEFAULT FALSE,
  confirmation_token      TEXT,
  confirmation_expires_at TIMESTAMPTZ,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
  ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
  ON users(confirmation_token)
  WHERE confirmation_token IS NOT NULL;

-- RLS enabled — backend uses service_role so all access is server-side.
-- No permissive client policies until we move to client-side RLS (Fase futura).
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
