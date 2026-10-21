-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: confirmação de email
--
--  Aplique via Supabase SQL Editor (Settings > SQL Editor)
--  ou psql em uma conexão direta ao banco.
--
--  Seguro para rodar em banco existente: usa IF NOT EXISTS.
-- ============================================================

ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed          BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirm_token      VARCHAR(80) UNIQUE,
  ADD COLUMN IF NOT EXISTS email_confirm_expires_at TIMESTAMPTZ;

-- Índice parcial: permite múltiplos NULLs (já confirmados) sem conflito
CREATE INDEX IF NOT EXISTS idx_members_confirm_token
  ON members (email_confirm_token)
  WHERE email_confirm_token IS NOT NULL;
