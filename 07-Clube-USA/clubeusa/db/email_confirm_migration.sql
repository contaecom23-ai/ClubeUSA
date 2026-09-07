-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Adiciona suporte a confirmacao de email
--
--  Aplicar com service_role no Supabase SQL Editor.
--  Seguro de re-executar (IF NOT EXISTS).
-- ============================================================

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed      BOOLEAN    NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_confirm_token  TEXT       UNIQUE,
    ADD COLUMN IF NOT EXISTS email_confirm_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_confirm_token
    ON members (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

COMMENT ON COLUMN members.email_confirmed IS
    'TRUE quando o membro clicou no link de confirmacao enviado por email';
COMMENT ON COLUMN members.email_confirm_token IS
    'Token opaco (URL-safe, 32 bytes) para confirmar email. Apagado apos uso.';
COMMENT ON COLUMN members.email_confirm_sent_at IS
    'Timestamp do ultimo envio de confirmacao (para rate-limit de reenvio).';
