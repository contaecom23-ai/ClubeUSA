-- ============================================================
--  email_confirm_migration.sql — Clube USA  (Fase 0.1)
--
--  Aplique no Supabase SQL Editor uma vez.
--  Idempotente: usa IF NOT EXISTS / IF EXISTS.
-- ============================================================

-- 1. Campo de confirmação no perfil do membro
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_email_confirmed
    ON members (email_confirmed_at)
    WHERE email_confirmed_at IS NOT NULL;

-- 2. Tabela de tokens de verificação de email
--    token_hash: SHA-256 do token URL-safe (nunca armazenar o token bruto)
--    TTL: 24 horas; só pode ser usado uma vez (used_at marca uso)
CREATE TABLE IF NOT EXISTS email_verify_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evtoken_member
    ON email_verify_tokens (member_id);

CREATE INDEX IF NOT EXISTS idx_evtoken_hash
    ON email_verify_tokens (token_hash);

-- 3. Limpeza periódica de tokens expirados (executar via cron ou manualmente)
--    CREATE OR REPLACE FUNCTION cleanup_expired_email_tokens()
--    RETURNS void LANGUAGE sql AS $$
--        DELETE FROM email_verify_tokens WHERE expires_at < NOW();
--    $$;
