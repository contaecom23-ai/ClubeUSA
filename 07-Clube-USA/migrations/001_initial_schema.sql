-- ============================================================
-- Clube USA — Migração 001: Schema inicial (Fase 0.1)
-- Como executar: cole no SQL Editor do Supabase (painel web)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Tabela de usuários ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT        UNIQUE NOT NULL,
    password_hash                   TEXT        NOT NULL,
    full_name                       TEXT        NOT NULL,
    zip_code                        TEXT,
    phone                           TEXT,
    email_confirmed                 BOOLEAN     NOT NULL DEFAULT FALSE,
    -- Token gerado pelo servidor (secrets.token_urlsafe(32)), NULL após confirmar
    email_confirmation_token        TEXT        UNIQUE,
    email_confirmation_expires_at   TIMESTAMPTZ,
    -- Código de referral gerado pelo servidor (secrets.token_urlsafe(6).upper())
    referral_code                   TEXT        UNIQUE NOT NULL,
    referred_by_id                  UUID        REFERENCES users(id) ON DELETE SET NULL,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para lookups frequentes
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_referral_code
    ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_email_confirmation_token
    ON users(email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- Atualização automática de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS habilitado; o servidor acessa com service_role (que bypassa RLS).
-- Políticas de acesso por anon key virão nas fases seguintes.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
