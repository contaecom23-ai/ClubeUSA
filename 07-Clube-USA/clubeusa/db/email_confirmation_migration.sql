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

-- 2. Tabela de tokens de confirmação
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,        -- SHA-256 do token raw (nunca guardamos o token em texto puro)
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ect_member  ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_ect_token   ON email_confirmation_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_ect_expires ON email_confirmation_tokens (expires_at);
