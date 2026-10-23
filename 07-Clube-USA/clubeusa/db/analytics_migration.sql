-- ============================================================
--  analytics_migration.sql — Fase 0.3
--  Tabela de eventos de analytics (append-only, não exposta ao cliente)
--  Rodar APÓS schema.sql
-- ============================================================

-- Eventos de analytics — nunca deleta, apenas insere
CREATE TABLE IF NOT EXISTS analytics_events (
    id          BIGSERIAL PRIMARY KEY,
    member_id   UUID REFERENCES members(id) ON DELETE SET NULL,
    event_type  VARCHAR(50) NOT NULL,
    properties  JSONB NOT NULL DEFAULT '{}',
    ip_hash     TEXT,
    session_id  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_member ON analytics_events (member_id);
CREATE INDEX IF NOT EXISTS idx_analytics_type   ON analytics_events (event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_day    ON analytics_events (created_at DESC);

-- Eventos possíveis documentados (enforced apenas no código):
--   user.registered       — novo cadastro
--   user.login            — login via OTP verificado
--   user.email_verified   — email confirmado
--   deal.clicked          — clique em deal rastreado
--   deal.viewed           — listagem de deals consultada
--   product.tracked       — produto adicionado ao rastreador
--   referral.used         — cadastro via link de indicação
--   billing.subscribe_started — início de checkout Stripe
--   billing.vip_activated — VIP confirmado (webhook Stripe)

-- Proíbe UPDATE/DELETE para garantir integridade histórica
REVOKE UPDATE, DELETE, TRUNCATE ON analytics_events FROM PUBLIC;

-- ============================================================
--  Fase 0.4 — adiciona email_confirmed ao members
--  (sem dado existente: default FALSE, seguro de rodar)
-- ============================================================
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

-- ============================================================
--  Funções RPC para agregados (usadas pelo analytics_service)
-- ============================================================

-- Conta membros com ao menos 1 evento nos últimos 7 dias
CREATE OR REPLACE FUNCTION count_active_members_7d()
RETURNS BIGINT AS $$
    SELECT COUNT(DISTINCT member_id)
    FROM analytics_events
    WHERE created_at >= NOW() - INTERVAL '7 days'
      AND member_id IS NOT NULL;
$$ LANGUAGE sql STABLE;

-- Novos membros por dia nos últimos 14 dias
CREATE OR REPLACE FUNCTION members_per_day_14d()
RETURNS TABLE(day DATE, count BIGINT) AS $$
    SELECT
        DATE(created_at) AS day,
        COUNT(*)         AS count
    FROM members
    WHERE created_at >= NOW() - INTERVAL '14 days'
    GROUP BY DATE(created_at)
    ORDER BY day ASC;
$$ LANGUAGE sql STABLE;
