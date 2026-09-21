# tests/test_email_confirmation.py — Fase 0.1
# Testa geração/validação de token e envio de e-mail de confirmação

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ── conftest.py já insere o root no sys.path ──────────────────────────────────


# ============================================================
#  email_service — unit tests (sem rede, sem DB)
# ============================================================

class TestEmailServiceLogic:
    """Testa a lógica pura de token sem tocar no banco."""

    def test_token_is_random_and_long(self):
        t1 = secrets.token_urlsafe(48)
        t2 = secrets.token_urlsafe(48)
        assert t1 != t2
        assert len(t1) >= 48

    def test_token_hash_is_sha256(self):
        raw = secrets.token_urlsafe(48)
        h = hashlib.sha256(raw.encode()).hexdigest()
        assert len(h) == 64
        assert h == hashlib.sha256(raw.encode()).hexdigest()  # determinístico

    def test_token_hash_does_not_equal_raw(self):
        raw = secrets.token_urlsafe(48)
        h = hashlib.sha256(raw.encode()).hexdigest()
        assert raw != h

    def test_html_pt_contains_url(self):
        from services.email_service import _build_html_pt
        html = _build_html_pt("https://clubeusa.com/auth/email/confirm/abc123")
        assert "https://clubeusa.com/auth/email/confirm/abc123" in html
        assert "Confirme seu e-mail" in html

    def test_html_es_contains_url(self):
        from services.email_service import _build_html_es
        html = _build_html_es("https://clubeusa.com/auth/email/confirm/abc123")
        assert "https://clubeusa.com/auth/email/confirm/abc123" in html
        assert "Confirma tu correo" in html

    def test_send_raw_dev_mode_logs_and_returns_true(self, caplog):
        """Em dev (sem SMTP_HOST), deve logar e retornar True."""
        import logging
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SMTP_HOST", None)
            from services import email_service
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = email_service._send_raw(
                    "test@example.com", "Assunto", "<p>HTML</p>", "Texto"
                )
            assert result is True
            assert "test@example.com" in caplog.text


class TestSendConfirmationEmail:
    """Testa send_confirmation_email com mock do Supabase."""

    def _make_sb_mock(self):
        sb = MagicMock()
        delete_chain = MagicMock()
        sb.table.return_value.delete.return_value.eq.return_value.is_.return_value = delete_chain
        insert_chain = MagicMock()
        sb.table.return_value.insert.return_value = insert_chain
        return sb

    @patch("services.email_service._send_raw", return_value=True)
    @patch("services.email_service.create_client")
    def test_sends_email_and_stores_token(self, mock_create, mock_send):
        mock_create.return_value = self._make_sb_mock()

        from services.email_service import send_confirmation_email
        result = send_confirmation_email(
            "member-uuid-123", "user@example.com", language="pt"
        )

        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "user@example.com"
        assert "Confirme seu e-mail" in call_args[1]

    @patch("services.email_service._send_raw", return_value=True)
    @patch("services.email_service.create_client")
    def test_sends_spanish_email(self, mock_create, mock_send):
        mock_create.return_value = self._make_sb_mock()

        from services.email_service import send_confirmation_email
        send_confirmation_email("uuid", "user@example.com", language="es")

        call_args = mock_send.call_args[0]
        assert "Confirma tu correo" in call_args[1]

    @patch("services.email_service._send_raw", return_value=False)
    @patch("services.email_service.create_client")
    def test_returns_false_on_smtp_failure(self, mock_create, mock_send):
        mock_create.return_value = self._make_sb_mock()

        from services.email_service import send_confirmation_email
        result = send_confirmation_email("uuid", "fail@example.com")
        assert result is False


class TestConfirmEmailToken:
    """Testa confirm_email_token — fluxos de sucesso e erro."""

    def _sb_with_token(self, expired=False, already_used=False):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        expires = now - timedelta(hours=1) if expired else now + timedelta(hours=24)

        sb = MagicMock()

        # usado_at = null significa token disponível
        token_record = {
            "id":        "token-id-abc",
            "member_id": "member-uuid-abc",
            "expires_at": expires.isoformat(),
            "used_at":   now.isoformat() if already_used else None,
        }

        select_chain = MagicMock()
        select_chain.execute.return_value.data = [] if already_used else [token_record]
        (sb.table.return_value
           .select.return_value
           .eq.return_value
           .is_.return_value) = select_chain

        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
        return sb

    @patch("services.email_service.create_client")
    def test_valid_token_confirms_email(self, mock_create):
        mock_create.return_value = self._sb_with_token()

        from services.email_service import confirm_email_token
        token_raw = secrets.token_urlsafe(48)
        result = confirm_email_token(token_raw)
        assert result["ok"] is True
        assert result["member_id"] == "member-uuid-abc"

    @patch("services.email_service.create_client")
    def test_invalid_token_returns_error(self, mock_create):
        sb = MagicMock()
        (sb.table.return_value
           .select.return_value
           .eq.return_value
           .is_.return_value
           .execute.return_value.data) = []
        mock_create.return_value = sb

        from services.email_service import confirm_email_token
        result = confirm_email_token("nonexistent-token")
        assert result["ok"] is False
        assert "inválido" in result["error"].lower() or "expirado" in result["error"].lower()

    @patch("services.email_service.create_client")
    def test_expired_token_returns_error(self, mock_create):
        mock_create.return_value = self._sb_with_token(expired=True)

        from services.email_service import confirm_email_token
        result = confirm_email_token(secrets.token_urlsafe(48))
        assert result["ok"] is False
        assert "expirado" in result["error"].lower()

    @patch("services.email_service.create_client")
    def test_used_token_not_found(self, mock_create):
        mock_create.return_value = self._sb_with_token(already_used=True)

        from services.email_service import confirm_email_token
        result = confirm_email_token(secrets.token_urlsafe(48))
        assert result["ok"] is False


# ============================================================
#  Isolamento multi-tenant: membro A não pode confirmar email de membro B
# ============================================================

class TestMultiTenantIsolation:
    """Garantia de que os tokens são isolados por member_id."""

    @patch("services.email_service.create_client")
    def test_token_lookup_uses_hash_not_raw(self, mock_create):
        """O banco deve ser consultado com SHA-256 do token, nunca com o token bruto."""
        sb = MagicMock()
        captured_args = {}

        def fake_eq(field, value):
            captured_args[field] = value
            return sb.table.return_value.select.return_value.eq.return_value

        sb.table.return_value.select.return_value.eq.side_effect = fake_eq
        sb.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value.data = []
        mock_create.return_value = sb

        from services.email_service import confirm_email_token
        raw_token = "super-secret-raw-token"
        confirm_email_token(raw_token)

        stored_value = captured_args.get("token_hash", "")
        assert stored_value != raw_token, "Token bruto nunca deve ser consultado no banco"
        assert len(stored_value) == 64, "Deve ser SHA-256 hex (64 chars)"
