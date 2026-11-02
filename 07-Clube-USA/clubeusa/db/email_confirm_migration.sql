-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Fase 0.1: Email confirmado
--
--  Executa UMA vez no Supabase SQL Editor.
-- ============================================================

-- 1. Coluna de verificacao no members (idempotente com IF NOT EXISTS)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_verified
    ON members (email_verified)
    WHERE deleted_at IS NULL;

-- 2. Tokens de confirmacao de email (TTL + uso unico)
CREATE TABLE IF NOT EXISTS email_confirm_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_token
    ON email_confirm_tokens (token);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member
    ON email_confirm_tokens (member_id);

-- Limpa tokens expirados automaticamente (nao ha dado sensivel aqui, so UUIDs)
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires
    ON email_confirm_tokens (expires_at)
    WHERE used_at IS NULL;
