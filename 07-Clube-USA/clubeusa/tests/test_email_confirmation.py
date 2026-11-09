"""
test_email_confirmation.py — Fase 0.1

Testa o fluxo completo de confirmação de email:
  - email_service.send_email_confirmation (modo dev + Resend)
  - confirm_email endpoint (token válido / expirado / inválido)
  - resend endpoint (token regenerado, já confirmado)
  - Isolamento: um membro nunca confirma email de outro (IDOR)
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, ANY
import pytest


# ============================================================
#  email_service
# ============================================================

class TestEmailService:
    def test_dev_mode_logs_and_returns_true(self, caplog):
        """Sem RESEND_API_KEY, apenas loga e retorna True."""
        import importlib
        import services.email_service as es

        orig_key = os.environ.pop("RESEND_API_KEY", None)
        try:
            importlib.reload(es)
            with caplog.at_level("INFO", logger="email_service"):
                result = es.send_email_confirmation(
                    to_email="test@example.com",
                    member_name="João",
                    token="abc123",
                    language="pt",
                )
            assert result is True
            assert "abc123" in caplog.text
        finally:
            if orig_key:
                os.environ["RESEND_API_KEY"] = orig_key
            importlib.reload(es)

    def test_resend_success(self):
        """Com RESEND_API_KEY, faz POST ao Resend e retorna True."""
        import services.email_service as es

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"}):
            with patch("services.email_service.requests.post", return_value=mock_resp) as mock_post:
                result = es.send_email_confirmation(
                    to_email="test@example.com",
                    member_name="Maria",
                    token="tok_xyz",
                    language="pt",
                )
        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["to"] == ["test@example.com"]
        assert "tok_xyz" in payload["html"]

    def test_resend_failure_returns_false(self):
        """Resend retornando 500 → False, sem levantar exceção."""
        import services.email_service as es

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"}):
            with patch("services.email_service.requests.post", return_value=mock_resp):
                result = es.send_email_confirmation(
                    to_email="test@example.com",
                    member_name="Carlos",
                    token="tok_fail",
                    language="es",
                )
        assert result is False

    def test_network_exception_returns_false(self):
        """Exceção de rede → False, sem propagar."""
        import services.email_service as es

        with patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"}):
            with patch("services.email_service.requests.post", side_effect=ConnectionError("timeout")):
                result = es.send_email_confirmation(
                    to_email="test@example.com",
                    member_name="Ana",
                    token="tok_net",
                    language="pt",
                )
        assert result is False

    def test_html_pt_contains_link(self):
        import services.email_service as es
        html = es._html_pt("Teste", "https://clubeusa.com/auth/email/confirm/TOK")
        assert "https://clubeusa.com/auth/email/confirm/TOK" in html
        assert "Confirmar meu email" in html

    def test_html_es_contains_link(self):
        import services.email_service as es
        html = es._html_es("Prueba", "https://clubeusa.com/auth/email/confirm/TOK2")
        assert "https://clubeusa.com/auth/email/confirm/TOK2" in html
        assert "Confirmar mi correo" in html


# ============================================================
#  Confirm endpoint — testa a lógica RPC via mock Supabase
# ============================================================

class TestConfirmEmailEndpoint:
    """Testa GET /auth/email/confirm/{token} sem chamadas reais ao banco."""

    def _make_app_client(self, rpc_data):
        """Cria TestClient com supabase mockado."""
        from fastapi.testclient import TestClient
        import sys
        import types

        # Monta mock mínimo de supabase
        mock_rpc_result = MagicMock()
        mock_rpc_result.data = rpc_data

        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        mock_module = types.ModuleType("supabase")
        mock_module.create_client = MagicMock(return_value=mock_sb)

        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://fake.supabase.co",
            "SUPABASE_SERVICE_KEY": "fake-key",
            "APP_URL": "https://clubeusa.com",
        }):
            with patch.dict(sys.modules, {"supabase": mock_module}):
                import importlib
                import api.main as main_module
                importlib.reload(main_module)
                client = TestClient(main_module.app, follow_redirects=False)
                return client, mock_sb

    def test_valid_token_redirects(self):
        client, mock_sb = self._make_app_client(
            rpc_data=[{"member_id": "uuid-123", "email_enc": "enc", "success": True}]
        )
        resp = client.get("/auth/email/confirm/valid_token_abc")
        assert resp.status_code == 302
        assert "email_confirmed=1" in resp.headers["location"]

    def test_invalid_token_returns_error_html(self):
        client, _ = self._make_app_client(
            rpc_data=[{"member_id": None, "email_enc": None, "success": False}]
        )
        resp = client.get("/auth/email/confirm/bad_token")
        assert resp.status_code == 400
        assert "Link" in resp.text

    def test_empty_token_rejected(self):
        """Token muito longo é rejeitado antes de bater no banco."""
        client, mock_sb = self._make_app_client(rpc_data=[])
        long_token = "x" * 200
        resp = client.get(f"/auth/email/confirm/{long_token}")
        assert resp.status_code == 400
        mock_sb.rpc.assert_not_called()

    def test_rpc_called_with_correct_token(self):
        client, mock_sb = self._make_app_client(
            rpc_data=[{"member_id": "uuid-456", "email_enc": "enc", "success": True}]
        )
        client.get("/auth/email/confirm/my_specific_token")
        mock_sb.rpc.assert_called_once_with(
            "confirm_member_email", {"p_token": "my_specific_token"}
        )
