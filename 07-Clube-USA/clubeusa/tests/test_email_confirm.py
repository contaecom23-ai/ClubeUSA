# ============================================================
#  tests/test_email_confirm.py — Clube USA
#  Testes de confirmacao de email (Fase 0.1)
# ============================================================

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


# ============================================================
#  email_service — geracao de token
# ============================================================

class TestGenerateEmailToken:
    def test_token_is_url_safe_string(self):
        from services.email_service import generate_email_token
        token = generate_email_token()
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_tokens_are_unique(self):
        from services.email_service import generate_email_token
        tokens = {generate_email_token() for _ in range(20)}
        assert len(tokens) == 20


# ============================================================
#  email_service — envio de email
# ============================================================

class TestSendConfirmationEmail:
    def test_dev_mode_logs_and_does_not_raise(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            with caplog.at_level(logging.INFO, logger="email_service"):
                # Should not raise
                send_confirmation_email(
                    to_email="joao@example.com",
                    member_id="member-123",
                    token="tok123",
                )
        assert "[DEV]" in caplog.text

    def test_prod_no_provider_logs_warning(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "EMAIL_PROVIDER": ""}):
            with caplog.at_level(logging.WARNING, logger="email_service"):
                send_confirmation_email(
                    to_email="joao@example.com",
                    member_id="member-123",
                    token="tok123",
                )
        assert "EMAIL_PROVIDER" in caplog.text

    def test_prod_resend_missing_key_logs_error(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": "resend", "RESEND_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            with caplog.at_level(logging.ERROR, logger="email_service"):
                send_confirmation_email("test@example.com", "m-1", "tok")
        assert "RESEND_API_KEY" in caplog.text

    def test_prod_sendgrid_missing_key_logs_error(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": "sendgrid", "SENDGRID_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            with caplog.at_level(logging.ERROR, logger="email_service"):
                send_confirmation_email("test@example.com", "m-1", "tok")
        assert "SENDGRID_API_KEY" in caplog.text


# ============================================================
#  confirm_member_email (member_service)
# ============================================================

class TestConfirmMemberEmail:
    def _mock_sb(self, data):
        mock = MagicMock()
        (mock.table.return_value
             .select.return_value
             .eq.return_value
             .execute.return_value.data) = data
        return mock

    def test_valid_token_confirms_email(self):
        from services.member_service import confirm_member_email
        expires = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
        mock_sb = self._mock_sb([{
            "id": "member-abc",
            "email_token_expires_at": expires,
            "email_confirmed": False,
        }])
        with patch("services.member_service._supabase", return_value=mock_sb), \
             patch("services.member_service._audit"):
            result = confirm_member_email("valid_token_xyz")
        assert result is True
        mock_sb.table.return_value.update.assert_called_once()
        update_data = mock_sb.table.return_value.update.call_args[0][0]
        assert update_data["email_confirmed"] is True
        assert update_data["email_token"] is None

    def test_expired_token_returns_false(self):
        from services.member_service import confirm_member_email
        expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_sb = self._mock_sb([{
            "id": "member-abc",
            "email_token_expires_at": expires,
            "email_confirmed": False,
        }])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("expired_token")
        assert result is False
        mock_sb.table.return_value.update.assert_not_called()

    def test_nonexistent_token_returns_false(self):
        from services.member_service import confirm_member_email
        mock_sb = self._mock_sb([])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("does_not_exist")
        assert result is False

    def test_already_confirmed_is_idempotent(self):
        from services.member_service import confirm_member_email
        mock_sb = self._mock_sb([{
            "id": "member-abc",
            "email_token_expires_at": None,
            "email_confirmed": True,
        }])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("any_token")
        assert result is True
        mock_sb.table.return_value.update.assert_not_called()

    def test_token_isolation_cross_member(self):
        """Token de um membro nao confirma email de outro (busca por valor do token)."""
        from services.member_service import confirm_member_email
        mock_sb = self._mock_sb([])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("other_member_token")
        assert result is False


# ============================================================
#  resend_email_confirmation (member_service)
# ============================================================

class TestResendEmailConfirmation:
    def test_wrong_email_returns_false(self):
        from services.member_service import resend_email_confirmation
        mock_sb = MagicMock()
        from utils.security import hash_pii
        real_hash = hash_pii("real@example.com")
        (mock_sb.table.return_value
                .select.return_value
                .eq.return_value
                .execute.return_value.data) = [{
            "id": "member-123",
            "email_hash": real_hash,
            "email_enc": None,
            "email_confirmed": False,
            "name_enc": None,
            "language": "pt",
        }]
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = resend_email_confirmation("member-123", "wrong@example.com")
        assert result is False

    def test_already_confirmed_returns_true(self):
        from services.member_service import resend_email_confirmation
        mock_sb = MagicMock()
        (mock_sb.table.return_value
                .select.return_value
                .eq.return_value
                .execute.return_value.data) = [{
            "id": "member-123",
            "email_hash": "any_hash",
            "email_enc": None,
            "email_confirmed": True,
            "name_enc": None,
            "language": "pt",
        }]
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = resend_email_confirmation("member-123", "any@example.com")
        assert result is True

    def test_member_not_found_returns_false(self):
        from services.member_service import resend_email_confirmation
        mock_sb = MagicMock()
        (mock_sb.table.return_value
                .select.return_value
                .eq.return_value
                .execute.return_value.data) = []
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = resend_email_confirmation("nonexistent-id", "any@example.com")
        assert result is False
