-- ============================================================
--  email_verification_migration.sql — Clube USA
--  Adiciona suporte a confirmacao de email
--
--  Aplicar APOS schema.sql principal.
--  Idempotente: usa IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.
-- ============================================================

-- 1. Coluna email_verified na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_verified ON members (email_verified)
    WHERE email_verified = TRUE;

-- 2. Tabela de tokens de verificacao de email (uso unico, TTL 24h)
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evtoken_member  ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_evtoken_expires ON email_verification_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_evtoken_token   ON email_verification_tokens (token);
