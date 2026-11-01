-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  Fase 0.1: confirmação de email
--
--  Seguro para rodar em banco existente:
--  ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS
-- ============================================================

-- 1. Campo email_confirmed na tabela members
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Tabela de tokens de verificação (single-use, TTL 24h, hash SHA-256)
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 do token enviado ao usuário
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evtoken_member  ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_evtoken_expires ON email_verification_tokens (expires_at);
CREATE INDEX IF NOT EXISTS idx_evtoken_hash    ON email_verification_tokens (token_hash);

-- 3. RLS: member vê apenas seus próprios tokens
ALTER TABLE email_verification_tokens ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'email_verification_tokens'
          AND policyname = 'evtoken_own'
    ) THEN
        CREATE POLICY evtoken_own ON email_verification_tokens
            FOR SELECT USING (member_id = auth.uid());
    END IF;
END;
$$;

-- 4. Limpeza automática de tokens expirados (job via pg_cron ou chamado manualmente)
-- Execute periodicamente:
-- DELETE FROM email_verification_tokens WHERE expires_at < NOW() OR used = TRUE;
