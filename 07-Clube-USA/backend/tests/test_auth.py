"""
Testes unitários de autenticação — Clube USA Fase 0.1

Estratégia: os clientes Supabase são mockados. Não é necessário
um projeto Supabase real para rodar estes testes.
"""
import os
import sys
from unittest.mock import MagicMock, patch

# Configura env vars antes de qualquer import do app
_TEST_JWT_SECRET = "test-jwt-secret-clube-usa-1234567890"
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", _TEST_JWT_SECRET)
os.environ.setdefault("SITE_URL", "http://localhost:8000")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt
import pytest
from fastapi.testclient import TestClient


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_token(user_id: str, secret: str = _TEST_JWT_SECRET) -> str:
    return jwt.encode(
        {"sub": user_id, "exp": 9_999_999_999},
        secret,
        algorithm="HS256",
    )


def _make_mock_user(uid="uid-123", email="test@clubeusa.com", confirmed=True):
    u = MagicMock()
    u.id = uid
    u.email = email
    u.email_confirmed_at = "2024-01-01T00:00:00Z" if confirmed else None
    return u


def _make_mock_session(uid="uid-123"):
    s = MagicMock()
    s.access_token = _make_token(uid)
    s.refresh_token = "refresh-abc"
    s.expires_in = 3600
    return s


# ─── Fixture: clientes mockados ───────────────────────────────────────────────

@pytest.fixture()
def mock_clients():
    mock_user_client = MagicMock()
    mock_admin_client = MagicMock()
    with (
        patch("routers.auth.get_user_client", return_value=mock_user_client),
        patch("routers.auth.get_admin_client", return_value=mock_admin_client),
        patch("database.get_user_client", return_value=mock_user_client),
        patch("database.get_admin_client", return_value=mock_admin_client),
    ):
        yield mock_user_client, mock_admin_client


@pytest.fixture()
def client(mock_clients):
    from main import app
    return TestClient(app, raise_server_exceptions=False)


# ─── /api/status ─────────────────────────────────────────────────────────────

def test_status(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Register ────────────────────────────────────────────────────────────────

def test_register_success(client, mock_clients):
    mock_user_client, mock_admin_client = mock_clients
    mock_user_client.auth.sign_up.return_value = MagicMock(
        user=_make_mock_user()
    )
    mock_admin_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

    r = client.post(
        "/api/auth/register",
        json={
            "email": "novo@clubeusa.com",
            "password": "senhaSegura123",
            "full_name": "João da Silva",
            "us_state": "FL",
            "city": "Miami",
        },
    )
    assert r.status_code == 201
    assert "email" in r.json()["message"].lower() or "cadastro" in r.json()["message"].lower()


def test_register_weak_password_rejected(client, mock_clients):
    r = client.post(
        "/api/auth/register",
        json={
            "email": "test@clubeusa.com",
            "password": "abc",
            "full_name": "Teste",
        },
    )
    assert r.status_code == 422


def test_register_invalid_email_rejected(client, mock_clients):
    r = client.post(
        "/api/auth/register",
        json={
            "email": "nao-e-email",
            "password": "senhaSegura123",
            "full_name": "Teste",
        },
    )
    assert r.status_code == 422


def test_register_empty_name_rejected(client, mock_clients):
    r = client.post(
        "/api/auth/register",
        json={
            "email": "test@clubeusa.com",
            "password": "senhaSegura123",
            "full_name": "   ",
        },
    )
    assert r.status_code == 422


def test_register_supabase_error_does_not_leak_email_existence(client, mock_clients):
    """Resposta genérica mesmo quando o email já existe (evita enumeração)."""
    mock_user_client, _ = mock_clients
    mock_user_client.auth.sign_up.side_effect = Exception("User already registered")

    r = client.post(
        "/api/auth/register",
        json={
            "email": "existing@clubeusa.com",
            "password": "senhaSegura123",
            "full_name": "Teste",
        },
    )
    # Deve retornar mensagem genérica, não erro 409 que confirmaria existência
    assert r.status_code == 201
    assert "email" in r.json()["message"].lower() or "confirmação" in r.json()["message"].lower()


# ─── Login ───────────────────────────────────────────────────────────────────

def test_login_success_sets_cookie(client, mock_clients):
    mock_user_client, _ = mock_clients
    mock_user_client.auth.sign_in_with_password.return_value = MagicMock(
        session=_make_mock_session(),
        user=_make_mock_user(),
    )

    r = client.post(
        "/api/auth/login",
        json={"email": "test@clubeusa.com", "password": "senhaSegura123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.cookies
    assert r.json()["email_confirmed"] is True


def test_login_unconfirmed_email_flag(client, mock_clients):
    mock_user_client, _ = mock_clients
    mock_user_client.auth.sign_in_with_password.return_value = MagicMock(
        session=_make_mock_session(),
        user=_make_mock_user(confirmed=False),
    )

    r = client.post(
        "/api/auth/login",
        json={"email": "test@clubeusa.com", "password": "senhaSegura123"},
    )
    assert r.status_code == 200
    assert r.json()["email_confirmed"] is False


def test_login_wrong_credentials(client, mock_clients):
    mock_user_client, _ = mock_clients
    mock_user_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    r = client.post(
        "/api/auth/login",
        json={"email": "test@clubeusa.com", "password": "senhaErrada"},
    )
    assert r.status_code == 401


# ─── GET /me ─────────────────────────────────────────────────────────────────

def test_get_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_get_me_invalid_token(client):
    r = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer token.invalido.aqui"},
    )
    assert r.status_code == 401


def test_get_me_success(client, mock_clients):
    uid = "uid-abc-123"
    token = _make_token(uid)
    _, mock_admin_client = mock_clients

    mock_admin_client.auth.admin.get_user_by_id.return_value = MagicMock(
        user=_make_mock_user(uid=uid, email="me@clubeusa.com")
    )
    mock_admin_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"id": uid, "full_name": "Maria Silva", "us_state": "CA", "city": "Los Angeles"}
    )

    r = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == uid
    assert body["full_name"] == "Maria Silva"
    assert body["email"] == "me@clubeusa.com"


