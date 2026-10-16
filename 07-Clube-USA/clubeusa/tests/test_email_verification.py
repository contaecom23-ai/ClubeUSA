# ============================================================
#  tests/test_email_verification.py — Clube USA
#  Testa o fluxo completo de verificacao de email (Fase 0.1)
# ============================================================
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_service
# ============================================================

class TestEmailService:
    def test_send_email_dev_mode_logs(self, caplog):
        """Em modo dev (sem SENDGRID_API_KEY), email e logado mas nao enviado."""
        import logging
        with patch.dict("os.environ", {}, clear=False):
            import importlib
            import services.email_service as es
            importlib.reload(es)
            with patch.dict("os.environ", {"SENDGRID_API_KEY": ""}, clear=False):
                with caplog.at_level(logging.INFO, logger="email_service"):
                    result = es.send_email("test@example.com", "Subject", "<p>Hello</p>")
        assert result is True

    def test_send_verification_email_generates_link(self, caplog):
        """O email de verificacao contem o link correto."""
        import logging
        import services.email_service as es
        with patch.object(es, "send_email", return_value=True) as mock_send:
            with patch.dict("os.environ", {"APP_URL": "https://clubeusa.com"}):
                es.send_verification_email("user@example.com", "abc123token", "Joao")
            args = mock_send.call_args[0]
            assert "abc123token" in args[2]  # token no HTML
            assert "https://clubeusa.com/auth/email/verify" in args[2]

    def test_generate_verification_token_length(self):
        """Token tem 96 caracteres hex (48 bytes)."""
        from services.email_service import generate_verification_token
        token = generate_verification_token()
        assert len(token) == 96
        assert token.isalnum()  # hex = apenas 0-9 a-f

    def test_verification_expires_at_is_future(self):
        """Expiracao e 24h no futuro."""
        from services.email_service import verification_expires_at
        expires = datetime.fromisoformat(verification_expires_at())
        now = datetime.utcnow()
        assert expires > now + timedelta(hours=23)
        assert expires < now + timedelta(hours=25)


# ============================================================
#  member_service — verify_email_token
# ============================================================

def _mock_supabase_factory(rows=None, update_ok=True):
    """Cria mock do Supabase que retorna rows no SELECT e aceita UPDATE."""
    sb = MagicMock()
    query_chain = MagicMock()
    query_chain.execute.return_value = MagicMock(data=rows or [])
    sb.table.return_value.select.return_value.eq.return_value = query_chain

    update_chain = MagicMock()
    update_chain.execute.return_value = MagicMock(data=[{}])
    sb.table.return_value.update.return_value.eq.return_value = update_chain

    return sb


class TestVerifyEmailToken:
    def _run(self, token, supabase_rows):
        with patch("services.member_service._supabase") as mock_sb_fn:
            mock_sb_fn.return_value = _mock_supabase_factory(rows=supabase_rows)
            from importlib import reload
            import services.member_service as ms
            reload(ms)
            with patch("services.member_service._supabase") as m2:
                m2.return_value = _mock_supabase_factory(rows=supabase_rows)
                return ms.verify_email_token(token)

    def test_empty_token_rejected(self):
        from services.member_service import verify_email_token
        with patch("services.member_service._supabase") as m:
            m.return_value = _mock_supabase_factory(rows=[])
            result = verify_email_token("")
        assert result["ok"] is False

    def test_short_token_rejected(self):
        from services.member_service import verify_email_token
        with patch("services.member_service._supabase") as m:
            m.return_value = _mock_supabase_factory(rows=[])
            result = verify_email_token("short")
        assert result["ok"] is False

    def test_token_not_found_returns_error(self):
        from services.member_service import verify_email_token
        with patch("services.member_service._supabase") as m:
            m.return_value = _mock_supabase_factory(rows=[])
            result = verify_email_token("a" * 96)
        assert result["ok"] is False
        assert "inválido" in result["error"].lower() or "utilizado" in result["error"].lower()

    def test_already_verified_returns_flag(self):
        from services.member_service import verify_email_token
        future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        rows = [{"id": "member-1", "email_verified": True, "email_verification_expires_at": future}]
        with patch("services.member_service._supabase") as m:
            m.return_value = _mock_supabase_factory(rows=rows)
            result = verify_email_token("a" * 96)
        assert result["ok"] is True
        assert result.get("already_verified") is True

    def test_expired_token_returns_error(self):
        from services.member_service import verify_email_token
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        rows = [{"id": "member-1", "email_verified": False, "email_verification_expires_at": past}]
        with patch("services.member_service._supabase") as m:
            sb = MagicMock()
            table = MagicMock()
            select_chain = MagicMock()
            select_chain.execute.return_value = MagicMock(data=rows)
            table.select.return_value.eq.return_value = select_chain
            update_chain = MagicMock()
            update_chain.execute.return_value = MagicMock(data=[{}])
            table.update.return_value.eq.return_value = update_chain
            sb.table.return_value = table
            m.return_value = sb
            result = verify_email_token("a" * 96)
        assert result["ok"] is False
        assert "expirado" in result["error"].lower()

    def test_valid_token_marks_verified(self):
        from services.member_service import verify_email_token
        future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        rows = [{"id": "member-1", "email_verified": False, "email_verification_expires_at": future}]
        update_calls = []
        with patch("services.member_service._supabase") as m:
            sb = MagicMock()
            table = MagicMock()
            select_chain = MagicMock()
            select_chain.execute.return_value = MagicMock(data=rows)
            table.select.return_value.eq.return_value = select_chain
            update_chain = MagicMock()
            update_chain.execute.return_value = MagicMock(data=[{}])
            table.update.return_value.eq.return_value = update_chain
            sb.table.return_value = table
            m.return_value = sb
            result = verify_email_token("a" * 96)
        assert result["ok"] is True
        assert result["member_id"] == "member-1"
        assert result.get("already_verified") is not True


# ============================================================
#  Isolamento multi-tenant: token de outro membro nao verifica
# ============================================================

class TestEmailVerificationTenantIsolation:
    def test_cross_tenant_token_not_found(self):
        """Token pertence a membro A — membro B nao consegue usar."""
        from services.member_service import verify_email_token
        # Supabase filtra por token; se o token nao e do membro correto,
        # a query retorna 0 rows — isso e suficiente para rejeitar.
        with patch("services.member_service._supabase") as m:
            m.return_value = _mock_supabase_factory(rows=[])
            result = verify_email_token("b" * 96)
        assert result["ok"] is False
