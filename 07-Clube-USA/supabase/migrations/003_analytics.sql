-- Fase 0.3: Analytics básico
-- Tabela genérica de eventos do sistema.
-- Eventos rastreados: 'user.registered' | 'user.logged_in' | 'referral.converted'
-- metadata: JSONB livre para contexto adicional por tipo de evento.
-- user_id: nullable — permite eventos pré-auth no futuro (ex: clique anônimo).

CREATE TABLE IF NOT EXISTS public.analytics_events (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type   TEXT        NOT NULL,
    user_id      UUID,
    metadata     JSONB       NOT NULL DEFAULT '{}',
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice composto para queries do painel admin (filtrar por tipo E janela temporal)
CREATE INDEX IF NOT EXISTS analytics_events_type_occurred_idx
    ON public.analytics_events (event_type, occurred_at DESC);

-- Índice para o breakdown diário (só occurred_at, sem filtro de tipo)
CREATE INDEX IF NOT EXISTS analytics_events_occurred_idx
    ON public.analytics_events (occurred_at DESC);

-- Índice para futura lookup por usuário (ex: histórico de ações)
CREATE INDEX IF NOT EXISTS analytics_events_user_id_idx
    ON public.analytics_events (user_id)
    WHERE user_id IS NOT NULL;

-- RLS habilitado; acesso exclusivo via service_role no backend.
-- Nenhuma policy definida = anon key não acessa estes dados.
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;
