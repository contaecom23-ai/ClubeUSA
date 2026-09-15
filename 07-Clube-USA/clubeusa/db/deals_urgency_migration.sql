-- Fase 1.1 — Deal urgency: adds expires_at to track deal expiration
-- Non-destructive: nullable column, existing rows unaffected (NULL = no expiry)
-- Apply in Supabase SQL editor or via psql.

ALTER TABLE deals ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

-- Partial index: only index rows that actually have an expiry date
CREATE INDEX IF NOT EXISTS idx_deals_expires
    ON deals (expires_at)
    WHERE expires_at IS NOT NULL;
