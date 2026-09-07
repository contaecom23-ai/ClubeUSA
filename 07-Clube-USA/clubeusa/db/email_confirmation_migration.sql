-- ============================================================
--  email_confirmation_migration.sql — Clube USA  Fase 0.1
--  Adiciona suporte a confirmacao de email
-- ============================================================

-- Coluna na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed_at)
    WHERE email_confirmed_at IS NOT NULL;

-- Tabela de tokens de confirmacao
-- Regra de seguranca: armazena apenas o HASH do token, nunca o raw.
-- Token raw e enviado no link de email e nunca toca o banco.
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ect_member  ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_ect_expires ON email_confirmation_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_ect_hash    ON email_confirmation_tokens (token_hash);

-- Expira tokens antigos automaticamente (limpeza periodica via cron do Supabase)
-- Sugestao: rodar "DELETE FROM email_confirmation_tokens WHERE expires_at < NOW()" diariamente
