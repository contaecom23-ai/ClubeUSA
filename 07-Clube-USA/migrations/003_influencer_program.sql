-- ClubeUSA — Migração 003 — Programa de Influenciadores (Fase 1.3)
-- Executar no SQL Editor do Supabase após 001 e 002

-- =============================================================
-- TABELA: influencer_payouts
-- Registro de pagamentos feitos a influenciadores.
-- O pagamento em si é externo (PayPal/Venmo/Zelle); isto rastreia o histórico.
-- =============================================================
CREATE TABLE IF NOT EXISTS influencer_payouts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    valid_referrals  INTEGER NOT NULL,          -- contagem de referrals válidos no momento do pagamento
    amount_usd       NUMERIC(10,2) NOT NULL,    -- valor pago em dólares
    payment_method   TEXT NOT NULL,             -- paypal | venmo | zelle | check | other
    payment_ref      TEXT,                      -- id externo ou código de transação
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_influencer_payouts_user_id   ON influencer_payouts(user_id);
CREATE INDEX IF NOT EXISTS idx_influencer_payouts_created_at ON influencer_payouts(created_at DESC);

-- =============================================================
-- FUNÇÃO: get_influencer_leaderboard
-- Top N influenciadores por referrals válidos (email confirmado + localização).
-- Não retorna email/telefone — apenas dados públicos.
-- =============================================================
CREATE OR REPLACE FUNCTION get_influencer_leaderboard(p_limit INTEGER DEFAULT 20)
RETURNS TABLE (
    user_id         UUID,
    display_name    TEXT,
    city            TEXT,
    state           TEXT,
    valid_referrals BIGINT
) LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT
        u.id                         AS user_id,
        u.name                       AS display_name,
        u.city,
        u.state,
        COUNT(r.id)                  AS valid_referrals
    FROM users u
    INNER JOIN users r
        ON r.referred_by_user_id = u.id
        AND r.email_confirmed_at IS NOT NULL
        AND (r.zip_code IS NOT NULL OR r.city IS NOT NULL)
    WHERE u.referral_code IS NOT NULL
    GROUP BY u.id, u.name, u.city, u.state
    ORDER BY valid_referrals DESC, u.created_at ASC
    LIMIT p_limit;
$$;

-- =============================================================
-- FUNÇÃO: get_valid_referral_count
-- Contagem de referrals válidos de um usuário específico.
-- =============================================================
CREATE OR REPLACE FUNCTION get_valid_referral_count(p_user_id UUID)
RETURNS BIGINT LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT COUNT(*) FROM users
    WHERE referred_by_user_id = p_user_id
      AND email_confirmed_at IS NOT NULL
      AND (zip_code IS NOT NULL OR city IS NOT NULL);
$$;
