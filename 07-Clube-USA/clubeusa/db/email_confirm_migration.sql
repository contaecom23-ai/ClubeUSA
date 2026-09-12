-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Adiciona campos para confirmacao de email (Fase 0.1)
--
--  Executar no Supabase SQL Editor.
--  Nao ha dado perdido: ADD COLUMN IF NOT EXISTS e idempotente.
-- ============================================================

ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed          BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirm_token      TEXT        UNIQUE,
  ADD COLUMN IF NOT EXISTS email_confirm_expires_at TIMESTAMPTZ;

-- Index para busca eficiente por token (lookup no momento da confirmacao)
CREATE INDEX IF NOT EXISTS idx_members_confirm_token
  ON members (email_confirm_token)
  WHERE email_confirm_token IS NOT NULL;

-- Comentarios explicativos
COMMENT ON COLUMN members.email_confirmed          IS 'Email verificado pelo usuario via link (false se nao forneceu email ou ainda nao confirmou)';
COMMENT ON COLUMN members.email_confirm_token      IS 'Token one-time-use para confirmacao de email (nullado apos uso)';
COMMENT ON COLUMN members.email_confirm_expires_at IS 'Expiracao do token de confirmacao (24h apos geracao)';
