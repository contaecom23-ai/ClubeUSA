-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Adiciona suporte a confirmacao de email (Fase 0.1)
-- ============================================================

-- Colunas de confirmacao de email
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed       BOOLEAN      NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirm_token   TEXT,
  ADD COLUMN IF NOT EXISTS email_confirm_sent_at TIMESTAMPTZ;

-- Indice para lookup rapido do token (confirmacao via link)
CREATE INDEX IF NOT EXISTS idx_members_email_confirm_token
    ON members (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Comentario: email_confirmed=TRUE so quando o membro clica no link.
-- Membros que nao fornecem email ficam com email_confirmed=FALSE (nao bloqueante para login).
