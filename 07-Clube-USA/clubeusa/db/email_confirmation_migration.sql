-- ============================================================
--  email_confirmation_migration.sql — Clube USA  Fase 0.1
--  APPLY: execute no Supabase SQL editor (Settings > SQL Editor)
--  Seguro re-executar (IF NOT EXISTS protege).
-- ============================================================

-- 1. Coluna de confirmacao de email no perfil do membro
ALTER TABLE members ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed_at)
    WHERE email_confirmed_at IS NOT NULL;

-- 2. Tabela de tokens de email (confirmacao; extensivel para reset de senha)
CREATE TABLE IF NOT EXISTS email_tokens (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id  UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token      VARCHAR(64) NOT NULL UNIQUE,
    token_type VARCHAR(20) NOT NULL DEFAULT 'email_confirm'
               CHECK (token_type IN ('email_confirm', 'password_reset')),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_token
    ON email_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_member
    ON email_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires
    ON email_tokens (expires_at);
