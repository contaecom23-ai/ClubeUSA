-- Migration 001: profiles table
-- Aplique no Supabase Dashboard > SQL Editor
-- Pré-requisito: auth.users já existe (criado automaticamente pelo Supabase)

-- ── Tabela profiles ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT,
    state       CHAR(2),         -- Código de estado americano (ex: FL, TX)
    city        TEXT,
    zip_code    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Backend usa service_role (bypassa RLS), então estas políticas protegem
-- contra acesso direto ao banco e são o "endgame" para client-side queries.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Insert via backend (service_role) não precisa de política INSERT.
-- Usuários não inserem diretamente via client.

-- ── Auto-update updated_at ────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ── Índices ───────────────────────────────────────────────────────────────────
-- Índice por ZIP para suportar busca local (Fase 1.2)
CREATE INDEX IF NOT EXISTS idx_profiles_zip_code ON public.profiles (zip_code);
CREATE INDEX IF NOT EXISTS idx_profiles_state ON public.profiles (state);
