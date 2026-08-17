-- Fase 0.2: Sistema de REFERRAL rastreável
-- Cada usuário ganha um slug único gerado no cadastro.
-- Cadastros que vieram de um referral registram o slug de origem.

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS referral_slug     TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS referred_by_slug  TEXT;

-- Índices para lookup rápido (GET /referrals/me conta por referred_by_slug)
CREATE INDEX IF NOT EXISTS profiles_referral_slug_idx
    ON public.profiles (referral_slug);

CREATE INDEX IF NOT EXISTS profiles_referred_by_slug_idx
    ON public.profiles (referred_by_slug);

-- Rastreamento leve de cliques no link de referral.
-- Não armazena IP para manter conformidade com privacidade.
-- clicked_at permite limitar window de analytics sem dado pessoal.
CREATE TABLE IF NOT EXISTS public.referral_clicks (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT        NOT NULL,
    clicked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS referral_clicks_slug_idx
    ON public.referral_clicks (slug);

ALTER TABLE public.referral_clicks ENABLE ROW LEVEL SECURITY;
