# tests/test_auth_email.py — Clube USA  Fase 0.1
# Suite de testes: email confirmation service + endpoints.
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

# Env vars ANTES de importar modulos do projeto
os.environ.setdefault("ENCRYPTION_KEY", "test-key-clubeusa-2026-aaaaaaaaaaaaa")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-clubeusa-2026")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("APP_URL", "https://clubeusa.com")
os.environ.setdefault("EMAIL_PROVIDER", "dev")

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_client(auth_override=None, follow_redirects=False):
    from api.routers.auth_email import router
    from deps import get_current_member
    app = FastAPI()
    app.include_router(router)
    if auth_override is not None:
        app.dependency_overrides[get_current_member] = lambda: auth_override
    return TestClient(app, follow_redirects=follow_redirects)


MEMBER = {"sub": "mem-test-001", "plan": "free"}
FUTURE  = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
PAST    = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()


# ============================================================
#  email_service unit tests
# ============================================================

class TestGenerateConfirmationToken:
    def _mock_sb(self):
        sb = MagicMock()
        sb.table.return_value.delete.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock()
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
        return sb

    def test_returns_url_safe_string(self):
        sb = self._mock_sb()
        with patch("services.email_service.create_client", return_value=sb):
            from services.email_service import generate_confirmation_token
            token = generate_confirmation_token("mem-001")
        assert isinstance(token, str) and len(token) >= 32

    def test_invalidates_previous_pending_tokens(self):
        """Delete chamado antes de inserir novo token."""
        sb = self._mock_sb()
        delete_execute = sb.table.return_value.delete.return_value.eq.return_value.eq.return_value.is_.return_value.execute
        with patch("services.email_service.create_client", return_value=sb):
            from services.email_service import generate_confirmation_token
            generate_confirmation_token("mem-001")
        delete_execute.assert_called_once()


class TestVerifyConfirmationToken:
    def _sb_with_token(self, expires: str, member_id: str = "mem-A"):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = [
            {"id": "tok-1", "member_id": member_id, "token": "tok", "expires_at": expires}
        ]
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        return sb

    def _sb_no_token(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = []
        return sb

    def test_valid_token_returns_member_id(self):
        sb = self._sb_with_token(FUTURE, member_id="mem-A")
        with patch("services.email_service.create_client", return_value=sb):
            from services import email_service
            result = email_service.verify_confirmation_token("tok")
        assert result == "mem-A"

    def test_missing_token_returns_none(self):
        sb = self._sb_no_token()
        with patch("services.email_service.create_client", return_value=sb):
            from services import email_service
            result = email_service.verify_confirmation_token("nope")
        assert result is None

    def test_expired_token_returns_none(self):
        sb = self._sb_with_token(PAST)
        with patch("services.email_service.create_client", return_value=sb):
            from services import email_service
            result = email_service.verify_confirmation_token("tok")
        assert result is None

    def test_valid_token_updates_email_confirmed_at(self):
        """Confirmar email persiste email_confirmed_at no membro."""
        sb = self._sb_with_token(FUTURE, member_id="mem-confirm")
        update_chain = sb.table.return_value.update.return_value.eq.return_value.execute
        with patch("services.email_service.create_client", return_value=sb):
            from services import email_service
            email_service.verify_confirmation_token("tok")
        assert update_chain.call_count >= 1


class TestSendConfirmationEmail:
    def test_returns_true_on_success(self):
        with patch("services.email_service.generate_confirmation_token", return_value="tok-123"), \
             patch("services.email_service._send"):
            from services.email_service import send_confirmation_email
            result = send_confirmation_email("mem-1", "test@example.com", "Joao")
        assert result is True

    def test_returns_false_on_exception(self):
        with patch("services.email_service.generate_confirmation_token", side_effect=Exception("db down")):
            from services.email_service import send_confirmation_email
            result = send_confirmation_email("mem-1", "test@example.com")
        assert result is False


# ============================================================
#  API endpoint tests
# ============================================================

class TestEmailStatusEndpoint:
    def test_requires_auth(self):
        client = _make_client()
        assert client.get("/auth/email/status").status_code == 401

    def test_returns_confirmed_true(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"email_confirmed_at": "2026-01-01T00:00:00+00:00"}
        ]
        with patch("api.routers.auth_email.create_client", return_value=sb):
            client = _make_client(auth_override=MEMBER)
            resp = client.get("/auth/email/status")
        assert resp.status_code == 200
        assert resp.json()["confirmed"] is True

    def test_returns_confirmed_false_when_null(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"email_confirmed_at": None}
        ]
        with patch("api.routers.auth_email.create_client", return_value=sb):
            client = _make_client(auth_override=MEMBER)
            resp = client.get("/auth/email/status")
        assert resp.status_code == 200
        assert resp.json()["confirmed"] is False


