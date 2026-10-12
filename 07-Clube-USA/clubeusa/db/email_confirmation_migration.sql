-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Adiciona suporte a verificacao de email no cadastro
--
--  Aplicar com: psql $DATABASE_URL -f email_confirmation_migration.sql
--  Seguro para re-executar (usa IF NOT EXISTS / idempotente).
-- ============================================================

-- Adiciona campo de confirmacao de email nos membros
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed         BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_verification_token TEXT        UNIQUE,
    ADD COLUMN IF NOT EXISTS email_token_expires_at  TIMESTAMPTZ;

-- Indice para lookup rapido do token (link de verificacao)
CREATE INDEX IF NOT EXISTS idx_members_email_token
    ON members (email_verification_token)
    WHERE email_verification_token IS NOT NULL;

-- Membros existentes que nao tem email = marcados como nao-aplicavel
-- (nao quebra nada; email_confirmed=FALSE para quem tem email, undefined para quem nao tem)
