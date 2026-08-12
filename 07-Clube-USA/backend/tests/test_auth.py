from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from gotrue.errors import AuthApiError

from app import dependencies
from app.main import app
from tests.conftest import _make_mock_supabase, make_token


# ── helpers ──────────────────────────────────────────────────────────────────

VALID_REGISTER = {
    "email": "novousuario@example.com",
    "password": "senhaSegura123",
    "first_name": "Ana",
    "last_name": "Costa",
    "zip_code": "90210",
}


def _client(mock: MagicMock) -> TestClient:
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    dependencies._supabase_client = original


# ── register ─────────────────────────────────────────────────────────────────


def test_register_success(client: TestClient) -> None:
    resp = client.post("/auth/register", json=VALID_REGISTER)
    assert resp.status_code == 201
    assert "email" in resp.json()["message"].lower()


def test_register_missing_first_name(client: TestClient) -> None:
    body = {**VALID_REGISTER, "first_name": ""}
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 422


def test_register_invalid_email(client: TestClient) -> None:
    body = {**VALID_REGISTER, "email": "not-an-email"}
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 422


def test_register_invalid_zip(client: TestClient) -> None:
    body = {**VALID_REGISTER, "zip_code": "ABCDE"}
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 422


def test_register_short_password(client: TestClient) -> None:
    body = {**VALID_REGISTER, "password": "abc"}
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 422


def test_register_zip_plus4_valid(client: TestClient) -> None:
    body = {**VALID_REGISTER, "zip_code": "10001-1234"}
    resp = client.post("/auth/register", json=body)
    assert resp.status_code == 201


def test_register_duplicate_email(client: TestClient) -> None:
    mock = _make_mock_supabase(
        register_raises=AuthApiError("User already registered", 400, "")
    )
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.post("/auth/register", json=VALID_REGISTER)
    dependencies._supabase_client = original

    assert resp.status_code == 400
    assert "cadastrado" in resp.json()["detail"].lower()


# ── login ─────────────────────────────────────────────────────────────────────


def test_login_success(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "senhaSegura123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    mock = _make_mock_supabase(
        login_raises=AuthApiError("Invalid login credentials", 401, "")
    )
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "errada"}
    )
    dependencies._supabase_client = original

    assert resp.status_code == 401
    assert "senha" in resp.json()["detail"].lower() or "email" in resp.json()["detail"].lower()


def test_login_email_not_confirmed(client: TestClient) -> None:
    mock = _make_mock_supabase(login_session=None)
    mock.auth.sign_in_with_password.return_value = MagicMock(session=None)
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "senhaSegura123"}
    )
    dependencies._supabase_client = original

    assert resp.status_code == 403


# ── refresh ───────────────────────────────────────────────────────────────────


def test_refresh_success(client: TestClient) -> None:
    resp = client.post("/auth/refresh", json={"refresh_token": "some-refresh-token"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_invalid_token(client: TestClient) -> None:
    mock = _make_mock_supabase(
        refresh_raises=AuthApiError("Invalid refresh token", 401, "")
    )
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.post("/auth/refresh", json={"refresh_token": "invalid"})
    dependencies._supabase_client = original

    assert resp.status_code in (400, 401)


# ── logout ────────────────────────────────────────────────────────────────────


def test_logout_success(client: TestClient, auth_headers: dict) -> None:
    resp = client.post("/auth/logout", headers=auth_headers)
    assert resp.status_code == 200


def test_logout_without_token(client: TestClient) -> None:
    resp = client.post("/auth/logout")
    assert resp.status_code == 403


def test_logout_expired_token(client: TestClient) -> None:
    expired_token = make_token(expired=True)
    resp = client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp.status_code == 401
