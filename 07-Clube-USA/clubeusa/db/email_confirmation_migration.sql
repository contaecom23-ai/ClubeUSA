-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: confirmacao de email
--
--  Aplique com cuidado em producao (ALTER TABLE e seguro sem
--  lock de longa duracao, mas confirme com o DBA).
--
--  Como rodar: execute este arquivo no SQL Editor do Supabase
--  ou via psql como service_role.
-- ============================================================

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed        BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_token            TEXT        UNIQUE,
    ADD COLUMN IF NOT EXISTS email_token_expires_at TIMESTAMPTZ;

-- Indice parcial: so cria entrada para linhas com token ativo
-- (evita index cheio de NULLs)
CREATE INDEX IF NOT EXISTS idx_members_email_token
    ON members (email_token)
    WHERE email_token IS NOT NULL;

-- Comentario de auditoria
COMMENT ON COLUMN members.email_confirmed        IS 'True se o usuario confirmou o email pelo link enviado.';
COMMENT ON COLUMN members.email_token            IS 'Token de confirmacao de email (UUID url-safe, 32 bytes). Apagado apos uso.';
COMMENT ON COLUMN members.email_token_expires_at IS 'Expiracao do token de confirmacao (TTL 24h).';
