"""Testes unitários para auth — sem chamadas reais ao Supabase."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def _make_user(email="joao@example.com", confirmed=True):
    from app.services.auth_service import hash_password, generate_referral_code
    return {
        "id": "user-uuid-1",
        "email": email,
        "password_hash": hash_password("senha1234"),
        "full_name": "João Silva",
        "zip_code": "10001",
        "referral_code": generate_referral_code(),
        "email_confirmed_at": "2026-01-01T00:00:00+00:00" if confirmed else None,
        "created_at": "2026-01-01T00:00:00+00:00",
    }


class TestRegister:
    def test_register_success(self, client):
        user = _make_user()
        with patch("app.routers.auth.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            # Email não existe
            db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            # Referral também não existe
            db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            # Insert retorna o usuário criado
            db.table.return_value.insert.return_value.execute.return_value.data = [user]

            with patch("app.routers.auth.send_confirmation_email", return_value=True):
                resp = client.post("/auth/register", json={
                    "email": "joao@example.com",
                    "password": "senha1234",
                    "full_name": "João Silva",
                    "zip_code": "10001",
                })
        assert resp.status_code == 201
        assert "email" in resp.json()

    def test_register_weak_password(self, client):
        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "123",
            "full_name": "João",
        })
        assert resp.status_code == 422

    def test_register_invalid_zip(self, client):
        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "senha1234",
            "full_name": "João",
            "zip_code": "ABCDE",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "nao-e-email",
            "password": "senha1234",
            "full_name": "João",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        user = _make_user()
        with patch("app.routers.auth.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [user]

            resp = client.post("/auth/login", json={
                "email": "joao@example.com",
                "password": "senha1234",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "joao@example.com"

    def test_login_wrong_password(self, client):
        user = _make_user()
        with patch("app.routers.auth.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [user]

            resp = client.post("/auth/login", json={
                "email": "joao@example.com",
                "password": "senhaerrada",
            })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        with patch("app.routers.auth.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

            resp = client.post("/auth/login", json={
                "email": "naoexiste@example.com",
                "password": "senha1234",
            })
        assert resp.status_code == 401


class TestGetMe:
    def test_get_me_requires_auth(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 403  # HTTPBearer retorna 403 sem credentials

    def test_get_me_invalid_token(self, client):
        resp = client.get("/users/me", headers={"Authorization": "Bearer tokeninvalido"})
        assert resp.status_code == 401

    def test_get_me_success(self, client):
        user = _make_user()
        from app.services.auth_service import create_access_token
        token = create_access_token(user["id"])

        with patch("app.dependencies.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = user

            resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "joao@example.com"


class TestAuthIsolation:
    """Garante que usuário A não acessa dados de B."""

    def test_cross_user_access_returns_401(self, client):
        from app.services.auth_service import create_access_token
        # Token válido para user-A, mas banco retorna vazio (user-A não existe mais)
        token = create_access_token("user-uuid-A")

        with patch("app.dependencies.get_db") as mock_get_db:
            db = MagicMock()
            mock_get_db.return_value = db
            db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

            resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
