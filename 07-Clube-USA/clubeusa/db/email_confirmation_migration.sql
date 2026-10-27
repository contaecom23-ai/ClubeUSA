-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Fase 0.1: confirmacao de email
--  Aplicar com: psql $DATABASE_URL < email_confirmation_migration.sql
-- ============================================================

-- Coluna de confirmacao no perfil do membro
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed_at)
    WHERE email_confirmed_at IS NOT NULL;

-- Tabela de tokens de confirmacao de email (TTL 24h)
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_tokens_member  ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_email_tokens_token   ON email_confirmation_tokens (token);
CREATE INDEX IF NOT EXISTS idx_email_tokens_expires ON email_confirmation_tokens (expires_at);

-- Um membro so pode ter um token pendente por vez.
-- A logica de negocio apaga o anterior antes de criar novo (ver email_service.py).
-- Nao usamos UNIQUE (member_id) aqui para evitar race condition na delecao.
