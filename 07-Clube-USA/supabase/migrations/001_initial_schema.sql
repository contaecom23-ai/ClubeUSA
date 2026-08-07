-- Clube USA — Initial Schema (Fase 0.1)
-- Applies to a Supabase (Postgres 15+) project.
-- All access goes through service_role key (server-side only).
-- RLS is enabled but bypassed by service_role; keeps tables locked if anon key leaks.

-- ── Users ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                 TEXT        NOT NULL UNIQUE,
    password_hash         TEXT        NOT NULL,
    full_name             TEXT        NOT NULL,
    phone                 TEXT,
    zip_code              TEXT,
    state                 TEXT,
    city                  TEXT,
    bio                   TEXT,
    email_confirmed       BOOLEAN     NOT NULL DEFAULT FALSE,
    email_confirmed_at    TIMESTAMPTZ,
    force_password_change BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active             BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Deny everything for anon/authenticated roles; service_role bypasses RLS.
CREATE POLICY "deny_all_users" ON users AS RESTRICTIVE
    FOR ALL TO anon, authenticated USING (FALSE);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Email confirmations ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_confirmations (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT        NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE email_confirmations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "deny_all_email_confirmations" ON email_confirmations AS RESTRICTIVE
    FOR ALL TO anon, authenticated USING (FALSE);

CREATE INDEX IF NOT EXISTS idx_email_confirmations_token   ON email_confirmations (token);
CREATE INDEX IF NOT EXISTS idx_email_confirmations_user_id ON email_confirmations (user_id);