def test_get_me_uses_token_user_id_not_request_param(client, mock_clients):
    """
    Isolamento multi-tenant: o user_id vem SEMPRE do JWT verificado
    no servidor, nunca de parâmetros do cliente. Este teste verifica que
    o endpoint /me retorna o perfil do usuário DO TOKEN, ignorando qualquer
    tentativa de injetar outro user_id via query string ou body.
    """
    uid_real = "uid-real"
    token = _make_token(uid_real)
    _, mock_admin_client = mock_clients

    mock_admin_client.auth.admin.get_user_by_id.return_value = MagicMock(
        user=_make_mock_user(uid=uid_real, email="real@clubeusa.com")
    )
    mock_admin_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"id": uid_real, "full_name": "Usuário Real", "us_state": None, "city": None}
    )

    # Tenta passar outro user_id via query param (deve ser ignorado)
    r = client.get(
        "/api/auth/me?user_id=uid-outro",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    # Verifica que o admin foi chamado com o uid do TOKEN, não com "uid-outro"
    mock_admin_client.auth.admin.get_user_by_id.assert_called_once_with(uid_real)


# ─── Confirm email ───────────────────────────────────────────────────────────

def test_confirm_email_success(client, mock_clients):
    mock_user_client, _ = mock_clients
    mock_user_client.auth.verify_otp.return_value = MagicMock(
        user=_make_mock_user()
    )

    r = client.post(
        "/api/auth/confirm",
        json={"token_hash": "hash-valido-aqui", "type": "email"},
    )
    assert r.status_code == 200
    assert "confirmado" in r.json()["message"].lower()


def test_confirm_email_invalid_token(client, mock_clients):
    mock_user_client, _ = mock_clients
    mock_user_client.auth.verify_otp.side_effect = Exception("OTP has expired or is invalid")

    r = client.post(
        "/api/auth/confirm",
        json={"token_hash": "hash-invalido", "type": "email"},
    )
    assert r.status_code == 400


def test_confirm_email_invalid_type(client, mock_clients):
    r = client.post(
        "/api/auth/confirm",
        json={"token_hash": "qualquer", "type": "tipo_desconhecido"},
    )
    assert r.status_code == 400


# ─── Logout ──────────────────────────────────────────────────────────────────

def test_logout_clears_cookie(client, mock_clients):
    uid = "uid-logout"
    token = _make_token(uid)

    r = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    # Cookie deve ser deletado (Set-Cookie com max-age=0 ou expires no passado)
    set_cookie = r.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


def test_logout_unauthenticated(client):
    r = client.post("/api/auth/logout")
    assert r.status_code == 401
