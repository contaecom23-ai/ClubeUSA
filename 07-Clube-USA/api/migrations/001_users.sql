-- Migration 001: users table
-- Run this in Supabase SQL editor (or via psql).
-- Using service_role for all server queries; RLS policies prepared for future activation.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.users (
    id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                    VARCHAR(255) UNIQUE NOT NULL,
    password_hash            VARCHAR(255) NOT NULL,
    full_name                VARCHAR(100) NOT NULL,
    email_confirmed          BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirm_token      UUID,
    email_confirm_expires_at TIMESTAMPTZ,

    -- Phase 0.2 columns (referral system) — defined now to avoid schema change later
    referral_code            VARCHAR(20)  UNIQUE,
    referred_by              UUID        REFERENCES public.users(id) ON DELETE SET NULL,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email
    ON public.users(email);

CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token
    ON public.users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_referral_code
    ON public.users(referral_code)
    WHERE referral_code IS NOT NULL;

-- Trigger: keep updated_at current
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();

-- RLS: enable now, but all real access goes via service_role (bypasses RLS).
-- Policies below protect anon/authenticated roles if enabled in the future.
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- No anon or authenticated Supabase roles should access user rows directly.
-- Service_role (server-side API) bypasses RLS automatically.
CREATE POLICY "deny_all_direct_access" ON public.users
    AS RESTRICTIVE
    FOR ALL
    TO anon, authenticated
    USING (false);
