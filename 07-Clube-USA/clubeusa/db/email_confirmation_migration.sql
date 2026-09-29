-- ============================================================
--  email_confirmation_migration.sql
--  Fase 0.1: adiciona confirmacao de email ao sistema
--
--  COMO APLICAR: cole no SQL Editor do Supabase (ou psql)
--  Idempotente: usa IF NOT EXISTS / DO $$ ... END $$
-- ============================================================

-- 1. Adiciona email_confirmed na tabela members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='members' AND column_name='email_confirmed'
    ) THEN
        ALTER TABLE members
            ADD COLUMN email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_enc IS NOT NULL;

-- 2. Tabela de tokens de confirmacao de email
--    token_hash = SHA-256 do token bruto (nunca armazenar token em texto puro)
--    Single-use: deletado apos confirmacao ou expiracao
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member
    ON email_confirmation_tokens (member_id);

CREATE INDEX IF NOT EXISTS idx_email_tokens_expires
    ON email_confirmation_tokens (expires_at);
