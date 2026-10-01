-- ============================================================
--  email_confirmation_migration.sql
--  Fase 0.1 — adiciona confirmacao de email aos membros
--
--  Como aplicar:
--    Execute via Supabase SQL Editor ou psql antes de
--    fazer deploy da API com os novos endpoints de email.
-- ============================================================

-- 1. Nova coluna no members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

-- Index parcial: rapido para buscar confirmados
CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed) WHERE email_confirmed = TRUE;

-- 2. Tabela de tokens de confirmacao de email
CREATE TABLE IF NOT EXISTS email_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_hash  TEXT NOT NULL,
    token       VARCHAR(6) NOT NULL,
    attempts    SMALLINT NOT NULL DEFAULT 0,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_hash    ON email_tokens (email_hash);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_tokens (expires_at);
