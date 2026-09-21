-- ============================================================
--  email_confirm_migration.sql — Fase 0.1
--  Adiciona confirmação de e-mail aos membros
--  SAFE: apenas ADD COLUMN (nunca DROP/ALTER que perde dado)
-- ============================================================

-- 1. Coluna de estado de confirmação no members
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed)
    WHERE email_hash IS NOT NULL;

-- 2. Tabela de tokens de confirmação (TTL gerenciado pela app)
CREATE TABLE IF NOT EXISTS email_confirmation_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,      -- SHA-256 do token; token bruto NUNCA armazenado
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ect_member   ON email_confirmation_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_ect_expires  ON email_confirmation_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_ect_token    ON email_confirmation_tokens (token_hash);

-- RLS: tokens são server-side only (service_role), sem acesso anon
ALTER TABLE email_confirmation_tokens ENABLE ROW LEVEL SECURITY;
