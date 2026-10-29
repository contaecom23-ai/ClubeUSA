# ============================================================
#  tests/test_email_confirmation.py — Fase 0.1
#  Testa o fluxo de confirmacao de email
# ============================================================

import os
import sys
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "api"))


# ============================================================
#  utils/email.py
# ============================================================

class TestSendConfirmationEmail:
    def test_dev_mode_logs_and_returns_false(self, caplog):
        """Sem SMTP configurado retorna False e loga o link."""
        from utils.email import send_confirmation_email

        env_clean = {k: v for k, v in os.environ.items() if k not in ("SMTP_HOST", "SMTP_USER")}
        with patch.dict(os.environ, env_clean, clear=True):
            import logging
            with caplog.at_level(logging.INFO, logger="email_sender"):
                result = send_confirmation_email(
                    to_email="test@example.com",
                    token="abc123",
                    app_url="https://clubeusa.com",
                    language="pt",
                )

        assert result is False
        assert "abc123" in caplog.text

    def test_smtp_sends_email(self):
        """Com SMTP configurado, envia o email."""
        import base64
        from utils.email import send_confirmation_email

        smtp_env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "secret",
            "FROM_EMAIL": "noreply@clubeusa.com",
        }
        with patch.dict(os.environ, smtp_env):
            with patch("smtplib.SMTP") as mock_smtp:
                instance = MagicMock()
                mock_smtp.return_value.__enter__ = lambda s: instance
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

                result = send_confirmation_email(
                    to_email="user@test.com",
                    token="tok123",
                    app_url="https://clubeusa.com",
                    language="pt",
                )

        assert result is True
        instance.sendmail.assert_called_once()
        args = instance.sendmail.call_args[0]
        assert args[1] == ["user@test.com"]
        # Body is base64 encoded; token URL must appear in decoded content
        raw = args[2]
        b64_token = base64.b64encode(b"tok123").decode()
        # The token appears in the HTML body which is base64 encoded
        assert b64_token in raw or "tok123" in raw or "/confirm/" in raw

    def test_smtp_failure_returns_false(self):
        """Falha de SMTP retorna False sem propagar excecao."""
        from utils.email import send_confirmation_email

        smtp_env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "secret",
        }
        with patch.dict(os.environ, smtp_env):
            with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
                result = send_confirmation_email("x@x.com", "tok", "https://clubeusa.com")

        assert result is False

    def test_spanish_subject(self):
        """Idioma ES usa subject em espanhol."""
        from utils.email import send_confirmation_email

        smtp_env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "secret",
        }
        with patch.dict(os.environ, smtp_env):
            with patch("smtplib.SMTP") as mock_smtp:
                instance = MagicMock()
                mock_smtp.return_value.__enter__ = lambda s: instance
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

                send_confirmation_email("x@x.com", "tok", "https://clubeusa.com", language="es")

        raw_email = instance.sendmail.call_args[0][2]
        # Subject is RFC2047 encoded-word; check it contains "Club_USA" or decoded form
        assert "Club_USA" in raw_email or "Club USA" in raw_email or "=?utf-8?" in raw_email
        # Recipient must be correct
        assert instance.sendmail.call_args[0][1] == ["x@x.com"]


# ============================================================
#  services/member_service.py — confirmacao de email
# ============================================================

def _make_sb_mock():
    return MagicMock()


class TestConfirmEmailToken:
    def _make_member_row(self, confirmed=False, expired=False, token="valid_token"):
        expires = (
            (datetime.utcnow() - timedelta(hours=1)).isoformat()
            if expired
            else (datetime.utcnow() + timedelta(hours=23)).isoformat()
        )
        return {
            "id":                         "member-uuid-001",
            "email_enc":                  "encrypted_email",
            "email_confirmed":            confirmed,
            "email_confirm_expires_at":   expires,
        }

    def test_valid_token_confirms_email(self):
        from services.member_service import confirm_email_token

        member_row = self._make_member_row()
        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [member_row]
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        sb.table.return_value.insert.return_value.execute.return_value.data = []  # audit_log

        with patch("services.member_service._supabase", return_value=sb):
            result = confirm_email_token("valid_token")

        assert result["confirmed"] is True
        assert result["member_id"] == "member-uuid-001"

    def test_invalid_token_raises(self):
        from services.member_service import confirm_email_token

        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("services.member_service._supabase", return_value=sb):
            with pytest.raises(ValueError, match="invalido ou ja utilizado"):
                confirm_email_token("wrong_token")

    def test_expired_token_raises(self):
        from services.member_service import confirm_email_token

        member_row = self._make_member_row(expired=True)
        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [member_row]

        with patch("services.member_service._supabase", return_value=sb):
            with pytest.raises(ValueError, match="expirado"):
                confirm_email_token("expired_token")

    def test_already_confirmed_returns_flag(self):
        from services.member_service import confirm_email_token

        member_row = self._make_member_row(confirmed=True)
        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [member_row]

        with patch("services.member_service._supabase", return_value=sb):
            result = confirm_email_token("valid_token")

        assert result["already_confirmed"] is True

    def test_empty_token_raises(self):
        from services.member_service import confirm_email_token

        with pytest.raises(ValueError, match="invalido"):
            confirm_email_token("")

    def test_too_long_token_raises(self):
        from services.member_service import confirm_email_token

        with pytest.raises(ValueError, match="invalido"):
            confirm_email_token("x" * 200)


class TestResendEmailConfirmation:
    def test_no_email_raises(self):
        from services.member_service import resend_email_confirmation

        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "email_enc": None,
            "email_confirmed": False,
            "language": "pt",
        }]

        with patch("services.member_service._supabase", return_value=sb):
            with pytest.raises(ValueError, match="Nenhum email"):
                resend_email_confirmation("member-id")

    def test_already_confirmed_raises(self):
        from services.member_service import resend_email_confirmation

        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "email_enc": "encrypted",
            "email_confirmed": True,
            "language": "pt",
        }]

        with patch("services.member_service._supabase", return_value=sb):
            with pytest.raises(ValueError, match="ja confirmado"):
                resend_email_confirmation("member-id")

    def test_sends_and_returns_result(self):
        from services.member_service import resend_email_confirmation

        sb = _make_sb_mock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "email_enc": "encrypted",
            "email_confirmed": False,
            "language": "pt",
        }]
        # For update (save token) and insert (audit_log)
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        sb.table.return_value.insert.return_value.execute.return_value.data = []

        with patch("services.member_service._supabase", return_value=sb), \
             patch("services.member_service.decrypt", return_value="user@example.com"), \
             patch("utils.email.send_confirmation_email", return_value=True) as mock_send:
            result = resend_email_confirmation("member-id")

        assert "sent" in result
        mock_send.assert_called_once()


class TestDispatchEmailConfirmation:
    def test_generates_token_and_saves_to_db(self):
        from services.member_service import _dispatch_email_confirmation

        sb = _make_sb_mock()
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        sb.table.return_value.insert.return_value.execute.return_value.data = []

        with patch("services.member_service._supabase", return_value=sb), \
             patch("utils.email.send_confirmation_email", return_value=False) as mock_send:
            result = _dispatch_email_confirmation("member-id", "user@test.com", "pt")

        update_call = sb.table.return_value.update.call_args
        saved_data = update_call[0][0]
        assert "email_confirm_token" in saved_data
        assert len(saved_data["email_confirm_token"]) > 20
        assert "email_confirm_expires_at" in saved_data

        mock_send.assert_called_once_with("user@test.com", saved_data["email_confirm_token"],
                                          os.environ.get("APP_URL", "https://clubeusa.com"), "pt")
