-- ============================================================
--  Phase 0.4 migration — anti-fraude + cadastro válido
--  Adiciona rastreamento de IP de registro para detecção
--  de cadastros em massa fraudulentos.
--  Não destrutivo: apenas ADD COLUMN IF NOT EXISTS.
-- ============================================================

ALTER TABLE members
  ADD COLUMN IF NOT EXISTS registration_ip_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_members_reg_ip
  ON members (registration_ip_hash)
  WHERE registration_ip_hash IS NOT NULL;

-- Comentário operacional:
-- 'cadastro válido' = registro existente + total_clicks >= 1
-- Não precisa de coluna armazenada (calculado em runtime).
-- registration_ip_hash é usado para detecção de fraude:
--   SELECT COUNT(*) FROM members WHERE registration_ip_hash = $1
--   AND created_at >= NOW() - INTERVAL '24 hours'
-- Se COUNT >= 3, rejeitar novo cadastro.
