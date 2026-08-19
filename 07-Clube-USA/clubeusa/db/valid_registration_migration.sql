-- ============================================================
--  valid_registration_migration.sql - Clube USA
--  Fase 0.4: cadastro valido verificavel + anti-fraude
--
--  DEPENDENCIA: email_confirmation_migration.sql (PR #54) deve
--  ser aplicada antes desta.
--
--  Como rodar: SQL Editor do Supabase ou psql como service_role.
-- ============================================================

-- Campo: email descartavel detectado no cadastro
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS is_disposable_email BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN members.is_disposable_email IS
    'TRUE se o dominio do email foi identificado como descartavel no momento do cadastro.';

-- Funcao: verifica se cadastro e valido (email confirmado + >=1 acao real)
-- "Acao real" = clique em deal OU indicacao confirmada.
-- Chamada pelo endpoint GET /api/v1/members/me/valid-status e pelo sistema
-- de influenciadores (Fase 1.3) para contar cadastros validos indicados.
CREATE OR REPLACE FUNCTION is_valid_registration(p_member_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT
        COALESCE(email_confirmed, FALSE) = TRUE
        AND is_disposable_email = FALSE
        AND (total_clicks >= 1 OR referral_count >= 1)
    FROM members
    WHERE id = p_member_id
      AND deleted_at IS NULL;
$$;

COMMENT ON FUNCTION is_valid_registration IS
    'Fase 0.4: TRUE se cadastro valido (email confirmado + nao-descartavel + >=1 acao real).';

-- View auxiliar: lista membros validos (para admin e influencer dashboard)
CREATE OR REPLACE VIEW valid_members AS
    SELECT id, referral_code, referred_by, total_clicks, referral_count, created_at
    FROM members
    WHERE COALESCE(email_confirmed, FALSE) = TRUE
      AND is_disposable_email = FALSE
      AND (total_clicks >= 1 OR referral_count >= 1)
      AND deleted_at IS NULL;

COMMENT ON VIEW valid_members IS
    'Fase 0.4: membros com cadastro valido (email confirmado + acao real).';
