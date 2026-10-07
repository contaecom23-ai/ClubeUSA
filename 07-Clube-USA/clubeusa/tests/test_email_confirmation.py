# ============================================================
#  tests/test_email_confirmation.py — Fase 0.1
#  Testa o fluxo completo de confirmacao de email
# ============================================================

import hashlib
import secrets
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# Garante que o diretório services/ está no path
ROOT = os.path.join(os.path.dirname(__file__), '..')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _make_token():
    return secrets.token_urlsafe(32)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# email_service.create_confirmation_token
# ---------------------------------------------------------------------------

class TestCreateConfirmationToken:
    def test_returns_urlsafe_token(self):
        mock_sb = MagicMock()
        mock_sb.table.return_value.delete.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock()
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            token = svc.create_confirmation_token("member-abc")

        assert len(token) >= 32

    def test_invalidates_previous_tokens(self):
        mock_sb = MagicMock()
        delete_chain = mock_sb.table.return_value.delete.return_value.eq.return_value.is_.return_value

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            svc.create_confirmation_token("member-xyz")

        mock_sb.table.assert_any_call("email_confirmation_tokens")
        delete_chain.execute.assert_called_once()


# ---------------------------------------------------------------------------
# email_service.verify_confirmation_token
# ---------------------------------------------------------------------------

class TestVerifyConfirmationToken:
    def _mock_sb_with_record(self, record):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = record
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        return mock_sb

    def test_valid_token_returns_member_id(self):
        token = _make_token()
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        record = [{"id": "tok-1", "member_id": "member-abc", "expires_at": expires, "used_at": None}]
        mock_sb = self._mock_sb_with_record(record)

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            result = svc.verify_confirmation_token(token)

        assert result == "member-abc"

    def test_expired_token_returns_none(self):
        token = _make_token()
        expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        record = [{"id": "tok-2", "member_id": "member-abc", "expires_at": expires, "used_at": None}]
        mock_sb = self._mock_sb_with_record(record)

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            result = svc.verify_confirmation_token(token)

        assert result is None

    def test_already_used_token_returns_none(self):
        token = _make_token()
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        record = [{"id": "tok-3", "member_id": "member-abc", "expires_at": expires, "used_at": "2026-01-01T00:00:00Z"}]
        mock_sb = self._mock_sb_with_record(record)

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            result = svc.verify_confirmation_token(token)

        assert result is None

    def test_unknown_token_returns_none(self):
        mock_sb = self._mock_sb_with_record([])

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            result = svc.verify_confirmation_token("token-invalido")

        assert result is None

    def test_valid_token_marks_as_used(self):
        """Garante single-use: token valido é marcado como usado."""
        token = _make_token()
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        record = [{"id": "tok-4", "member_id": "member-abc", "expires_at": expires, "used_at": None}]
        mock_sb = self._mock_sb_with_record(record)

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            svc.verify_confirmation_token(token)

        mock_sb.table.return_value.update.assert_called_once()
        update_args = mock_sb.table.return_value.update.call_args[0][0]
        assert "used_at" in update_args


# ---------------------------------------------------------------------------
# email_service.send_confirmation_email
# ---------------------------------------------------------------------------

class TestSendConfirmationEmail:
    def test_dev_mode_logs_and_returns_true(self, caplog):
        """Sem EMAIL_PROVIDER configurado, apenas loga (nao envia)."""
        import logging
        import importlib
        import services.email_service as svc

        env = {"APP_URL": "https://test.com", "EMAIL_FROM": "x@x.com"}
        with patch.dict(os.environ, env, clear=False):
            importlib.reload(svc)
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = svc.send_confirmation_email("test@example.com", "tok123", "pt")

        assert result is True

    def test_resend_success(self):
        import importlib
        import services.email_service as svc
        import requests as req_mod
        importlib.reload(svc)

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.object(req_mod, "post", return_value=mock_resp), \
             patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key", "EMAIL_FROM": "x@x.com", "APP_URL": "https://x.com"}):
            result = svc._send_via_resend("user@example.com", "Subject", "<p>Test</p>")

        assert result is True

    def test_resend_failure_returns_false(self):
        import importlib
        import services.email_service as svc
        import requests as req_mod
        importlib.reload(svc)

        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.text = "Unprocessable"

        with patch.object(req_mod, "post", return_value=mock_resp), \
             patch.dict(os.environ, {"RESEND_API_KEY": "re_test", "EMAIL_FROM": "x@x.com", "APP_URL": "https://x.com"}):
            result = svc._send_via_resend("user@example.com", "Sub", "<p>x</p>")

        assert result is False

    def test_resend_missing_key_returns_false(self):
        import importlib
        import services.email_service as svc
        importlib.reload(svc)

        with patch.dict(os.environ, {}, clear=True):
            result = svc._send_via_resend("user@example.com", "Sub", "<p>x</p>")

        assert result is False


