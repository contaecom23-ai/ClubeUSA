-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Adiciona suporte a confirmação de email (Fase 0.1)
--
--  Aplique no Supabase SQL Editor ou via CLI.
--  Idempotente: usa ADD COLUMN IF NOT EXISTS.
-- ============================================================

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at              TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS email_confirmation_token        TEXT,
    ADD COLUMN IF NOT EXISTS email_confirmation_token_expires TIMESTAMPTZ;

-- Índice para lookup por token (busca direta O(log n))
CREATE UNIQUE INDEX IF NOT EXISTS idx_members_email_confirm_token
    ON members (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;
