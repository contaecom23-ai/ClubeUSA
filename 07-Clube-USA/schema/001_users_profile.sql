-- ============================================================
-- Migração 001 — Perfil de usuário (Fase 0.1)
-- Executar no SQL Editor do Supabase (projeto > SQL Editor)
-- ============================================================

-- Tabela de perfil mínimo vinculada ao auth.users do Supabase.
-- user_id FK -> auth.users(id) ON DELETE CASCADE: garante que perfis
-- não ficam órfãos se o usuário for removido do Auth (LGPD, ban, etc.).
-- email cached aqui para evitar chamada admin a cada /me; atualizar
--   se o usuário mudar email (feature futura — Fase 3+).
CREATE TABLE IF NOT EXISTS public.users_profile (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name  TEXT        NOT NULL CHECK (length(trim(full_name)) >= 2 AND length(full_name) <= 100),
    email      TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice para busca por user_id (acesso primário)
CREATE INDEX IF NOT EXISTS idx_users_profile_user_id ON public.users_profile(user_id);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_profile_updated_at ON public.users_profile;
CREATE TRIGGER trg_users_profile_updated_at
    BEFORE UPDATE ON public.users_profile
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ── Row Level Security ─────────────────────────────────────────────────────
-- Habilitado desde o início; acesso via service_role (backend) bypassa RLS.
-- Políticas de usuário final serão adicionadas quando o frontend acessar
-- o Supabase diretamente (não previsto para Fases 0-2).

ALTER TABLE public.users_profile ENABLE ROW LEVEL SECURITY;

-- Usuário autenticado pode ler apenas seu próprio perfil
CREATE POLICY "Usuário lê próprio perfil"
    ON public.users_profile FOR SELECT
    USING (auth.uid() = user_id);

-- Usuário autenticado pode atualizar apenas seu próprio perfil
CREATE POLICY "Usuário atualiza próprio perfil"
    ON public.users_profile FOR UPDATE
    USING (auth.uid() = user_id);

-- INSERT é feito exclusivamente pelo backend (service_role), nunca pelo cliente
-- Nenhuma política de INSERT para usuários anônimos/autenticados.

-- ── Comentários ────────────────────────────────────────────────────────────
COMMENT ON TABLE  public.users_profile           IS 'Perfil mínimo de usuário — Fase 0.1';
COMMENT ON COLUMN public.users_profile.user_id   IS 'FK para auth.users(id) ON DELETE CASCADE — vem sempre do JWT validado';
COMMENT ON COLUMN public.users_profile.email     IS 'Cache do email; sincronizar se usuário trocar email (Fase 3+)';
