-- analytics_migration.sql — Fase 0.3
-- Rodar uma vez no Supabase SQL Editor.
-- Melhora performance das queries de analytics sem bloquear leituras.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_action_created
    ON audit_logs (action, created_at DESC);
