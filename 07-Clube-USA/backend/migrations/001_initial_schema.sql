-- =============================================================================
-- Migração 001 — Schema inicial Clube USA
-- Aplicar em: Supabase Dashboard > SQL Editor
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabela profiles
-- Estende auth.users (gerenciado pelo Supabase Auth).
-- Toda leitura/escrita só ocorre via FastAPI com service_role key.
-- RLS habilitado mas sem policy permissiva — acesso só server-side.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT        NOT NULL CHECK (length(trim(full_name)) >= 2),
    city        TEXT,
    state       CHAR(2),    -- código de 2 letras do estado americano
    phone       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para buscas futuras por estado (Fase 1.2)
CREATE INDEX IF NOT EXISTS profiles_state_idx ON public.profiles(state);

-- RLS ativo — bloqueia acesso anônimo direto ao banco.
-- Todo acesso legítimo vem da API com service_role (bypassa RLS).
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Sem policy permissiva: qualquer acesso via anon key ou user JWT direto
-- ao banco é bloqueado. Isso é intencional.

-- -----------------------------------------------------------------------------
-- Trigger: cria perfil automaticamente ao cadastrar usuário
-- Lê full_name de raw_user_meta_data (passado no sign_up da API)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Usuário')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

-- Garante idempotência ao re-aplicar a migração
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
