-- Clube USA — Schema inicial (Fase 0.1)
-- Aplicar no Supabase SQL Editor ou via psql.
-- Compatível com PostgreSQL 14+.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── USUÁRIOS ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                           TEXT        UNIQUE NOT NULL,
    password_hash                   TEXT        NOT NULL,
    full_name                       TEXT        NOT NULL,
    phone                           TEXT,
    zip_code                        TEXT,
    city                            TEXT,
    state                           TEXT,
    email_confirmed                 BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirmation_token        TEXT,
    email_confirmation_expires_at   TIMESTAMPTZ,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at                   TIMESTAMPTZ,
    is_active                       BOOLEAN     NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  users IS 'Usuários da plataforma Clube USA. Acesso via service_role no backend; nunca via anon key.';
COMMENT ON COLUMN users.email IS 'Armazenado em lowercase; UNIQUE garante sem duplicatas.';
COMMENT ON COLUMN users.email_confirmation_token IS 'secrets.token_urlsafe(32); NULL após confirmação.';

-- Índices de performance
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
    ON users (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- Atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trg_set_updated_at();

-- ─── ROW LEVEL SECURITY ───────────────────────────────────────────────────────
-- O backend usa service_role (bypassa RLS).
-- RLS está habilitado aqui para garantir que anon key nunca acesse dados.
-- Quando evoluirmos para Supabase Auth nativo, adicionaremos policies granulares.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Sem policies explícitas = nenhum acesso via anon/authenticated role.
-- service_role bypassa RLS por padrão no Supabase.
