"""
Testes de autenticação: registro, confirmação de email, login, refresh, logout.
DB mockado via conftest.mock_db + dependency_overrides.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import make_result

REGISTER_PAYLOAD = {
    "email": "joao@example.com",
    "password": "senha123",
    "full_name": "João Silva",
}


# ── /auth/register ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client, mock_db):
    mock_db.execute.side_effect = [
        make_result([]),                                          # sem email duplicado
        make_result([{"id": "uuid-123", "email": "joao@example.com"}]),  # insert user
        make_result([{"user_id": "uuid-123"}]),                  # insert profile
    ]
    with patch("app.auth.service.send_confirmation_email", new_callable=AsyncMock):
        resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    # Não deve vazar tokens nem senha no retorno do registro
    assert "access_token" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_register_weak_password(client, mock_db):
    resp = await client.post("/auth/register", json={
        **REGISTER_PAYLOAD,
        "password": "abc",  # < 8 chars
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client, mock_db):
    resp = await client.post("/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "nao-e-um-email",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_name(client, mock_db):
    resp = await client.post("/auth/register", json={
        **REGISTER_PAYLOAD,
        "full_name": "   ",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client, mock_db):
    mock_db.execute.side_effect = [
        make_result([{"id": "existing-uuid"}]),  # email já existe
    ]
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


# ── /auth/confirm-email ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_email_success(client, mock_db):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    mock_db.execute.side_effect = [
        make_result([{
            "id": "uuid-123",
            "email_confirmed": False,
            "email_confirmation_expires_at": future,
        }]),
        make_result([{}]),  # update
    ]
    resp = await client.get("/auth/confirm-email?token=valid-token-abc")
    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_confirm_email_invalid_token(client, mock_db):
    mock_db.execute.side_effect = [make_result([])]  # token não existe
    resp = await client.get("/auth/confirm-email?token=token-invalido")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_confirm_email_expired_token(client, mock_db):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    mock_db.execute.side_effect = [
        make_result([{
            "id": "uuid-123",
            "email_confirmed": False,
            "email_confirmation_expires_at": past,
        }]),
    ]
    resp = await client.get("/auth/confirm-email?token=expired-token")
    assert resp.status_code == 400
    assert "expir" in resp.json()["detail"].lower()


# ── /auth/login ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client, mock_db):
    from app.security import hash_password
    hashed = hash_password("senha123")
    mock_db.execute.side_effect = [
        make_result([{
            "id": "uuid-123",
            "password_hash": hashed,
            "email_confirmed": True,
            "is_active": True,
        }]),
        make_result([{}]),  # insert refresh token
    ]
    resp = await client.post("/auth/login", json={"email": "joao@example.com", "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in_days"] == 7


@pytest.mark.asyncio
async def test_login_wrong_password(client, mock_db):
    from app.security import hash_password
    hashed = hash_password("senha-correta")
    mock_db.execute.side_effect = [
        make_result([{
            "id": "uuid-123",
            "password_hash": hashed,
            "email_confirmed": True,
            "is_active": True,
        }]),
    ]
    resp = await client.post("/auth/login", json={"email": "joao@example.com", "password": "senha-errada"})
    assert resp.status_code == 401
    # Mensagem genérica — não revelar se email existe
    assert "inválid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_email_not_confirmed(client, mock_db):
    from app.security import hash_password
    hashed = hash_password("senha123")
    mock_db.execute.side_effect = [
        make_result([{
            "id": "uuid-123",
            "password_hash": hashed,
            "email_confirmed": False,
            "is_active": True,
        }]),
    ]
    resp = await client.post("/auth/login", json={"email": "joao@example.com", "password": "senha123"})
    assert resp.status_code == 403
    assert "confirmad" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email(client, mock_db):
    mock_db.execute.side_effect = [make_result([])]
    resp = await client.post("/auth/login", json={"email": "naoexiste@example.com", "password": "qualquer"})
    assert resp.status_code == 401
    # Mesmo erro que senha errada — não revelar inexistência
    assert "inválid" in resp.json()["detail"].lower()


# ── /auth/refresh ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_success(client, mock_db):
    from app.security import generate_refresh_token
    plain, token_hash, expires = generate_refresh_token()
    mock_db.execute.side_effect = [
        make_result([{
            "id": "rt-uuid",
            "user_id": "uuid-123",
            "expires_at": expires.isoformat(),
            "used_at": None,
        }]),
        make_result([{}]),  # invalidar token antigo
        make_result([{}]),  # inserir novo token
    ]
    resp = await client.post("/auth/refresh", json={"refresh_token": plain})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    # Novo refresh token gerado (rotação)
    assert body["refresh_token"] != plain


@pytest.mark.asyncio
async def test_refresh_already_used_token(client, mock_db):
    from app.security import generate_refresh_token
    plain, _, expires = generate_refresh_token()
    mock_db.execute.side_effect = [
        make_result([{
            "id": "rt-uuid",
            "user_id": "uuid-123",
            "expires_at": expires.isoformat(),
            "used_at": datetime.now(timezone.utc).isoformat(),  # já usado
        }]),
    ]
    resp = await client.post("/auth/refresh", json={"refresh_token": plain})
    assert resp.status_code == 401
