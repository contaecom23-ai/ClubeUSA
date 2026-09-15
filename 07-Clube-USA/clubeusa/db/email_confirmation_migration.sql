-- ============================================================
--  Fase 0.1: confirmacao de email
--  Migracao ADITIVA — nao remove nem altera colunas existentes.
--  Aplicar no Supabase: SQL Editor > Run
-- ============================================================

-- Adiciona flag de confirmacao ao membro
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN members.email_confirmed IS
    'True quando o membro confirmou o email via link enviado. False nao bloqueia login (auth e por WhatsApp).';

-- Tabela de tokens de confirmacao de email (TTL gerenciado pela aplicacao)
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       TEXT NOT NULL UNIQUE,          -- secrets.token_urlsafe(32)
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,                   -- preenchido ao usar o token
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member  ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_token   ON email_confirmation_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_confirmation_tokens (expires_at);

-- Limpeza automatica de tokens expirados (opcional — pode rodar como cron no Supabase)
-- DELETE FROM email_confirmation_tokens WHERE expires_at < NOW() - INTERVAL '2 days';
