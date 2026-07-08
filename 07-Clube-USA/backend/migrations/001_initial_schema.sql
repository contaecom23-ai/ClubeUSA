-- ============================================================
-- Migration 001 — Clube USA initial schema
-- Run once in the Supabase SQL Editor for your project.
-- ============================================================

-- ---------------------------------------------------------------
-- profiles — one-to-one with auth.users
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT        NOT NULL
                CHECK (char_length(full_name) BETWEEN 2 AND 100),
    zip_code    TEXT
                CHECK (zip_code ~ '^\d{5}(-\d{4})?$'),
    state_us    CHAR(2)
                CHECK (state_us IN (
                    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
                    'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
                    'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
                    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
                    'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'
                )),
    city        TEXT,
    whatsapp    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT  profiles_pkey PRIMARY KEY (id)
);

-- Auto-update updated_at on every row change
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------
-- Row Level Security (defence-in-depth; backend uses service_role
-- which bypasses RLS, but this protects against accidental anon key
-- exposure or future client-side use)
-- ---------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Users can only read/update their own row
CREATE POLICY "profiles: owner select"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles: owner update"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- No public insert via anon key; inserts only via service_role from the API
CREATE POLICY "profiles: no anon insert"
    ON public.profiles FOR INSERT
    WITH CHECK (false);

-- ---------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------
CREATE INDEX IF NOT EXISTS profiles_zip_code_idx ON public.profiles (zip_code);
CREATE INDEX IF NOT EXISTS profiles_state_us_idx  ON public.profiles (state_us);
