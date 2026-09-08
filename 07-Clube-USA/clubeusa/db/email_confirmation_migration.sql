-- ============================================================
--  email_confirmation_migration.sql — Clube USA
--  Confirmacao de email para completar Fase 0.1
--
--  Execucao: Supabase SQL Editor (uma vez, idempotente)
-- ============================================================

-- 1. Adiciona colunas em members (IF NOT EXISTS = idempotente)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed    BOOLEAN    NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

-- 2. Tabela de tokens de confirmacao de email
CREATE TABLE IF NOT EXISTS email_confirmations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_conf_member  ON email_confirmations (member_id);
CREATE INDEX IF NOT EXISTS idx_email_conf_token   ON email_confirmations (token_hash);
CREATE INDEX IF NOT EXISTS idx_email_conf_expires ON email_confirmations (expires_at);

-- 3. RLS: token so pode ser lido pelo proprio servidor (service_role)
--    Nao habilitamos RLS nesta tabela porque o acesso ja e exclusivo
--    via service_role key (nunca exposta ao cliente).

-- 4. Indice parcial para busca eficiente de tokens nao usados
CREATE INDEX IF NOT EXISTS idx_email_conf_unused
    ON email_confirmations (token_hash)
    WHERE used_at IS NULL;
