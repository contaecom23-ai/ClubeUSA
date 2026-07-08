"""
Testes da API de perfil — cobrindo:
  - Rota pública /health
  - Autenticação obrigatória
  - GET /profile (sucesso / não encontrado)
  - PUT /profile (sucesso / sem campos / validação)
  - Isolamento multi-tenant (owner SEMPRE do token)
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# conftest.py já setou as env vars antes deste import
from api.main import app

client = TestClient(app)

JWT_SECRET = "test-jwt-secret-32-chars-xxxxxxxxx!"


def _make_token(user_id: str = "user-abc", email: str = "joao@example.com") -> str:
    return jwt.encode(
        {"sub": user_id, "email": email, "aud": "authenticated"},
        JWT_SECRET,
        algorithm="HS256",
    )


def _auth(user_id: str = "user-abc") -> dict:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


_PROFILE_ROW = {
    "id": "user-abc",
    "first_name": "João",
    "last_name": "Silva",
    "phone": "5551234567",
    "zip_code": "10001",
    "city": "New York",
    "state": "NY",
    "country": "US",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
}


# ─── /health ─────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Autenticação ─────────────────────────────────────────────

def test_get_profile_no_token_returns_403():
    r = client.get("/profile")
    assert r.status_code == 403


def test_get_profile_invalid_token_returns_401():
    r = client.get("/profile", headers={"Authorization": "Bearer token.invalido.xxx"})
    assert r.status_code == 401


# ─── GET /profile ─────────────────────────────────────────────

def test_get_profile_success():
    mock_result = MagicMock()
    mock_result.data = _PROFILE_ROW

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        (db.table.return_value
           .select.return_value
           .eq.return_value
           .single.return_value
           .execute.return_value) = mock_result

        r = client.get("/profile", headers=_auth())

    assert r.status_code == 200
    data = r.json()
    assert data["first_name"] == "João"
    assert data["email"] == "joao@example.com"
    # updated_at não deve aparecer na resposta (não está em ProfileResponse)
    assert "updated_at" not in data


def test_get_profile_not_found_returns_404():
    mock_result = MagicMock()
    mock_result.data = None

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        (db.table.return_value
           .select.return_value
           .eq.return_value
           .single.return_value
           .execute.return_value) = mock_result

        r = client.get("/profile", headers=_auth())

    assert r.status_code == 404


# ─── PUT /profile ─────────────────────────────────────────────

def test_update_profile_success():
    updated = {**_PROFILE_ROW, "phone": "5559999999"}
    mock_result = MagicMock()
    mock_result.data = [updated]

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        (db.table.return_value
           .update.return_value
           .eq.return_value
           .execute.return_value) = mock_result

        r = client.put("/profile", json={"phone": "5559999999"}, headers=_auth())

    assert r.status_code == 200
    assert r.json()["phone"] == "5559999999"


def test_update_profile_empty_body_returns_400():
    r = client.put("/profile", json={}, headers=_auth())
    assert r.status_code == 400


def test_update_profile_invalid_zip_returns_422():
    r = client.put("/profile", json={"zip_code": "abc"}, headers=_auth())
    assert r.status_code == 422


def test_update_profile_invalid_state_returns_422():
    r = client.put("/profile", json={"state": "XX"}, headers=_auth())
    assert r.status_code == 422


def test_update_profile_valid_state_normalized():
    updated = {**_PROFILE_ROW, "state": "FL"}
    mock_result = MagicMock()
    mock_result.data = [updated]

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        (db.table.return_value
           .update.return_value
           .eq.return_value
           .execute.return_value) = mock_result

        r = client.put("/profile", json={"state": "fl"}, headers=_auth())

    assert r.status_code == 200


# ─── ISOLAMENTO MULTI-TENANT ──────────────────────────────────

def test_cross_tenant_isolation_put():
    """
    Mesmo que o cliente envie um id diferente no corpo,
    o eq() do update usa SEMPRE o user_id do token.
    """
    mock_result = MagicMock()
    mock_result.data = []  # simulando "not found" para o user-A no recurso de user-B

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        eq_mock = db.table.return_value.update.return_value.eq
        eq_mock.return_value.execute.return_value = mock_result

        client.put(
            "/profile",
            json={"first_name": "Hacker"},
            headers=_auth(user_id="user-A"),
        )

        # Garantia: o eq() foi chamado com o id do TOKEN, não com qualquer outro id
        eq_mock.assert_called_once_with("id", "user-A")


def test_cross_tenant_isolation_get():
    """
    GET /profile retorna apenas o perfil do usuário autenticado.
    """
    mock_result = MagicMock()
    mock_result.data = None

    with patch("api.routers.profiles.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        eq_mock = (db.table.return_value
                   .select.return_value
                   .eq)
        eq_mock.return_value.single.return_value.execute.return_value = mock_result

        client.get("/profile", headers=_auth(user_id="user-B"))

        eq_mock.assert_called_once_with("id", "user-B")
