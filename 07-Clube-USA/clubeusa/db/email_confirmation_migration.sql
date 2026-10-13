-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: email confirmado
--
--  Executar em ordem no Supabase SQL Editor.
-- ============================================================

-- 1. Adiciona campo email_confirmed_at em members (idempotente)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

-- 2. Tabela de tokens de verificacao de email
--    - token_hash: HMAC do token enviado ao usuario (nunca guardar em texto puro)
--    - expira em 24h, uso unico (deletado apos verificacao)
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evt_member  ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_evt_expires ON email_verification_tokens (expires_at);

-- Limpeza automatica de tokens expirados (sem acumulo na tabela)
CREATE OR REPLACE FUNCTION cleanup_expired_email_tokens()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM email_verification_tokens WHERE expires_at < NOW();
END;
$$;
