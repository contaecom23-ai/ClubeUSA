# tests/test_email_auth.py — Fase 0.1: email auth
#
# Executa com: pytest tests/test_email_auth.py -v
# (necessita SUPABASE_URL, SUPABASE_SERVICE_KEY, ENCRYPTION_KEY, JWT_SECRET no .env)

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "api"))


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key-must-be-32chars!!")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-32chars-minimum!!")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("APP_URL", "https://clubeusa.com")


# ── security.py ──────────────────────────────────────────────

class TestPasswordHash:
    def test_hash_and_verify(self):
        from utils.security import hash_password, verify_password
        pw = "SecurePass123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed)

    def test_wrong_password_fails(self):
        from utils.security import hash_password, verify_password
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_unique_per_call(self):
        from utils.security import hash_password
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt salt randomizado

    def test_generate_email_token_length(self):
        from utils.security import generate_email_token
        token = generate_email_token()
        assert len(token) >= 32

    def test_generate_email_token_unique(self):
        from utils.security import generate_email_token
        tokens = {generate_email_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_create_web_token_7_days(self):
        from utils.security import create_web_token
        import jose.jwt as _jwt
        token = create_web_token("member-123", "free")
        payload = _jwt.decode(
            token,
            os.environ["JWT_SECRET"],
            algorithms=["HS256"],
        )
        diff = payload["exp"] - payload["iat"]
        # 7 days = 604800 seconds ±60s
        assert abs(diff - 7 * 24 * 3600) < 60


# ── email_service.py ─────────────────────────────────────────

class TestEmailService:
    def test_send_confirmation_logs_in_dev(self, caplog):
        import logging
        from services.email_service import send_confirmation_email
        with caplog.at_level(logging.INFO, logger="email_service"):
            result = send_confirmation_email("user@test.com", "Test User", "tok123")
        assert result is True
        assert "DEV" in caplog.text

    def test_send_welcome_logs_in_dev(self, caplog):
        import logging
        from services.email_service import send_welcome_email
        with caplog.at_level(logging.INFO, logger="email_service"):
            result = send_welcome_email("user@test.com", "Test User", "REF123")
        assert result is True

    def test_send_no_api_key_in_prod(self, monkeypatch, caplog):
        import logging
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
        from services import email_service
        import importlib
        importlib.reload(email_service)
        with caplog.at_level(logging.INFO, logger="email_service"):
            result = email_service.send_confirmation_email("user@test.com", "U", "tok")
        assert result is True  # fallback para log
        monkeypatch.setenv("ENVIRONMENT", "development")


# ── Endpoints (FastAPI TestClient) ───────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    with (
        patch("supabase.create_client"),
        patch("routers.news.router"),
        patch("routers.forum.router"),
        patch("routers.assistant.router"),
    ):
        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)
        return TestClient(main_mod.app)


def _make_sb_mock(existing=None, insert_id="member-uuid-123", member_data=None):
    """Constrói mock do supabase para os testes de endpoint."""
    sb = MagicMock()
    tbl = MagicMock()
    sb.table.return_value = tbl

    select_chain = MagicMock()
    tbl.select.return_value = select_chain
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = MagicMock(data=existing or [])

    insert_chain = MagicMock()
    tbl.insert.return_value = insert_chain
    insert_chain.execute.return_value = MagicMock(data=[{"id": insert_id}])

    update_chain = MagicMock()
    tbl.update.return_value = update_chain
    update_chain.eq.return_value = update_chain
    update_chain.execute.return_value = MagicMock(data=[])

    return sb


class TestRegisterEmailEndpoint:
    @patch("services.email_service.send_confirmation_email", return_value=True)
    @patch("routers.email_auth._sb")
    def test_register_new_user(self, mock_sb, mock_send):
        from fastapi.testclient import TestClient
        sb = _make_sb_mock(existing=[])
        mock_sb.return_value = sb

        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/register-email", json={
            "email": "novo@test.com",
            "password": "Senha1234",
            "name": "Fulano",
            "language": "pt",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email_confirmed"] is False
        assert "member_id" in data
        assert mock_send.called

    @patch("services.email_service.send_confirmation_email", return_value=True)
    @patch("routers.email_auth._sb")
    def test_register_duplicate_confirmed(self, mock_sb, mock_send):
        from fastapi.testclient import TestClient
        sb = _make_sb_mock(existing=[{"id": "abc", "email_confirmed": True}])
        mock_sb.return_value = sb

        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/register-email", json={
            "email": "existe@test.com",
            "password": "Senha1234",
        })
        assert resp.status_code == 409

    def test_register_weak_password(self):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/register-email", json={
            "email": "user@test.com",
            "password": "123",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/register-email", json={
            "email": "nao-e-email",
            "password": "Senha1234",
        })
        assert resp.status_code == 422

    def test_register_invalid_language(self):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/register-email", json={
            "email": "user@test.com",
            "password": "Senha1234",
            "language": "fr",
        })
        assert resp.status_code == 422


