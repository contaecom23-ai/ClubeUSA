# ============================================================
#  tests/test_email_verification.py — Clube USA
#  Testes do email_service.py (Fase 0.1)
# ============================================================
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_service — transporte e templates
# ============================================================

class TestEmailServiceDevMode:
    def test_send_logs_in_dev(self, caplog):
        """Em dev (ENVIRONMENT != production), email é logado, não enviado."""
        import logging
        import services.email_service as es
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = es._send("test@example.com", "Assunto", "texto plano", "<p>html</p>")
        assert result is True

    def test_send_logs_link_from_html(self, caplog):
        """Em dev, extrai e loga links do HTML para facilitar teste manual."""
        import logging
        import services.email_service as es
        html = '<a href="https://example.com/confirm/abc123">Confirmar</a>'
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            with caplog.at_level(logging.INFO, logger="email_service"):
                es._send("x@y.com", "s", "t", html)
        assert any("abc123" in r.message for r in caplog.records)

    def test_send_confirmation_email_calls_send(self):
        """send_confirmation_email delega para _send com args corretos."""
        import services.email_service as es
        with patch.object(es, "_send", return_value=True) as mock_send:
            result = es.send_confirmation_email("u@example.com", "Joao", "https://clubeusa.com/confirm/tok")
        assert result is True
        call_args = mock_send.call_args[0]
        assert call_args[0] == "u@example.com"
        assert "Confirme" in call_args[1]        # subject
        assert "https://clubeusa.com/confirm/tok" in call_args[3]  # html body

    def test_html_confirmation_escapes_xss(self):
        """HTML do email escapa caracteres perigosos para prevenir XSS."""
        import services.email_service as es
        html = es._html_confirmation('<script>alert(1)</script>', 'https://ok.com/token')
        assert '<script>' not in html
        assert '&lt;script&gt;' in html

    def test_html_confirmation_contains_link(self):
        """HTML contém o link de confirmação."""
        import services.email_service as es
        html = es._html_confirmation('Joao', 'https://clubeusa.com/auth/email/confirm/TOKEN123')
        assert 'TOKEN123' in html


class TestEmailServiceSendGrid:
    def test_sendgrid_called_when_api_key_set(self):
        """Em produção com SENDGRID_API_KEY, usa SendGrid."""
        import services.email_service as es
        mock_response = MagicMock()
        mock_response.status_code = 202
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SENDGRID_API_KEY": "SG.fake_key",
        }):
            with patch.object(es, "_send_sendgrid", return_value=True) as sg_mock:
                with patch.object(es, "_send_smtp", return_value=False) as smtp_mock:
                    es._send("a@b.com", "s", "t", "<p>h</p>")
        sg_mock.assert_called_once()
        smtp_mock.assert_not_called()

    def test_smtp_called_when_no_sendgrid_key(self):
        """Em produção sem SENDGRID_API_KEY, usa SMTP."""
        import services.email_service as es
        env = {"ENVIRONMENT": "production"}
        with patch.dict(os.environ, env, clear=True):
            with patch.object(es, "_send_sendgrid", return_value=True) as sg_mock:
                with patch.object(es, "_send_smtp", return_value=True) as smtp_mock:
                    es._send("a@b.com", "s", "t", "<p>h</p>")
        sg_mock.assert_not_called()
        smtp_mock.assert_called_once()


class TestEmailServiceSmtp:
    def test_smtp_returns_false_when_not_configured(self):
        """SMTP retorna False se variáveis não configuradas."""
        import services.email_service as es
        with patch.dict(os.environ, {}, clear=True):
            result = es._send_smtp("x@y.com", "s", "t", "<p>h</p>")
        assert result is False

    def test_smtp_logs_error_when_not_configured(self, caplog):
        """SMTP loga erro quando não configurado."""
        import logging
        import services.email_service as es
        with patch.dict(os.environ, {}, clear=True):
            with caplog.at_level(logging.ERROR, logger="email_service"):
                es._send_smtp("x@y.com", "s", "t", "<p>h</p>")
        assert any("SMTP" in r.message for r in caplog.records)
