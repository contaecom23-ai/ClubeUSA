-- Clube USA — Migração inicial
-- Fase 0.1: Cadastro + perfil mínimo + email confirmado
-- Compatível com Supabase (PostgreSQL 15+)

-- Extensão para UUID v4
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,

    -- Perfil mínimo
    full_name       VARCHAR(255),
    zip_code        VARCHAR(10),
    us_state        VARCHAR(50),
    bio             TEXT,

    -- Confirmação de e-mail
    email_confirmed         BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token     VARCHAR(255),
    email_confirm_expires_at TIMESTAMP WITH TIME ZONE,

    -- Reset de senha
    password_reset_token        VARCHAR(255),
    password_reset_expires_at   TIMESTAMP WITH TIME ZONE,

    -- Controle
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Índices de lookup frequente
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_password_reset_token
    ON users(password_reset_token)
    WHERE password_reset_token IS NOT NULL;

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
