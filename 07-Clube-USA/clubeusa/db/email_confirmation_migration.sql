-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: email confirmado
--
--  Roda uma vez no Supabase (SQL Editor).
--  Idempotente: usa IF NOT EXISTS / IF EXISTS.
-- ============================================================

-- 1. Colunas na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed               BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_confirmation_token      TEXT,
    ADD COLUMN IF NOT EXISTS email_confirmation_expires_at TIMESTAMPTZ;

-- 2. Indice para lookup rapido por token (nulo nao indexado = economico)
CREATE INDEX IF NOT EXISTS idx_members_email_confirm_token
    ON members (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- 3. Indice: membros com email confirmado (filtra cadastros validos)
CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_confirmed = TRUE;
