-- Clube USA — Initial Schema (Phase 0.1)
-- Run this in your Supabase SQL Editor or against any PostgreSQL instance.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                     TEXT NOT NULL UNIQUE,
    password_hash             TEXT NOT NULL,
    full_name                 TEXT NOT NULL,
    email_confirmed           BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token       TEXT,
    email_confirm_expires_at  TIMESTAMPTZ,
    referral_code             TEXT UNIQUE NOT NULL DEFAULT substr(md5(random()::text), 1, 8),
    referred_by_user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active                 BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email           ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_referral_code   ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by     ON users(referred_by_user_id);
CREATE INDEX IF NOT EXISTS idx_users_confirm_token   ON users(email_confirm_token) WHERE email_confirm_token IS NOT NULL;

-- ============================================================
-- PROFILES (extended user data — separated to allow GDPR wipe)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    user_id     UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    us_state    TEXT,
    us_city     TEXT,
    whatsapp    TEXT,
    bio         TEXT CHECK (char_length(bio) <= 500),
    avatar_url  TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-create an empty profile row when a user is inserted
CREATE OR REPLACE FUNCTION fn_create_profile_for_new_user()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO profiles (user_id) VALUES (NEW.id) ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_create_profile ON users;
CREATE TRIGGER trg_create_profile
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION fn_create_profile_for_new_user();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- ============================================================
-- RATE LIMIT TOKENS (simple, in-DB; replace with Redis at 10k+)
-- ============================================================
CREATE TABLE IF NOT EXISTS rate_limit_log (
    id         BIGSERIAL PRIMARY KEY,
    ip         TEXT NOT NULL,
    endpoint   TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rl_ip_endpoint_time ON rate_limit_log(ip, endpoint, created_at);

-- Purge old entries automatically (keep only last 10 minutes)
CREATE OR REPLACE FUNCTION fn_purge_rate_limit_log()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM rate_limit_log WHERE created_at < NOW() - INTERVAL '10 minutes';
END;
$$;

-- ============================================================
-- ROW LEVEL SECURITY (enable once all access is server-side via service_role)
-- Uncomment when you confirm the backend ONLY uses service_role key.
-- ============================================================
-- ALTER TABLE users    ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "users_own_row"    ON users    FOR ALL USING (auth.uid() = id);
-- CREATE POLICY "profiles_own_row" ON profiles FOR ALL USING (auth.uid() = user_id);
