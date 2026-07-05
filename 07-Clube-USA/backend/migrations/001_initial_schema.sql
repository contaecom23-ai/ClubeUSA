-- =============================================================
-- Clube USA — Migration 001: Initial Schema
-- =============================================================
-- Run against your Supabase project with the service_role key.
-- All tables use server-side access only (service_role).
-- RLS is disabled intentionally until client-side queries are needed;
-- security is enforced at the API layer (see backend/app/).
-- =============================================================

-- Users: core auth record (email + password hash + verification status)
CREATE TABLE IF NOT EXISTS public.users (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT        UNIQUE NOT NULL,
    password_hash     TEXT        NOT NULL,
    is_email_verified BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Profiles: mutable user data (1-to-1 with users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    full_name  TEXT        CHECK (char_length(full_name) <= 100),
    phone      TEXT        CHECK (char_length(phone) <= 30),
    state      TEXT        CHECK (char_length(state) <= 50),
    city       TEXT        CHECK (char_length(city) <= 100),
    zip_code   TEXT        CHECK (zip_code ~ '^\d{5}(-\d{4})?$' OR zip_code IS NULL),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Email verification tokens (24h TTL, single-use)
CREATE TABLE IF NOT EXISTS public.email_verification_tokens (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token      TEXT        UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email
    ON public.users(email);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id
    ON public.profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_verification_tokens_token
    ON public.email_verification_tokens(token);

CREATE INDEX IF NOT EXISTS idx_verification_tokens_user_id
    ON public.email_verification_tokens(user_id);

-- Auto-update updated_at on row changes
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON public.users
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_profiles_updated_at') THEN
        CREATE TRIGGER update_profiles_updated_at
            BEFORE UPDATE ON public.profiles
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
    END IF;
END $$;

-- Security: revoke direct access from anon/authenticated roles.
-- All access goes through the API with the service_role key.
REVOKE ALL ON public.users FROM anon, authenticated;
REVOKE ALL ON public.profiles FROM anon, authenticated;
REVOKE ALL ON public.email_verification_tokens FROM anon, authenticated;

ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_verification_tokens DISABLE ROW LEVEL SECURITY;
