-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Fase 0.1: adiciona confirmação de email
--
--  Aplicar com: psql $DATABASE_URL < db/email_confirm_migration.sql
-- ============================================================

-- 1. Adiciona flag de verificacao em members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Tabela de tokens de confirmacao de email
--    Um token por membro; sobrescrito a cada novo pedido.
CREATE TABLE IF NOT EXISTS email_confirm_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 do token — nunca guardar token em claro
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member  ON email_confirm_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_confirm_tokens (expires_at);

-- Remove tokens expirados automaticamente (cleanup via cron no Supabase ou pg_cron)
-- Enquanto nao ha cron configurado, a aplicacao limpa no momento da verificacao.

COMMENT ON TABLE email_confirm_tokens IS
    'Tokens de confirmacao de email (TTL 24h). Token armazenado como hash SHA-256.';
COMMENT ON COLUMN email_confirm_tokens.token_hash IS
    'SHA-256 do token enviado por email. O token em claro vai apenas no link enviado ao usuario.';
