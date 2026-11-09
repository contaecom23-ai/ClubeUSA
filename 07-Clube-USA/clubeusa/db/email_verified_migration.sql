-- ============================================================
--  Fase 0.1: Confirmacao de email
--  Rodar no Supabase SQL Editor (or via migration tool)
-- ============================================================

-- 1. Coluna no perfil do membro
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Tabela de tokens de verificacao
--    Armazena apenas o HASH do token (nao o token bruto) — igual ao pattern de reset de senha.
--    Token bruto vai somente no email do usuario e nunca em banco.
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,       -- SHA-256(token_bruto)
    expires_at  TIMESTAMPTZ NOT NULL,       -- TTL: 1 hora
    used_at     TIMESTAMPTZ,                -- NULL = nao usado ainda
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evtoken_member  ON email_verification_tokens (member_id);
CREATE INDEX IF NOT EXISTS idx_evtoken_hash    ON email_verification_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_evtoken_expires ON email_verification_tokens (expires_at);

-- Limpeza automatica de tokens expirados (opcional, executar periodicamente)
-- DELETE FROM email_verification_tokens WHERE expires_at < NOW() - INTERVAL '7 days';
