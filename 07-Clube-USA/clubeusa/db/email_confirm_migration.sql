-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Fase 0.1: confirmação de email
--
--  Executa no Supabase SQL Editor (uma vez).
-- ============================================================

-- 1. Campo email_confirmed_at na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

-- 2. Tabela de tokens de confirmação de email (single-use, 24h TTL)
--    Armazena somente o hash SHA-256 do token — o raw token é enviado
--    apenas por email e nunca fica no banco.
CREATE TABLE IF NOT EXISTS email_confirm_tokens (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id  UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member  ON email_confirm_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_confirm_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_email_tokens_hash    ON email_confirm_tokens (token_hash);

-- Limpa tokens expirados/usados há mais de 7 dias (cron job ou chamada manual)
-- DELETE FROM email_confirm_tokens
-- WHERE used_at IS NOT NULL OR expires_at < NOW() - INTERVAL '7 days';
