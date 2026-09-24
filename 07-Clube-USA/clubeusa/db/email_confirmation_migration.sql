-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Adiciona confirmação de email aos membros
--
--  Aplicar via Supabase Dashboard > SQL Editor
--  Idempotente: usa IF NOT EXISTS / ADD COLUMN IF NOT EXISTS
-- ============================================================

-- 1. Colunas na tabela members
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed     BOOLEAN    NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_confirmed_at  TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_confirmed = FALSE;

-- 2. Tabela de tokens de confirmação
-- Regra de segurança: armazena apenas o HASH do token, nunca o raw.
-- Token raw é enviado no link de email e nunca toca o banco.
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ect_member  ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_ect_token   ON email_confirmation_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_ect_expires ON email_confirmation_tokens (expires_at);

-- Limpeza periódica de tokens expirados (sugestão: rodar via Supabase cron diariamente)
-- DELETE FROM email_confirmation_tokens WHERE expires_at < NOW();
