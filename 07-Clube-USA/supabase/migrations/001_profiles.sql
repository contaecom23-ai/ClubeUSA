-- Fase 0.1: Tabela de perfis de usuários
-- Vinculada a auth.users do Supabase (ON DELETE CASCADE para limpeza automática).
-- user_id vem sempre do servidor (token JWT), nunca do cliente.

CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name  TEXT        NOT NULL,
    last_name   TEXT        NOT NULL DEFAULT '',
    phone       TEXT        NOT NULL DEFAULT '',
    zip_code    TEXT        NOT NULL DEFAULT '',
    state       TEXT        NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS profiles_zip_code_idx ON public.profiles(zip_code);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS habilitado como endgame; acesso server-side via service_role no momento.
-- Policies serão adicionadas quando o frontend conectar diretamente ao Supabase.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
