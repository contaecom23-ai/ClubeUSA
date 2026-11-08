-- ============================================================
--  email_verification_migration.sql — Fase 0.1
--
--  Adiciona verificacao de email:
--  1. Campo email_verified na tabela members
--  2. Tabela email_verification_tokens (tokens com TTL 24h)
--
--  Executar uma vez no Supabase SQL Editor.
--  Idempotente: usa IF NOT EXISTS / IF NOT EXISTS.
-- ============================================================

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_verified
    ON members (email_verified) WHERE email_hash IS NOT NULL;

-- Tokens de verificacao: UUID, member_id, token (hash), TTL, estado
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ev_member  ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_ev_expires ON email_verification_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_ev_token   ON email_verification_tokens (token_hash);
