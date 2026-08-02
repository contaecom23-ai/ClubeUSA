-- Migration 001 — Fase 0.1: perfis de usuário
-- Execute no SQL Editor do Supabase (Dashboard > SQL Editor > New query)
-- REVERSÃO: ver seção DROP ao final (mantenha comentado em produção)

-- ============================================================
-- TABELA: profiles
-- Dados de perfil além do que o Supabase Auth já armazena.
-- id = auth.users.id (1:1, cascade delete)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name  TEXT        NOT NULL CHECK (length(trim(first_name)) > 0),
    last_name   TEXT        NOT NULL CHECK (length(trim(last_name)) > 0),
    zip_code    TEXT        NOT NULL CHECK (zip_code ~ '^\d{5}(-\d{4})?$'),
    phone       TEXT        CHECK (phone IS NULL OR phone ~ '^\+?[\d\s\-().]{7,20}$'),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- RLS (Row Level Security)
-- O backend usa service_role (ignora RLS), mas configuramos RLS
-- como defesa em profundidade para o caso de acesso direto.
-- ============================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Usuário autenticado lê apenas o próprio perfil
CREATE POLICY "profiles_select_own"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Usuário autenticado atualiza apenas o próprio perfil
CREATE POLICY "profiles_update_own"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id);

-- INSERT via trigger (SECURITY DEFINER) — sem política pública de INSERT
-- O service_role do backend também bypass RLS

-- ============================================================
-- TRIGGER: auto-updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- TRIGGER: criar perfil ao registrar novo usuário
-- Dispara no INSERT em auth.users (quando sign_up é chamado).
-- Dados extras vêm do campo raw_user_meta_data (user_metadata na API).
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    INSERT INTO public.profiles (id, first_name, last_name, zip_code, phone)
    VALUES (
        NEW.id,
        trim(COALESCE(NEW.raw_user_meta_data->>'first_name', '')),
        trim(COALESCE(NEW.raw_user_meta_data->>'last_name', '')),
        trim(COALESCE(NEW.raw_user_meta_data->>'zip_code', '00000')),
        NULLIF(trim(COALESCE(NEW.raw_user_meta_data->>'phone', '')), '')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- ROLLBACK (mantenha comentado em produção; descomente para reverter)
-- ============================================================
-- DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
-- DROP TRIGGER IF EXISTS profiles_set_updated_at ON public.profiles;
-- DROP FUNCTION IF EXISTS public.handle_new_user();
-- DROP FUNCTION IF EXISTS public.set_updated_at();
-- DROP TABLE IF EXISTS public.profiles;
