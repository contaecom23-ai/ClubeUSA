-- Migration: adiciona tabela otp_codes para OTPs persistentes
-- Executar em bancos existentes que nao rodaram o schema.sql completo

CREATE TABLE IF NOT EXISTS otp_codes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_hash  TEXT NOT NULL,
    otp         VARCHAR(6) NOT NULL,
    attempts    SMALLINT NOT NULL DEFAULT 0,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_otp_phone   ON otp_codes (phone_hash);
CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes (expires_at);
