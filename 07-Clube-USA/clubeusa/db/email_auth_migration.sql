-- ============================================================
--  email_auth_migration.sql — Clube USA — Fase 0.1
--  Adiciona campos para auth por email (aditivo, sem perda de dados)
-- ============================================================

-- Suporte a senha hashada para login por email
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS password_hash         TEXT,
  ADD COLUMN IF NOT EXISTS email_confirmed       BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirmation_token TEXT,
  ADD COLUMN IF NOT EXISTS email_token_expires_at   TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS zip_code             VARCHAR(10);

-- Garante unicidade do token (parcial: ignora NULLs)
CREATE UNIQUE INDEX IF NOT EXISTS idx_members_email_confirm_token
  ON members (email_confirmation_token)
  WHERE email_confirmation_token IS NOT NULL;

-- Lookup rapido para confirmar token
CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
  ON members (email_confirmed)
  WHERE email_confirmed = FALSE AND email_confirmation_token IS NOT NULL;
