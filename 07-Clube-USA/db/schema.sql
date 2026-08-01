-- Clube USA — Schema v0.1
-- Execute no Supabase SQL Editor (Dashboard > SQL Editor > New query)
-- Supabase já gerencia auth.users; este schema estende com perfil de aplicação.

-- ============================================================
-- PERFIS DE USUÁRIO
-- Cada registro é de propriedade exclusiva de um auth.users.id
-- ============================================================
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id          UUID         NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    full_name   TEXT         NOT NULL,
    city        TEXT,
    state       TEXT,                 -- sigla de 2 letras (ex: "FL", "TX")
    zip_code    TEXT,                 -- ZIP code americano
    bio         TEXT,
    phone       TEXT,
    language    TEXT         NOT NULL DEFAULT 'pt',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT user_profiles_pkey PRIMARY KEY (id),
    CONSTRAINT user_profiles_language_check CHECK (language IN ('pt', 'en', 'es'))
);

-- Índice para lookups por cidade/estado (busca por região, Fase 1.2)
CREATE INDEX IF NOT EXISTS idx_user_profiles_state_city ON public.user_profiles (state, city);

-- ============================================================
-- ROW LEVEL SECURITY — usuário vê e edita APENAS o próprio perfil
-- ============================================================
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Apenas o próprio usuário lê seu perfil
CREATE POLICY "profile_select_own" ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Apenas o próprio usuário atualiza seu perfil
CREATE POLICY "profile_update_own" ON public.user_profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- INSERT é feito pelo trigger abaixo com SECURITY DEFINER — sem política INSERT pública
-- (INSERT via trigger roda como superuser do banco, não precisa de policy)

-- ============================================================
-- TRIGGER: atualiza updated_at automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS user_profiles_set_updated_at ON public.user_profiles;
CREATE TRIGGER user_profiles_set_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ============================================================
-- TRIGGER: cria perfil automaticamente ao cadastrar novo usuário
-- full_name vem do metadata enviado pelo frontend no signUp()
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (id, full_name)
    VALUES (
        NEW.id,
        COALESCE(
            NULLIF(TRIM(NEW.raw_user_meta_data ->> 'full_name'), ''),
            'Usuário'
        )
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
