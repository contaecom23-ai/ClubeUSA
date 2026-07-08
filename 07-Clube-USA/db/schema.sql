-- =============================================================
-- Clube USA — Schema v0.1
-- Fonte de verdade. Toda mudança no banco começa aqui.
-- Execute no Supabase SQL Editor (Settings > SQL Editor).
-- =============================================================

-- ─── PROFILES ────────────────────────────────────────────────
-- Vinculado a auth.users (gerenciado pelo Supabase Auth).
-- id = auth.users.id; email fica em auth.users, não duplicamos.
CREATE TABLE IF NOT EXISTS public.profiles (
  id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name  TEXT,
  last_name   TEXT,
  phone       TEXT,
  zip_code    TEXT,
  city        TEXT,
  state       CHAR(2),   -- código 2 letras do estado dos EUA
  country     TEXT        NOT NULL DEFAULT 'US',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para busca por ZIP (preparação para Fase 1.2)
CREATE INDEX IF NOT EXISTS idx_profiles_zip_code ON public.profiles(zip_code);

-- ─── RLS ─────────────────────────────────────────────────────
-- Habilitado desde o início. A API usa service_role (bypassa RLS).
-- Políticas abaixo são para quando clientes acessarem diretamente.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own"  ON public.profiles FOR SELECT  USING (auth.uid() = id);
CREATE POLICY "users_update_own"  ON public.profiles FOR UPDATE  USING (auth.uid() = id);

-- ─── FUNÇÃO: auto-atualizar updated_at ───────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ─── FUNÇÃO: criar perfil ao cadastrar usuário ───────────────
-- SECURITY DEFINER: roda como o dono da função (postgres)
-- para ter permissão de inserir em public.profiles.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO public.profiles (id)
  VALUES (NEW.id)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_on_auth_user_created ON auth.users;
CREATE TRIGGER trg_on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
