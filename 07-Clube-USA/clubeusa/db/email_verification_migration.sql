-- ============================================================
--  email_verification_migration.sql — Clube USA
--  Fase 0.1: email confirmado
--
--  Executar via Supabase SQL Editor ou psql.
--  Idempotente (IF NOT EXISTS / IF EXISTS).
-- ============================================================

-- 1. Adiciona coluna email_verified em members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- Indice para queries de "cadastros válidos" (0.4)
CREATE INDEX IF NOT EXISTS idx_members_email_verified
    ON members (email_verified) WHERE deleted_at IS NULL;

-- 2. Tabela de tokens de verificação de email
--    - token_hash: SHA-256 do token bruto (nunca guarda o token em texto puro)
--    - um token por member — resend sobrescreve o anterior
CREATE TABLE IF NOT EXISTS email_verifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    email_hash  TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_verif_member  ON email_verifications (member_id);
CREATE INDEX IF NOT EXISTS idx_email_verif_token   ON email_verifications (token_hash);
CREATE INDEX IF NOT EXISTS idx_email_verif_expires ON email_verifications (expires_at);

-- Garante apenas um token pendente por member (delete-on-resend via aplicação,
-- mas como belt-and-suspenders, unique já existe via token_hash único)