class TestConfirmEmailEndpoint:
    @patch("routers.email_auth._sb")
    def test_confirm_valid_token(self, mock_sb):
        from datetime import datetime, timedelta, timezone
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "email_confirmed": False,
            "email_token_expires_at": future,
            "referral_code": "ABCD1234",
            "name_enc": "",
        }])
        # second call (welcome email lookup) also returns data
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "m-123", "email_confirmed": False, "email_token_expires_at": future,
                   "referral_code": "ABCD1234", "name_enc": "", "email_enc": ""}]
        )
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch("services.email_service.send_welcome_email", return_value=True):
            resp = client.get("/auth/confirm-email?token=validtoken")
        assert resp.status_code == 200
        assert resp.json()["confirmed"] is True

    @patch("routers.email_auth._sb")
    def test_confirm_invalid_token(self, mock_sb):
        sb = _make_sb_mock(existing=[])
        mock_sb.return_value = sb

        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/auth/confirm-email?token=doesnotexist")
        assert resp.status_code == 404

    @patch("routers.email_auth._sb")
    def test_confirm_expired_token(self, mock_sb):
        from datetime import datetime, timedelta, timezone
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "email_confirmed": False,
            "email_token_expires_at": past,
            "referral_code": "ABCD1234",
        }])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/auth/confirm-email?token=expiredtoken")
        assert resp.status_code == 400
        assert "expirado" in resp.json()["detail"].lower()


class TestLoginEndpoint:
    @patch("routers.email_auth._sb")
    def test_login_success(self, mock_sb):
        from utils.security import hash_password
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        pw_hash = hash_password("Senha1234")
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "plan": "free",
            "status": "active",
            "password_hash": pw_hash,
            "email_confirmed": True,
        }])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "Senha1234",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["expires_in_days"] == 7

    @patch("routers.email_auth._sb")
    def test_login_wrong_password(self, mock_sb):
        from utils.security import hash_password
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        pw_hash = hash_password("correct")
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "plan": "free",
            "status": "active",
            "password_hash": pw_hash,
            "email_confirmed": True,
        }])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "wrong",
        })
        assert resp.status_code == 401

    @patch("routers.email_auth._sb")
    def test_login_unconfirmed_email(self, mock_sb):
        from utils.security import hash_password
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        pw_hash = hash_password("Senha1234")
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "plan": "free",
            "status": "active",
            "password_hash": pw_hash,
            "email_confirmed": False,
        }])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "Senha1234",
        })
        assert resp.status_code == 403

    @patch("routers.email_auth._sb")
    def test_login_nonexistent_user(self, mock_sb):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        sb = _make_sb_mock(existing=[])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/login", json={
            "email": "naoexiste@test.com",
            "password": "Senha1234",
        })
        assert resp.status_code == 401  # 401, nao 404 (nao vazar existencia)

    @patch("routers.email_auth._sb")
    def test_login_banned_user(self, mock_sb):
        from utils.security import hash_password
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        pw_hash = hash_password("Senha1234")
        sb = _make_sb_mock(existing=[{
            "id": "m-123",
            "plan": "free",
            "status": "banned",
            "password_hash": pw_hash,
            "email_confirmed": True,
        }])
        mock_sb.return_value = sb

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.post("/auth/login", json={
            "email": "banned@test.com",
            "password": "Senha1234",
        })
        assert resp.status_code == 403


class TestUpdateProfileEndpoint:
    @patch("routers.email_auth._sb")
    def test_update_profile_success(self, mock_sb):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        from utils.security import create_web_token

        sb = _make_sb_mock()
        mock_sb.return_value = sb

        token = create_web_token("m-123", "free")

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.put(
            "/member/profile",
            json={"name": "Novo Nome", "state": "FL", "zip_code": "33101"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Perfil atualizado com sucesso."

    def test_update_profile_unauthenticated(self):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.put("/member/profile", json={"name": "Teste"})
        assert resp.status_code == 401

    @patch("routers.email_auth._sb")
    def test_update_profile_invalid_zip(self, mock_sb):
        from fastapi.testclient import TestClient
        from routers.email_auth import router
        from fastapi import FastAPI
        from utils.security import create_web_token

        token = create_web_token("m-123", "free")

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.put(
            "/member/profile",
            json={"zip_code": "naozip"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
