# ============================================================
#  tests/test_email_confirm.py — Clube USA
#  Testes de confirmacao de email (Fase 0.1)
# ============================================================

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call


# ============================================================
#  email_service
# ============================================================

class TestGenerateConfirmToken:
    def test_token_is_url_safe_string(self):
        from services.email_service import generate_confirm_token
        token, expires = generate_confirm_token()
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_expires_in_24h(self):
        from services.email_service import generate_confirm_token
        before = datetime.now(timezone.utc)
        _, expires = generate_confirm_token()
        after = datetime.now(timezone.utc)
        assert expires > before + timedelta(hours=23, minutes=55)
        assert expires < after + timedelta(hours=24, minutes=5)

    def test_tokens_are_unique(self):
        from services.email_service import generate_confirm_token
        tokens = {generate_confirm_token()[0] for _ in range(20)}
        assert len(tokens) == 20


class TestSendConfirmationEmail:
    def test_dev_mode_returns_true_and_logs(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with patch.dict(os.environ, {"EMAIL_PROVIDER": "log"}):
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = send_confirmation_email(
                    to_email="joao@example.com",
                    member_name="João",
                    confirm_url="https://clubeusa.com/auth/email/confirm?token=tok123",
                    language="pt",
                )
        assert result is True
        assert "joao@example.com" in caplog.text

    def test_dev_mode_spanish(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with patch.dict(os.environ, {"EMAIL_PROVIDER": "log"}):
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = send_confirmation_email(
                    to_email="maria@example.com",
                    member_name="María",
                    confirm_url="https://clubeusa.com/auth/email/confirm?token=tok456",
                    language="es",
                )
        assert result is True

    def test_unsupported_provider_returns_false(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with patch.dict(os.environ, {"EMAIL_PROVIDER": "unknown_provider"}):
            with caplog.at_level(logging.WARNING, logger="email_service"):
                result = send_confirmation_email(
                    to_email="test@example.com",
                    member_name="",
                    confirm_url="https://clubeusa.com/auth/email/confirm?token=x",
                )
        assert result is False

    def test_resend_missing_key_returns_false(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        env = {"EMAIL_PROVIDER": "resend", "RESEND_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            with caplog.at_level(logging.WARNING, logger="email_service"):
                result = send_confirmation_email(
                    to_email="test@example.com",
                    member_name="Test",
                    confirm_url="https://clubeusa.com/auth/email/confirm?token=x",
                )
        assert result is False

    def test_sendgrid_missing_key_returns_false(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        env = {"EMAIL_PROVIDER": "sendgrid", "SENDGRID_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            with caplog.at_level(logging.WARNING, logger="email_service"):
                result = send_confirmation_email(
                    to_email="test@example.com",
                    member_name="Test",
                    confirm_url="https://clubeusa.com/auth/email/confirm?token=x",
                )
        assert result is False


# ============================================================
#  confirm_member_email
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
            "email_confirm_expires_at": expires,
            "email_confirmed": False,
        }])
        with patch("services.member_service._supabase", return_value=mock_sb), \
             patch("services.member_service._audit"):
            result = confirm_member_email("valid_token_xyz")
        assert result is True
        # Verify update was called to confirm and nullify token
        mock_sb.table.return_value.update.assert_called_once()
        update_data = mock_sb.table.return_value.update.call_args[0][0]
        assert update_data["email_confirmed"] is True
        assert update_data["email_confirm_token"] is None

    def test_expired_token_returns_false(self):
        from services.member_service import confirm_member_email
        expires = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_sb = self._mock_sb([{
            "id": "member-abc",
            "email_confirm_expires_at": expires,
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
            "email_confirm_expires_at": None,
            "email_confirmed": True,
        }])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("any_token")
        assert result is True
        mock_sb.table.return_value.update.assert_not_called()

    def test_token_isolation_cross_member(self):
        """Token de um membro nao confirma email de outro (busca por valor do token, nao por member_id)."""
        from services.member_service import confirm_member_email
        # Token nao encontrado porque e do membro errado (hash diferente)
        mock_sb = self._mock_sb([])
        with patch("services.member_service._supabase", return_value=mock_sb):
            result = confirm_member_email("other_member_token")
        assert result is False


# ============================================================
#  resend_email_confirmation
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
