-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Adiciona suporte a confirmacao de email em members.
--
--  Executar uma vez no Supabase SQL Editor.
-- ============================================================

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed          BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_confirm_token      TEXT,
    ADD COLUMN IF NOT EXISTS email_confirm_expires_at TIMESTAMPTZ;

-- Indice para lookup rapido do token (usado em POST /auth/email/verify)
CREATE INDEX IF NOT EXISTS idx_members_email_confirm_token
    ON members (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- Comentario explicativo
COMMENT ON COLUMN members.email_confirmed          IS 'True apos o usuario clicar no link de confirmacao enviado por email.';
COMMENT ON COLUMN members.email_confirm_token      IS 'Token de confirmacao de email (hash SHA-256 do token raw). Apagado apos uso.';
COMMENT ON COLUMN members.email_confirm_expires_at IS 'TTL do token de confirmacao. Padrao: 24h apos o registro.';
