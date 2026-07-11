-- Migration 001: Users table + email verification + refresh tokens
-- Fase 0.1 — Cadastro + perfil mínimo + email confirmado

-- Enable pgcrypto for gen_random_uuid() on older PG versions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ──────────────────────────────────────────────────────────────────────────────
-- USERS
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email                       TEXT UNIQUE NOT NULL,
  password_hash               TEXT NOT NULL,
  name                        TEXT NOT NULL,
  zip_code                    TEXT,
  state_abbr                  CHAR(2),   -- US state abbreviation (e.g. "FL")
  email_verified              BOOLEAN NOT NULL DEFAULT FALSE,
  -- verification token stored as hash (token itself is sent in email, never stored plain)
  email_verification_token_hash TEXT,
  email_verification_sent_at  TIMESTAMPTZ,
  email_verified_at           TIMESTAMPTZ,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);

-- ──────────────────────────────────────────────────────────────────────────────
-- REFRESH TOKENS
-- One active refresh token per user session; stored as hash, short-lived, revocable.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);

-- ──────────────────────────────────────────────────────────────────────────────
-- RATE-LIMIT LOG (used by the auth endpoints to enforce per-IP/email limits)
-- Lightweight; a background job can prune entries older than 1 day.
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_rate_limit (
  id         BIGSERIAL PRIMARY KEY,
  key        TEXT NOT NULL,           -- e.g. "login:1.2.3.4" or "register:user@mail.com"
  action     TEXT NOT NULL,           -- "login" | "register" | "resend_verification"
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_key_action ON auth_rate_limit(key, action, attempted_at);

-- ──────────────────────────────────────────────────────────────────────────────
-- updated_at auto-trigger
-- ──────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ──────────────────────────────────────────────────────────────────────────────
-- RLS (Row Level Security) — enabled as endgame policy, enforced server-side
-- for now. Enable RLS but grant service_role full access; anon/authenticated
-- roles get nothing here — all access goes through the API.
-- ──────────────────────────────────────────────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_rate_limit ENABLE ROW LEVEL SECURITY;

-- service_role bypasses RLS by default in Supabase — no extra policy needed.
-- Deny all access to anon and authenticated roles explicitly.
CREATE POLICY deny_anon_users ON users FOR ALL TO anon, authenticated USING (false);
CREATE POLICY deny_anon_refresh ON refresh_tokens FOR ALL TO anon, authenticated USING (false);
CREATE POLICY deny_anon_ratelimit ON auth_rate_limit FOR ALL TO anon, authenticated USING (false);
