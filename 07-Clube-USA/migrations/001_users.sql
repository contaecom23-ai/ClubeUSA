-- Migration: 001_users
-- Phase 0.1: User auth + minimal profile
-- Run once against your Supabase project via the SQL editor.
-- Idempotent (uses IF NOT EXISTS).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users (core auth) ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.users (
    id                               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email                            TEXT         UNIQUE NOT NULL,
    password_hash                    TEXT         NOT NULL,
    email_confirmed                  BOOLEAN      NOT NULL DEFAULT FALSE,
    email_confirmation_token         TEXT,
    email_confirmation_expires_at    TIMESTAMPTZ,
    is_active                        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at                       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON public.users (email);

CREATE INDEX IF NOT EXISTS idx_users_confirmation_token
    ON public.users (email_confirmation_token)
    WHERE email_confirmation_token IS NOT NULL;

-- ── Profiles (minimal, expandable) ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.profiles (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID         UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    full_name     TEXT,
    zip_code      TEXT,
    phone         TEXT,
    bio           TEXT,
    avatar_url    TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id
    ON public.profiles (user_id);

-- ── updated_at trigger ───────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'users_updated_at') THEN
        CREATE TRIGGER users_updated_at
            BEFORE UPDATE ON public.users
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'profiles_updated_at') THEN
        CREATE TRIGGER profiles_updated_at
            BEFORE UPDATE ON public.profiles
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
    END IF;
END $$;

-- ── Row Level Security ───────────────────────────────────────────────────────
-- The API uses service_role (bypasses RLS). RLS here is a safety net for
-- any future client-side access and ensures the anon key has zero read access.

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Deny all by default (no permissive policies for anon/authenticated roles).
-- Client-side policies will be added in Phase 3+ when needed.
