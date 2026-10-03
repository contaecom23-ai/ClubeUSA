-- ============================================================
--  fase0_complementar_migration.sql — Clube USA
--  Idempotente: pode ser executado multiplas vezes sem erro
--  Parte do Fase 0.3 + 0.4
-- ============================================================

-- RPC para analytics de crescimento diario (Fase 0.3)
CREATE OR REPLACE FUNCTION get_daily_registrations(p_since TIMESTAMPTZ)
RETURNS TABLE(date TEXT, count BIGINT)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        DATE_TRUNC('day', created_at)::DATE::TEXT AS date,
        COUNT(*)                                   AS count
    FROM members
    WHERE created_at >= p_since
      AND deleted_at IS NULL
    GROUP BY 1
    ORDER BY 1;
$$;

-- Indice para anti-fraude por IP (Fase 0.4)
-- Permite contar cadastros recentes por IP em < 5ms
CREATE INDEX IF NOT EXISTS idx_audit_ip_created
    ON audit_logs (ip_hash, created_at DESC)
    WHERE action = 'member.created'
      AND ip_hash IS NOT NULL;
