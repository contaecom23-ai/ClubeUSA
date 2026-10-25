-- ============================================================
--  email_confirm_migration.sql — Clube USA
--  FASE 0.1: confirmacao de email
--
--  Executar no Supabase SQL Editor (uma vez, idempotente).
-- ============================================================

-- 1. Adicionar colunas de verificacao de email na tabela members
ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_confirmed       BOOLEAN     NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_verify_token    TEXT        UNIQUE,
  ADD COLUMN IF NOT EXISTS email_verify_expires  TIMESTAMPTZ;

-- Indice para lookup rapido por token (usado na confirmacao)
CREATE INDEX IF NOT EXISTS idx_members_email_verify
  ON members (email_verify_token)
  WHERE email_verify_token IS NOT NULL;

-- 2. Indice para buscar membros com email nao confirmado (util para reenvio em massa)
CREATE INDEX IF NOT EXISTS idx_members_unconfirmed_email
  ON members (email_confirmed, created_at)
  WHERE email_enc IS NOT NULL AND email_confirmed = FALSE;

-- ============================================================
--  COMO USAR
--  Apos rodar esta migration, o fluxo e:
--  1. Cadastro com email -> token gerado no backend -> email enviado
--  2. Usuario clica no link -> POST /auth/email/confirm
--  3. email_confirmed = true, token apagado
-- ============================================================
