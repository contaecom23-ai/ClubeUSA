-- Fase 0.1 — Perfil mínimo do usuário Clube USA
-- Usuários gerenciados pelo Supabase Auth (auth.users)
-- Esta tabela estende auth.users com dados de perfil da plataforma

CREATE TABLE IF NOT EXISTS public.profiles (
  id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name   TEXT        NOT NULL CHECK (char_length(full_name) >= 2 AND char_length(full_name) <= 120),
  phone       TEXT        CHECK (phone IS NULL OR phone ~ '^\+?[0-9\s\-\(\)]{7,20}$'),
  zip_code    TEXT        CHECK (zip_code IS NULL OR zip_code ~ '^[0-9]{5}(-[0-9]{4})?$'),
  state       TEXT        CHECK (state IS NULL OR char_length(state) = 2),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS: apenas o próprio usuário acessa/edita seu perfil via client
-- (acesso do backend usa service_role, que bypassa RLS com segurança)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_update_own" ON public.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Trigger: mantém updated_at correto em cada UPDATE
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Trigger: cria linha em profiles logo que o usuário é criado no Auth
-- O full_name vem dos metadados que o frontend envia no signUp
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (
    NEW.id,
    COALESCE(NULLIF(TRIM(NEW.raw_user_meta_data->>'full_name'), ''), 'Usuário')
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

-- Ativado quando Supabase Auth confirma email e cria o usuário
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