class TestRequestEmailConfirmationEndpoint:
    def test_requires_auth(self):
        client = _make_client()
        assert client.post("/auth/email/request-confirmation").status_code == 401

    def test_returns_already_confirmed_when_email_confirmed(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "mem-test-001",
            "email_enc": "encrypted",
            "name_enc": None,
            "email_confirmed_at": "2026-01-01T00:00:00Z",
        }]
        with patch("api.routers.auth_email.create_client", return_value=sb):
            client = _make_client(auth_override=MEMBER)
            resp = client.post("/auth/email/request-confirmation")
        assert resp.status_code == 200
        assert resp.json()["confirmed"] is True

    def test_returns_400_when_no_email(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "mem-test-001",
            "email_enc": None,
            "name_enc": None,
            "email_confirmed_at": None,
        }]
        with patch("api.routers.auth_email.create_client", return_value=sb):
            client = _make_client(auth_override=MEMBER)
            resp = client.post("/auth/email/request-confirmation")
        assert resp.status_code == 400

    def test_sends_email_and_returns_success(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "mem-test-001",
            "email_enc": "enc-email",
            "name_enc": "enc-name",
            "email_confirmed_at": None,
        }]
        with patch("api.routers.auth_email.create_client", return_value=sb), \
             patch("utils.security.decrypt", return_value="test@example.com"), \
             patch("services.email_service.send_confirmation_email", return_value=True):
            client = _make_client(auth_override=MEMBER)
            resp = client.post("/auth/email/request-confirmation")
        assert resp.status_code == 200
        assert resp.json()["confirmed"] is False

    def test_returns_503_when_email_send_fails(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "mem-test-001",
            "email_enc": "enc-email",
            "name_enc": None,
            "email_confirmed_at": None,
        }]
        with patch("api.routers.auth_email.create_client", return_value=sb), \
             patch("utils.security.decrypt", return_value="test@example.com"), \
             patch("services.email_service.send_confirmation_email", return_value=False):
            client = _make_client(auth_override=MEMBER)
            resp = client.post("/auth/email/request-confirmation")
        assert resp.status_code == 503

    def test_cross_tenant_isolation(self):
        """member_id vem SEMPRE do token JWT (servidor), nunca do corpo da requisicao."""
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "mem-A",
            "email_enc": "enc",
            "name_enc": None,
            "email_confirmed_at": None,
        }]
        with patch("api.routers.auth_email.create_client", return_value=sb), \
             patch("utils.security.decrypt", return_value="a@example.com"), \
             patch("services.email_service.send_confirmation_email", return_value=True):
            client = _make_client(auth_override={"sub": "mem-A", "plan": "free"})
            resp = client.post("/auth/email/request-confirmation")
        assert resp.status_code == 200
        # Verifica que o id usado na query eh o do token, nao de entrada externa
        eq_call = sb.table.return_value.select.return_value.eq.call_args
        assert eq_call[0] == ("id", "mem-A")


class TestConfirmEmailEndpoint:
    def test_valid_token_redirects_with_flag(self):
        with patch("services.email_service.verify_confirmation_token", return_value="mem-1"):
            client = _make_client()
            resp = client.get("/auth/email/confirm/valid-token-abc")
        assert resp.status_code == 302
        assert "email_confirmed=1" in resp.headers["location"]

    def test_invalid_token_returns_400_html(self):
        with patch("services.email_service.verify_confirmation_token", return_value=None):
            client = _make_client()
            resp = client.get("/auth/email/confirm/bad-token")
        assert resp.status_code == 400
        assert "text/html" in resp.headers.get("content-type", "")

    def test_oversized_token_returns_400_without_db_call(self):
        with patch("services.email_service.verify_confirmation_token") as mock_verify:
            client = _make_client()
            resp = client.get("/auth/email/confirm/" + "x" * 200)
        assert resp.status_code == 400
        mock_verify.assert_not_called()  # nunca chega ao banco

    def test_token_confirms_only_its_owner(self):
        """O token mapeia para um member_id fixo no banco.
        Nao ha como usar o token de A para confirmar o email de B."""
        with patch("services.email_service.verify_confirmation_token", return_value="mem-owner") as mv:
            client = _make_client()
            resp = client.get("/auth/email/confirm/token-for-owner")
        assert resp.status_code == 302
        mv.assert_called_once_with("token-for-owner")
        # O service usa o member_id retornado internamente — sem input externo influenciando
