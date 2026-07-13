-- Clube USA — Schema inicial (Fase 0.1)
-- Execute no Supabase SQL Editor ou via psql com service_role.
-- Supabase RLS fica para fase posterior; acesso via service_role server-side até lá.

-- Extensão necessária para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Tabela principal de usuários
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    phone               VARCHAR(50),
    zip_code            VARCHAR(10),
    city                VARCHAR(100),
    state               CHAR(2),
    country             VARCHAR(50) DEFAULT 'US',
    email_confirmed     BOOLEAN DEFAULT FALSE,
    email_confirmed_at  TIMESTAMPTZ,
    referral_code       VARCHAR(20) UNIQUE NOT NULL,
    referred_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    last_login_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);

-- ---------------------------------------------------------------------------
-- Tokens de confirmação de email (uso único, expiram em 24h)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS email_confirmations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_confirmations_token   ON email_confirmations(token);
CREATE INDEX IF NOT EXISTS idx_email_confirmations_user_id ON email_confirmations(user_id);

-- ---------------------------------------------------------------------------
-- Refresh tokens (hash armazenado, nunca o token bruto)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id    ON refresh_tokens(user_id);

-- ---------------------------------------------------------------------------
-- Log de tentativas de login (rate-limit / anti-brute-force)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS login_attempts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address   VARCHAR(45) NOT NULL,
    email        VARCHAR(255),
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    success      BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_ip    ON login_attempts(ip_address, attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email, attempted_at);

-- Limpa tentativas antigas automaticamente (opcional — cron no Supabase ou pg_cron)
-- DELETE FROM login_attempts WHERE attempted_at < NOW() - INTERVAL '7 days';

-- ---------------------------------------------------------------------------
-- Trigger para manter updated_at atualizado
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_users_updated_at'
    ) THEN
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;
