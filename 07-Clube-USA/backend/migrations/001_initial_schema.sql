-- ============================================================
-- Clube USA — Migração 001: Schema inicial (Fase 0.1)
-- Executar no SQL Editor do Supabase (service_role)
-- ============================================================

-- Extensão para UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Tabela de usuários ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   TEXT UNIQUE NOT NULL,
    password_hash           TEXT NOT NULL,
    full_name               TEXT NOT NULL,
    email_confirmed         BOOLEAN NOT NULL DEFAULT FALSE,
    email_confirm_token     TEXT,
    email_confirm_sent_at   TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Tabela de perfis (1:1 com users) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    city        TEXT,
    state       TEXT CHECK (state IS NULL OR length(state) = 2),
    zip_code    TEXT CHECK (zip_code IS NULL OR zip_code ~ '^\d{5}(-\d{4})?$'),
    bio         TEXT CHECK (bio IS NULL OR length(bio) <= 500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Índices ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_email_confirm_token ON public.users(email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);

-- ── Trigger: updated_at automático ───────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ── RLS: habilitado mas permissivo via service_role ───────────────────────────
-- Todo acesso é server-side (service_role bypassa RLS).
-- Quando tivermos Edge Functions ou client-side, adicionaremos políticas.
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Bloqueia acesso via anon key (nunca exposta) — service_role continua livre
CREATE POLICY "deny_anon_users"    ON public.users    FOR ALL TO anon USING (false);
CREATE POLICY "deny_anon_profiles" ON public.profiles FOR ALL TO anon USING (false);

-- ============================================================
-- Para reverter: DROP TABLE public.profiles; DROP TABLE public.users;
-- ============================================================
