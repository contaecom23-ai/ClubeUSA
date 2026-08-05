-- Clube USA — Schema inicial
-- Fase 0.1: Cadastro + perfil mínimo + email confirmado
-- Rodar no Supabase SQL Editor ou via psql contra o banco Supabase (service_role).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email                           VARCHAR(255) UNIQUE NOT NULL,
    password_hash                   VARCHAR(255) NOT NULL,
    first_name                      VARCHAR(100) NOT NULL,
    last_name                       VARCHAR(100) NOT NULL,
    phone                           VARCHAR(20),
    zip_code                        VARCHAR(10),
    city                            VARCHAR(100),
    state                           VARCHAR(50),
    email_confirmed                 BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token             VARCHAR(255),
    email_confirm_token_expires_at  TIMESTAMPTZ,
    is_active                       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON users (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS (endgame): habilitado mas server-side usa service_role que bypassa.
-- Quando o frontend fizer chamadas diretas ao Supabase, ativar as policies abaixo.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy placeholder: usuário só vê o próprio registro.
-- Ativar quando o frontend tiver acesso direto (não hoje).
-- CREATE POLICY users_self ON users
--   USING (auth.uid() = id)
--   WITH CHECK (auth.uid() = id);