# ---------------------------------------------------------------------------
# Integracao: register_member dispara email de confirmacao
# ---------------------------------------------------------------------------

class TestRegisterTriggerEmail:
    def _make_mock_sb(self, member_id="new-member-id", referral_code="ABCD1234"):
        mock_sb = MagicMock()
        # Lookup de duplicata (nao existe)
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        # Insert retorna o membro criado
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": member_id,
            "plan": "free",
            "referral_code": referral_code,
        }]
        return mock_sb

    def test_register_with_email_calls_send_confirmation(self):
        """Registrar membro com email deve disparar send_confirmation_email."""
        import importlib
        import services.member_service as ms
        import services.group_manager as gm
        import services.email_service as es
        importlib.reload(ms)

        mock_sb = self._make_mock_sb()

        with patch.dict(os.environ, {
            "SUPABASE_URL": "x",
            "SUPABASE_SERVICE_KEY": "y",
            "ENCRYPTION_KEY": "test-key-32bytes-padding-here!!",
            "JWT_SECRET": "jwt-secret-long-enough-for-tests",
        }), \
        patch("supabase.create_client", return_value=mock_sb), \
        patch.object(gm, "assign_member_to_group", return_value={}), \
        patch.object(es, "create_confirmation_token", return_value="tok-abc"), \
        patch.object(es, "send_confirmation_email", return_value=True) as mock_send:
            result = ms.register_member(
                phone="+15555551234",
                name="Test User",
                email="user@example.com",
                language="pt",
            )

        mock_send.assert_called_once_with("user@example.com", "tok-abc", "pt")
        assert result["email_confirmation_sent"] is True

    def test_register_without_email_skips_confirmation(self):
        """Registrar sem email nao dispara confirmacao."""
        import importlib
        import services.member_service as ms
        import services.group_manager as gm
        import services.email_service as es
        importlib.reload(ms)

        mock_sb = self._make_mock_sb(member_id="new-member-id-2", referral_code="EFGH5678")

        with patch.dict(os.environ, {
            "SUPABASE_URL": "x",
            "SUPABASE_SERVICE_KEY": "y",
            "ENCRYPTION_KEY": "test-key-32bytes-padding-here!!",
            "JWT_SECRET": "jwt-secret-long-enough-for-tests",
        }), \
        patch("supabase.create_client", return_value=mock_sb), \
        patch.object(gm, "assign_member_to_group", return_value={}), \
        patch.object(es, "send_confirmation_email") as mock_send:
            result = ms.register_member(phone="+15555559999", language="pt")

        mock_send.assert_not_called()
        assert result["email_confirmation_sent"] is False


# ---------------------------------------------------------------------------
# Isolamento multi-tenant: token so confirma o membro dono do token
# ---------------------------------------------------------------------------

class TestMultiTenantIsolation:
    def test_token_b_does_not_confirm_member_a(self):
        """Token gerado para membro A nao pode confirmar membro B com token_b inexistente."""
        token_b = _make_token()

        mock_sb = MagicMock()
        # Banco nao conhece token_b
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "y"}), \
             patch("supabase.create_client", return_value=mock_sb):
            import importlib
            import services.email_service as svc
            importlib.reload(svc)
            result = svc.verify_confirmation_token(token_b)

        assert result is None
