-- promotions_migration.sql — Fase 1.1 (Promoções/Achados)
-- Deals submetidos pela comunidade. Separada da tabela 'deals' (auto-scraping Amazon).
-- Rodar no Supabase SQL Editor ANTES de subir o código.

-- Tabela principal
CREATE TABLE IF NOT EXISTS promotions (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submitted_by UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    title        TEXT NOT NULL CHECK (char_length(title) BETWEEN 5 AND 200),
    description  TEXT CHECK (char_length(description) <= 1000),
    store_name   TEXT NOT NULL CHECK (char_length(store_name) BETWEEN 2 AND 100),
    url          TEXT CHECK (char_length(url) <= 500),
    price_now    NUMERIC(10,2) CHECK (price_now > 0),
    price_was    NUMERIC(10,2) CHECK (price_was > 0),
    zip_code     VARCHAR(10),
    state        VARCHAR(50),
    category     VARCHAR(50) NOT NULL DEFAULT 'other'
                 CHECK (category IN ('grocery','gas','restaurant','services','electronics','fashion','other')),
    expires_at   TIMESTAMPTZ,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','approved','rejected')),
    upvotes      INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promotions_status_time ON promotions (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_promotions_submitter   ON promotions (submitted_by);
CREATE INDEX IF NOT EXISTS idx_promotions_zip         ON promotions (zip_code) WHERE zip_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_promotions_category    ON promotions (category, status);
CREATE INDEX IF NOT EXISTS idx_promotions_upvotes     ON promotions (upvotes DESC) WHERE status = 'approved';

-- Anti-duplo-voto: PRIMARY KEY (promotion_id, member_id) garante unicidade no banco
CREATE TABLE IF NOT EXISTS promotion_upvotes (
    promotion_id UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    member_id    UUID NOT NULL REFERENCES members(id)    ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (promotion_id, member_id)
);

CREATE INDEX IF NOT EXISTS idx_pup_member ON promotion_upvotes (member_id);

-- Trigger updated_at (reusa função existente do schema principal)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_promotions_updated'
  ) THEN
    CREATE TRIGGER trg_promotions_updated
        BEFORE UPDATE ON promotions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
  END IF;
END $$;

-- RLS
ALTER TABLE promotions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotion_upvotes ENABLE ROW LEVEL SECURITY;

-- Membros veem aprovadas + as próprias (server usa service_role, RLS é endgame)
CREATE POLICY IF NOT EXISTS promotions_read ON promotions
    FOR SELECT USING (status = 'approved' OR submitted_by = auth.uid());

CREATE POLICY IF NOT EXISTS promotions_insert ON promotions
    FOR INSERT WITH CHECK (submitted_by = auth.uid());

CREATE POLICY IF NOT EXISTS promotions_delete_own_pending ON promotions
    FOR DELETE USING (submitted_by = auth.uid() AND status = 'pending');

CREATE POLICY IF NOT EXISTS upvotes_read_own ON promotion_upvotes
    FOR SELECT USING (member_id = auth.uid());

CREATE POLICY IF NOT EXISTS upvotes_insert_own ON promotion_upvotes
    FOR INSERT WITH CHECK (member_id = auth.uid());
