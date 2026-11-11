-- ============================================================
--  analytics_migration.sql — Clube USA
--  Fase 0.3: Analytics básico
--
--  Cria RPCs (funções SQL) para agregações eficientes.
--  As funções rodam no banco e retornam apenas totais,
--  não carregando linhas individuais no servidor.
--  Executa UMA vez no Supabase SQL Editor.
-- ============================================================

-- Diário de cadastros: quantos membros por dia nos últimos N dias
CREATE OR REPLACE FUNCTION get_daily_registrations(p_days_back INT DEFAULT 30)
RETURNS TABLE(reg_date DATE, cnt BIGINT)
LANGUAGE SQL SECURITY DEFINER AS $$
  SELECT
    created_at::DATE AS reg_date,
    COUNT(*)         AS cnt
  FROM members
  WHERE deleted_at IS NULL
    AND created_at >= (NOW() - (p_days_back || ' days')::INTERVAL)
  GROUP BY reg_date
  ORDER BY reg_date;
$$;

-- Funil de conversão: registros → email verificado → clique → VIP
CREATE OR REPLACE FUNCTION get_conversion_funnel()
RETURNS TABLE(stage TEXT, cnt BIGINT)
LANGUAGE SQL SECURITY DEFINER AS $$
  SELECT 'registered'::TEXT AS stage,
         COUNT(*)           AS cnt
  FROM members WHERE deleted_at IS NULL
  UNION ALL
  SELECT 'email_verified',
         COUNT(*) FROM members WHERE email_verified = TRUE AND deleted_at IS NULL
  UNION ALL
  SELECT 'had_click',
         COUNT(DISTINCT member_id) FROM clicks
  UNION ALL
  SELECT 'referred',
         COUNT(*) FROM members WHERE referred_by IS NOT NULL AND deleted_at IS NULL
  UNION ALL
  SELECT 'vip',
         COUNT(*) FROM members WHERE plan = 'vip' AND deleted_at IS NULL;
$$;
