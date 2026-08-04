-- Migration 001 — Clube USA: base de usuários + confirmação de email
-- Aplicar no Supabase > SQL Editor (ou via supabase CLI: supabase db push)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               TEXT UNIQUE NOT NULL,
    password_hash       TEXT NOT NULL,
    full_name           TEXT NOT NULL,
    zip_code            TEXT,
    -- gerado no registro; usado pela Fase 0.2 (referral)
    referral_code       TEXT UNIQUE NOT NULL,
    -- preenchido na Fase 0.2 ao rastrear indicação
    referred_by_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    email_confirmed_at  TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- email_confirmations
-- ============================================================
CREATE TABLE IF NOT EXISTS email_confirmations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Índices
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_users_email         ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_email_conf_token    ON email_confirmations(token);
CREATE INDEX IF NOT EXISTS idx_email_conf_user     ON email_confirmations(user_id);

-- ============================================================
-- RLS habilitado como preparação — acesso atual é só server-side
-- via service_role (bypassa RLS). Policies adicionadas no futuro
-- quando o frontend acessar o Supabase diretamente.
-- ============================================================
ALTER TABLE users               ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_confirmations ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Auto-atualiza updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
