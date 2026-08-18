-- analytics_migration.sql — Fase 0.3
-- Índice composto em audit_logs para queries de analytics (GET /admin/analytics).
-- Rodar uma vez no Supabase SQL Editor.
-- CONCURRENTLY não bloqueia leitura/escrita durante a criação.

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_action_created
    ON audit_logs (action, created_at DESC);
