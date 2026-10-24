-- Migration: email confirmation for FASE 0.1
-- Adiciona campos de confirmação de email à tabela members.
-- Executar no Supabase SQL Editor em bancos existentes.

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed         BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_confirm_token     TEXT        UNIQUE,
    ADD COLUMN IF NOT EXISTS email_confirm_expires_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_members_confirm_token
    ON members (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;
