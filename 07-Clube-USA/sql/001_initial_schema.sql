-- 001_initial_schema.sql
-- Clube USA — schema inicial: perfis de usuário
--
-- Como aplicar: cole no SQL Editor do painel Supabase e execute.
-- Pré-requisito: projeto Supabase criado com Auth habilitado.

-- Tabela de perfis (1:1 com auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT        NOT NULL CHECK (length(trim(full_name)) > 0),
    us_state    TEXT        CHECK (length(us_state) <= 100),
    city        TEXT        CHECK (length(city) <= 100),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice explícito (FK já cria um, mas deixa claro para futuras queries)
CREATE INDEX IF NOT EXISTS idx_profiles_id ON public.profiles(id);

-- Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Usuários autenticados lêem apenas o próprio perfil
CREATE POLICY "users_select_own_profile"
    ON public.profiles
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

-- Usuários autenticados atualizam apenas o próprio perfil
CREATE POLICY "users_update_own_profile"
    ON public.profiles
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- INSERT e DELETE são exclusivos do service_role (backend) — sem política pública.
-- O service_role bypassa RLS por design.

-- Trigger: atualiza updated_at automaticamente
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
