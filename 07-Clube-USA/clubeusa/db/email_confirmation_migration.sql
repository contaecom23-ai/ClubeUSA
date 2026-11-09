-- ============================================================
--  email_confirmation_migration.sql — Clube USA  Fase 0.1
--
--  Adiciona suporte a confirmacao de email nos membros:
--    - email_confirmed_at: timestamp de quando o email foi confirmado
--    - email_confirm_token: token UUID para o link de confirmacao
--    - email_confirm_expires_at: validade do token (24h)
--
--  COMO RODAR:
--    No Supabase SQL Editor, execute este script inteiro.
--    E idempotente: usa IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.
-- ============================================================

-- Adiciona colunas novas em members (nao destrutivo — sem DROP)
ALTER TABLE members
    ADD COLUMN IF NOT EXISTS email_confirmed_at     TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS email_confirm_token    TEXT,
    ADD COLUMN IF NOT EXISTS email_confirm_expires  TIMESTAMPTZ;

-- Index para lookup rapido do token na hora da confirmacao
CREATE INDEX IF NOT EXISTS idx_members_confirm_token
    ON members (email_confirm_token)
    WHERE email_confirm_token IS NOT NULL;

-- ============================================================
--  Funcao RPC — confirmar email via token
--  Chamada pelo backend apos validar o token.
--  Limpa o token apos uso (one-time-use).
-- ============================================================
CREATE OR REPLACE FUNCTION confirm_member_email(p_token TEXT)
RETURNS TABLE (member_id UUID, email_enc TEXT, success BOOLEAN) AS $$
DECLARE
    v_member RECORD;
BEGIN
    SELECT id, email_enc, email_confirmed_at, email_confirm_expires
    INTO v_member
    FROM members
    WHERE email_confirm_token = p_token
      AND deleted_at IS NULL
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::UUID, NULL::TEXT, FALSE;
        RETURN;
    END IF;

    IF v_member.email_confirmed_at IS NOT NULL THEN
        -- Ja confirmado — OK idempotente
        RETURN QUERY SELECT v_member.id, v_member.email_enc, TRUE;
        RETURN;
    END IF;

    IF v_member.email_confirm_expires < NOW() THEN
        RETURN QUERY SELECT NULL::UUID, NULL::TEXT, FALSE;
        RETURN;
    END IF;

    -- Confirma e limpa o token
    UPDATE members
    SET email_confirmed_at    = NOW(),
        email_confirm_token   = NULL,
        email_confirm_expires = NULL
    WHERE id = v_member.id;

    RETURN QUERY SELECT v_member.id, v_member.email_enc, TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
