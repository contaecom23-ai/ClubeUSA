-- ============================================================
--  referral_click_migration.sql — Clube USA
--  Fase 0.2: Rastreamento de cliques em links de referral
--
--  Executa UMA vez no Supabase SQL Editor.
-- ============================================================

-- Cliques em links /i/{code} — funil de conversao
-- Sem PII: ip e user_agent sempre hasheados
CREATE TABLE IF NOT EXISTS referral_clicks (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    referral_code    VARCHAR(12) NOT NULL,
    ip_hash          TEXT,
    ua_hash          TEXT,
    converted_member UUID        REFERENCES members(id) ON DELETE SET NULL,
    clicked_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refclicks_code
    ON referral_clicks (referral_code);

CREATE INDEX IF NOT EXISTS idx_refclicks_at
    ON referral_clicks (clicked_at DESC);

CREATE INDEX IF NOT EXISTS idx_refclicks_converted
    ON referral_clicks (converted_member)
    WHERE converted_member IS NOT NULL;
