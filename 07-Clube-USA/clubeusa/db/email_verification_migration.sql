-- ============================================================
--  email_verification_migration.sql — Clube USA
--  Confirmaçao de email: adiciona email_verified em members
--  e cria tabela email_tokens para tokens de confirmacao.
--  Executar no Supabase > SQL Editor.
-- ============================================================

-- 1. Coluna email_verified na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Tabela de tokens de email (confirmacao e futuramente reset de senha)
CREATE TABLE IF NOT EXISTS email_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       TEXT NOT NULL UNIQUE,
    token_type  VARCHAR(30) NOT NULL DEFAULT 'email_verification'
                CHECK (token_type IN ('email_verification', 'password_reset')),
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_token   ON email_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_member  ON email_tokens (member_id, token_type);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_tokens (expires_at);
