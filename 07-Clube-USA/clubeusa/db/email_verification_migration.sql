-- ============================================================
--  email_verification_migration.sql — Clube USA
--  Adiciona verificacao de email a tabela members
--  e cria tabela de tokens de verificacao.
--
--  Executar UMA VEZ no banco de producao/staging.
-- ============================================================

-- 1. Adiciona colunas de verificacao em members (idempotente)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified    BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_verified
    ON members (email_verified) WHERE email_verified = TRUE;

-- 2. Tabela de tokens de verificacao
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_verify_token
    ON email_verification_tokens (token)
    WHERE used_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_email_verify_member
    ON email_verification_tokens (member_id);
