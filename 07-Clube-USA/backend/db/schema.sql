-- =============================================
-- Clube USA — Schema v0.1
-- FONTE DE VERDADE do banco de dados.
-- Aplicar no Supabase SQL Editor antes de rodar o backend.
-- =============================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- TABELA: profiles
-- Estende auth.users do Supabase Auth.
-- Cada linha pertence a um único usuário (id = auth.uid()).
-- =============================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id               UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name        TEXT        NOT NULL CHECK (char_length(full_name) BETWEEN 1 AND 100),
  city             TEXT        CHECK (char_length(city) <= 100),
  state_us         CHAR(2)     CHECK (state_us ~ '^[A-Z]{2}$'),
  phone            TEXT        CHECK (char_length(phone) <= 20),
  referral_code    TEXT        UNIQUE NOT NULL,
  referred_by_code TEXT        REFERENCES public.profiles(referral_code),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- RLS (Row Level Security)
-- Cada usuário acessa apenas seu próprio perfil.
-- Backend usa service_role (bypassa RLS), mas
-- SEMPRE filtra por user_id vindo do token JWT.
-- =============================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "profiles_update_own"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "profiles_insert_own"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- =============================================
-- FUNÇÃO: atualiza updated_at automaticamente
-- =============================================
CREATE OR REPLACE FUNCTION public.fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();

-- =============================================
-- FUNÇÃO: cria perfil ao registrar novo usuário
-- Dispara após INSERT em auth.users.
-- Captura full_name, city, state_us, referral_code
-- do raw_user_meta_data passado no signUp().
-- =============================================
CREATE OR REPLACE FUNCTION public.fn_create_profile_on_signup()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  code     TEXT;
  attempts INT := 0;
BEGIN
  -- Gera referral_code único: 8 chars hex lowercase
  LOOP
    code := lower(substring(encode(gen_random_bytes(6), 'hex'), 1, 8));
    EXIT WHEN NOT EXISTS (
      SELECT 1 FROM public.profiles WHERE referral_code = code
    );
    attempts := attempts + 1;
    IF attempts > 10 THEN
      RAISE EXCEPTION 'Falha ao gerar referral_code único após 10 tentativas';
    END IF;
  END LOOP;

  INSERT INTO public.profiles (
    id,
    full_name,
    city,
    state_us,
    referral_code,
    referred_by_code
  ) VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    NULLIF(NEW.raw_user_meta_data->>'city', ''),
    NULLIF(upper(NEW.raw_user_meta_data->>'state_us'), ''),
    code,
    NULLIF(NEW.raw_user_meta_data->>'referred_by_code', '')
  );

  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.fn_create_profile_on_signup();
