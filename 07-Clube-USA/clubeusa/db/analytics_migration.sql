-- ============================================================
--  Migration: Analytics — tabela de eventos
--  Idempotente (pode re-executar sem erro)
--  Aplicar no Supabase: Dashboard → SQL Editor
-- ============================================================

-- Tabela de eventos para funil de analytics e Phase 0.4 (cadastro válido)
CREATE TABLE IF NOT EXISTS events (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID        REFERENCES members(id) ON DELETE CASCADE,
    event_type  TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_member ON events(member_id);
CREATE INDEX IF NOT EXISTS idx_events_type   ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_time   ON events(created_at);

-- Evento: membro cadastrado
COMMENT ON COLUMN events.event_type IS
  'Valores: member.registered | email.confirmed | deal.clicked | referral.used | profile.updated';
