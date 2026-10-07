-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: adiciona suporte a confirmacao de email
--
--  Aplique no Supabase SQL Editor (Settings > SQL Editor).
--  Seguro para re-aplicar (IF NOT EXISTS / DO $$ guards).
-- ============================================================

-- 1. Adiciona coluna email_confirmed na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed) WHERE email_hash IS NOT NULL;

-- 2. Tabela de tokens de confirmacao de email
--    Single-use, TTL de 24h, vinculado ao member_id
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 do token; nunca armazena o token em texto puro
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,            -- NULL = nao usado ainda
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member
    ON email_confirmation_tokens (member_id);

CREATE INDEX IF NOT EXISTS idx_email_tokens_expires
    ON email_confirmation_tokens (expires_at);

-- 3. Cleanup: remove tokens expirados automaticamente (via job agendado no Supabase)
--    Execute manualmente ou configure como cron job no Supabase:
--    DELETE FROM email_confirmation_tokens WHERE expires_at < NOW();
