-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Idempotente: pode ser executado multiplas vezes sem erro
--  Parte do Fase 0.1: confirmacao de email
-- ============================================================

-- Adiciona colunas de confirmacao de email na tabela members
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed     BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirmed_at  TIMESTAMPTZ;

-- Indice para busca rapida de membros sem email confirmado
CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_confirmed = FALSE;

-- Tabela de tokens de confirmacao de email
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ect_member
    ON email_confirmation_tokens (member_id);

CREATE INDEX IF NOT EXISTS idx_ect_token
    ON email_confirmation_tokens (token_hash);

CREATE INDEX IF NOT EXISTS idx_ect_expires
    ON email_confirmation_tokens (expires_at)
    WHERE used_at IS NULL;
