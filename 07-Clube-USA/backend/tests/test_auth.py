"""Testes de integração das rotas de auth — banco mockado."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# conftest.py define env vars antes deste import
import database
from main import app
from security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_user_row(
    *,
    email="joao@example.com",
    first_name="João",
    last_name="Silva",
    email_confirmed=True,
    is_active=True,
    password="senha123",
):
    return {
        "id": uuid.uuid4(),
        "email": email,
        "password_hash": hash_password(password),
        "first_name": first_name,
        "last_name": last_name,
        "phone": None,
        "zip_code": "10001",
        "city": "New York",
        "state": "NY",
        "email_confirmed": email_confirmed,
        "email_confirm_token_expires_at": datetime.now(timezone.utc) + timedelta(hours=23),
        "is_active": is_active,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# /status
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_register_success(mock_pool, mock_conn):
    mock_conn.fetchrow = AsyncMock(return_value=None)  # email não existe
    mock_conn.execute = AsyncMock()

    with patch.object(database, "pool", mock_pool), \
         patch("main.send_confirmation_email", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/register", json={
                "email": "novo@example.com",
                "password": "Senha@123",
                "first_name": "Maria",
                "last_name": "Souza",
            })

    assert resp.status_code == 201
    assert "email" in resp.json()["message"].lower()


@pytest.mark.anyio
async def test_register_duplicate_email_same_message(mock_pool, mock_conn):
    # Quando email existe, retorna mesma mensagem (não vaza existência)
    mock_conn.fetchrow = AsyncMock(return_value={"id": uuid.uuid4()})

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/register", json={
                "email": "existente@example.com",
                "password": "Senha@123",
                "first_name": "Maria",
                "last_name": "Souza",
            })

    assert resp.status_code == 201  # mesmo status code — não revela duplicata


@pytest.mark.anyio
async def test_register_short_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "password": "123",
            "first_name": "A",
            "last_name": "B",
        })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_register_invalid_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "nao-e-email",
            "password": "Senha@123",
            "first_name": "X",
            "last_name": "Y",
        })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/confirm-email
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_confirm_email_success(mock_pool, mock_conn):
    token_expires = datetime.now(timezone.utc) + timedelta(hours=23)
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": uuid.uuid4(),
        "email_confirmed": False,
        "email_confirm_token_expires_at": token_expires,
    })
    mock_conn.execute = AsyncMock()

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/confirm-email", json={"token": "valid-token-abc"})

    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()


@pytest.mark.anyio
async def test_confirm_email_invalid_token(mock_pool, mock_conn):
    mock_conn.fetchrow = AsyncMock(return_value=None)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/confirm-email", json={"token": "token-invalido"})

    assert resp.status_code == 400


@pytest.mark.anyio
async def test_confirm_email_expired_token(mock_pool, mock_conn):
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": uuid.uuid4(),
        "email_confirmed": False,
        "email_confirm_token_expires_at": expired,
    })

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/confirm-email", json={"token": "expired-token"})

    assert resp.status_code == 400
    assert "expir" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_login_success(mock_pool, mock_conn):
    user = _make_user_row(password="Senha@123")
    mock_conn.fetchrow = AsyncMock(return_value=user)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "joao@example.com",
                "password": "Senha@123",
            })

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password(mock_pool, mock_conn):
    user = _make_user_row(password="senha-certa")
    mock_conn.fetchrow = AsyncMock(return_value=user)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "joao@example.com",
                "password": "senha-errada",
            })

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_found(mock_pool, mock_conn):
    mock_conn.fetchrow = AsyncMock(return_value=None)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "nao@existe.com",
                "password": "qualquer",
            })

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_inactive_user(mock_pool, mock_conn):
    user = _make_user_row(is_active=False, password="Senha@123")
    mock_conn.fetchrow = AsyncMock(return_value=user)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/login", json={
                "email": "joao@example.com",
                "password": "Senha@123",
            })

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_me_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # HTTPBearer retorna 403 sem header


@pytest.mark.anyio
async def test_get_me_invalid_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token.invalido"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_me_success(mock_pool, mock_conn):
    user_id = uuid.uuid4()
    token = create_access_token(str(user_id))

    user = _make_user_row()
    user["id"] = user_id
    mock_conn.fetchrow = AsyncMock(return_value=user)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "joao@example.com"
    assert body["email_confirmed"] is True


@pytest.mark.anyio
async def test_get_me_cross_tenant_returns_404(mock_pool, mock_conn):
    """Usuário com token válido mas id não existe no banco retorna 404, não vaza dados."""
    token = create_access_token(str(uuid.uuid4()))
    mock_conn.fetchrow = AsyncMock(return_value=None)

    with patch.object(database, "pool", mock_pool):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert resp.status_code == 404
