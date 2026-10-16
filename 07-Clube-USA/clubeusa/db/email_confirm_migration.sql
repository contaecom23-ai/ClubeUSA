-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Fase 0.1: adiciona confirmacao de email
-- ============================================================

-- Campo email_confirmed na tabela members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_enc IS NOT NULL;

-- Tabela de tokens de confirmacao de email
CREATE TABLE IF NOT EXISTS email_confirm_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_confirm_token   ON email_confirm_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_confirm_member  ON email_confirm_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_confirm_expires ON email_confirm_tokens (expires_at);

-- Limpeza periodica de tokens expirados/usados (via pg_cron ou chamada manual)
-- DELETE FROM email_confirm_tokens WHERE expires_at < NOW() - INTERVAL '7 days' OR used = TRUE;
