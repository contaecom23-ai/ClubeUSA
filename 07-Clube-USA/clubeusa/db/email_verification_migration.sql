-- ============================================================
--  email_verification_migration.sql — Clube USA
--  Fase 0.1: confirmacao de email
--
--  Executar em bancos existentes que nao rodaram o schema.sql
--  completo com estas tabelas.
-- ============================================================

-- 1. Adiciona coluna email_verified em members
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_verified
  ON members (email_verified)
  WHERE email_verified = FALSE AND email_hash IS NOT NULL;

-- 2. Tabela de tokens de verificacao de email
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 do token (token nao fica em texto puro)
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evt_member    ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_evt_token     ON email_verification_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_evt_expires   ON email_verification_tokens (expires_at);
