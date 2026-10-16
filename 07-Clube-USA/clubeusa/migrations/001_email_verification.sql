-- ============================================================
--  Migration 001: Adiciona campos de verificacao de email
--  Aplicar no Supabase SQL Editor antes do deploy.
-- ============================================================

ALTER TABLE members
  ADD COLUMN IF NOT EXISTS email_verified         BOOLEAN     NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS email_verification_token TEXT,
  ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMPTZ;

-- Indice para lookup rapido pelo token (token e buscado em /auth/email/verify)
CREATE INDEX IF NOT EXISTS idx_members_email_verification_token
  ON members (email_verification_token)
  WHERE email_verification_token IS NOT NULL;

-- Comentarios para documentacao
COMMENT ON COLUMN members.email_verified IS 'True quando o membro confirmou o email clicando no link enviado.';
COMMENT ON COLUMN members.email_verification_token IS 'Token hex-96 para confirmar email. Nulo apos confirmacao ou expiracao.';
COMMENT ON COLUMN members.email_verification_expires_at IS 'Expiracao do token. TTL de 24h a partir do envio.';
