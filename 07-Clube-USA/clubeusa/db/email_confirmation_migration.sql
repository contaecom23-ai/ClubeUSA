-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Adiciona confirmacao de email ao perfil do membro
--  e tabela de tokens de verificacao.
--
--  Execucao: rodar no painel SQL do Supabase (uma vez)
-- ============================================================

-- 1. Campo na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

-- Indice para consulta rapida de emails confirmados
CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed_at)
    WHERE email_confirmed_at IS NOT NULL;

-- 2. Tabela de tokens de verificacao de email
CREATE TABLE IF NOT EXISTS email_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_token     ON email_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_member    ON email_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires   ON email_tokens (expires_at);
