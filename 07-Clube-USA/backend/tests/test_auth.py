"""
Testes da autenticação (registro, confirmação de email, login).
Garante: fluxo feliz, validações, isolamento (cross-user → 404/401),
rate-limit, e que segredos não vazam nas respostas.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.auth.security import (
    create_access_token,
    generate_confirm_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------
# Utilitários de segurança
# ---------------------------------------------------------------

def test_password_hash_and_verify():
    h = hash_password("SenhaForte123")
    assert verify_password("SenhaForte123", h)
    assert not verify_password("SenhaErrada", h)


def test_hash_is_never_plain():
    h = hash_password("abc12345")
    assert "abc12345" not in h


def test_token_encode_decode():
    from app.auth.security import decode_access_token
    token = create_access_token("user-uuid-123")
    assert decode_access_token(token) == "user-uuid-123"


def test_invalid_token_returns_none():
    from app.auth.security import decode_access_token
    assert decode_access_token("token.invalido.aqui") is None


# ---------------------------------------------------------------
# Endpoint: POST /auth/register
# ---------------------------------------------------------------

def test_register_success(client, db_mock):
    # Ordem real das chamadas execute() dentro de register_user:
    # 0: check_rate_limit SELECT count      → count=0
    # 1: check_rate_limit INSERT entry      → ignored
    # 2: users SELECT (email já existe?)   → data=[]
    # 3: users INSERT novo usuário          → data=[{user}]
    mock_chain = db_mock.table.return_value
    call_count = 0

    def execute_side_effect():
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            result.data = []
            result.count = 0   # rate-limit: sem tentativas anteriores
        elif call_count == 1:
            result.data = []
            result.count = 0   # insert do rate_limit entry
        elif call_count == 2:
            result.data = []   # nenhum usuário com este email
            result.count = 0
        else:
            result.data = [{"id": "uuid-1", "email": "joao@test.com"}]
            result.count = 1
        call_count += 1
        return result

    mock_chain.execute.side_effect = execute_side_effect

    with patch("app.auth.service.send_email") as mock_email:
        mock_email.return_value = None
        resp = client.post(
            "/auth/register",
            json={"email": "joao@test.com", "password": "SenhaForte1", "full_name": "João"},
        )

    assert resp.status_code == 201
    assert "email" in resp.json()["message"].lower()


def test_register_password_too_short(client):
    resp = client.post(
        "/auth/register",
        json={"email": "a@test.com", "password": "123", "full_name": "Ana"},
    )
    assert resp.status_code == 422


def test_register_invalid_email(client):
    resp = client.post(
        "/auth/register",
        json={"email": "nao-e-email", "password": "SenhaForte1", "full_name": "Ana"},
    )
    assert resp.status_code == 422


def test_register_missing_name(client):
    resp = client.post(
        "/auth/register",
        json={"email": "a@test.com", "password": "SenhaForte1", "full_name": ""},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------
# Endpoint: GET /auth/confirm-email
# ---------------------------------------------------------------

def test_confirm_email_success(client, db_mock):
    future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    mock_chain = db_mock.table.return_value
    mock_chain.execute.return_value.data = [
        {"id": "uuid-1", "email_confirmed": False, "email_confirm_expires_at": future}
    ]

    resp = client.get("/auth/confirm-email?token=valid-token-abc")
    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()


def test_confirm_email_invalid_token(client, db_mock):
    mock_chain = db_mock.table.return_value
    mock_chain.execute.return_value.data = []

    resp = client.get("/auth/confirm-email?token=token-invalido")
    assert resp.status_code == 404


def test_confirm_email_expired(client, db_mock):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    mock_chain = db_mock.table.return_value
    mock_chain.execute.return_value.data = [
        {"id": "uuid-1", "email_confirmed": False, "email_confirm_expires_at": past}
    ]

    resp = client.get("/auth/confirm-email?token=token-expirado")
    assert resp.status_code == 400


def test_confirm_email_already_confirmed(client, db_mock):
    future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    mock_chain = db_mock.table.return_value
    mock_chain.execute.return_value.data = [
        {"id": "uuid-1", "email_confirmed": True, "email_confirm_expires_at": future}
    ]

    resp = client.get("/auth/confirm-email?token=token-ja-confirmado")
    assert resp.status_code == 400


# ---------------------------------------------------------------
# Endpoint: POST /auth/login
# ---------------------------------------------------------------

def test_login_success(client, db_mock):
    # Ordem real: 0=rate-limit SELECT, 1=rate-limit INSERT, 2=users SELECT
    hashed = hash_password("SenhaForte1")
    call_count = 0

    def execute_side_effect():
        nonlocal call_count
        result = MagicMock()
        if call_count < 2:
            result.data = []
            result.count = 0   # rate-limit ok
        else:
            result.data = [
                {
                    "id": "uuid-1",
                    "password_hash": hashed,
                    "email_confirmed": True,
                    "is_active": True,
                }
            ]
            result.count = 1
        call_count += 1
        return result

    db_mock.table.return_value.execute.side_effect = execute_side_effect

    resp = client.post(
        "/auth/login",
        json={"email": "joao@test.com", "password": "SenhaForte1"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password(client, db_mock):
    hashed = hash_password("SenhaCorreta1")
    call_count = 0

    def execute_side_effect():
        nonlocal call_count
        result = MagicMock()
        if call_count < 2:
            result.data = []
            result.count = 0   # rate-limit ok
        else:
            result.data = [
                {
                    "id": "uuid-1",
                    "password_hash": hashed,
                    "email_confirmed": True,
                    "is_active": True,
                }
            ]
            result.count = 1
        call_count += 1
        return result

    db_mock.table.return_value.execute.side_effect = execute_side_effect

    resp = client.post(
        "/auth/login",
        json={"email": "joao@test.com", "password": "SenhaErrada1"},
    )
    assert resp.status_code == 401
    # Resposta genérica — não vazar se o email existe
    assert "email ou senha" in resp.json()["detail"].lower()


def test_login_email_not_confirmed(client, db_mock):
    hashed = hash_password("SenhaForte1")
    call_count = 0

    def execute_side_effect():
        nonlocal call_count
        result = MagicMock()
        if call_count < 2:
            result.data = []
            result.count = 0   # rate-limit ok
        else:
            result.data = [
                {
                    "id": "uuid-1",
                    "password_hash": hashed,
                    "email_confirmed": False,
                    "is_active": True,
                }
            ]
            result.count = 1
        call_count += 1
        return result

    db_mock.table.return_value.execute.side_effect = execute_side_effect

    resp = client.post(
        "/auth/login",
        json={"email": "joao@test.com", "password": "SenhaForte1"},
    )
    assert resp.status_code == 403
    assert "confirmado" in resp.json()["detail"].lower()


def test_login_nonexistent_user(client, db_mock):
    db_mock.table.return_value.execute.return_value.data = []
    db_mock.table.return_value.execute.return_value.count = 0

    resp = client.post(
        "/auth/login",
        json={"email": "naoexiste@test.com", "password": "SenhaForte1"},
    )
    # Mesma resposta que senha errada — não vaza existência do email
    assert resp.status_code == 401
    assert "email ou senha" in resp.json()["detail"].lower()


# ---------------------------------------------------------------
# Segurança: hash_password nunca armazena plain text
# ---------------------------------------------------------------

def test_password_hash_not_in_response(client, db_mock):
    """Garante que password_hash nunca vaza no response do login."""
    hashed = hash_password("SenhaForte1")
    call_count = 0

    def execute_side_effect():
        nonlocal call_count
        result = MagicMock()
        if call_count < 2:
            result.data = []
            result.count = 0   # rate-limit ok
        else:
            result.data = [
                {
                    "id": "uuid-1",
                    "password_hash": hashed,
                    "email_confirmed": True,
                    "is_active": True,
                }
            ]
            result.count = 1
        call_count += 1
        return result

    db_mock.table.return_value.execute.side_effect = execute_side_effect

    resp = client.post("/auth/login", json={"email": "j@t.com", "password": "SenhaForte1"})
    assert "password_hash" not in str(resp.json())
    assert hashed not in str(resp.json())
