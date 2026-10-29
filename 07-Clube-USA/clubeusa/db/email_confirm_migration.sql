-- ============================================================
--  email_confirm_migration.sql — Fase 0.1
--  Adiciona confirmacao de email aos membros
-- ============================================================

ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed            BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirm_token        TEXT        UNIQUE,
  ADD COLUMN IF NOT EXISTS email_confirm_expires_at   TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirm
  ON members (email_confirm_token)
  WHERE email_confirm_token IS NOT NULL;

COMMENT ON COLUMN members.email_confirmed          IS 'true apos o membro clicar no link de confirmacao';
COMMENT ON COLUMN members.email_confirm_token      IS 'token seguro gerado por secrets.token_urlsafe(32); limpo apos uso';
COMMENT ON COLUMN members.email_confirm_expires_at IS 'token expira em 24h; regenerado a cada reenvio';
