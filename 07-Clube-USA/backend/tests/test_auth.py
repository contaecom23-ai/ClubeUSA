"""
Testes de integração: autenticação (registro, confirmação, login, refresh, logout).

Requer TEST_DATABASE_URL — veja conftest.py.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

pytestmark = pytest.mark.asyncio


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, email="test@example.com", password="Senha123", name="Test User"):
    return await client.post("/auth/register", json={"email": email, "password": password, "full_name": name})


async def _confirm(client: AsyncClient, db: AsyncSession, email="test@example.com"):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    return await client.get(f"/auth/confirm-email/{user.email_confirm_token}")


async def _login(client: AsyncClient, email="test@example.com", password="Senha123"):
    return await client.post("/auth/login", json={"email": email, "password": password})


# ─── Registro ─────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient, db: AsyncSession):
    r = await _register(client)
    assert r.status_code == 201
    data = r.json()
    assert "user_id" in data
    assert "email" not in data  # não vazar dados desnecessários


async def test_register_duplicate_email(client: AsyncClient, db: AsyncSession):
    await _register(client, email="dup@example.com")
    r = await _register(client, email="dup@example.com")
    assert r.status_code == 409


async def test_register_weak_password_no_digit(client: AsyncClient):
    r = await _register(client, password="semdigito", email="weak@example.com")
    assert r.status_code == 422


async def test_register_weak_password_too_short(client: AsyncClient):
    r = await _register(client, password="Ab1", email="short@example.com")
    assert r.status_code == 422


async def test_register_empty_name(client: AsyncClient):
    r = await _register(client, name="  ", email="noname@example.com")
    assert r.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    r = await client.post("/auth/register", json={"email": "nao-e-email", "password": "Senha123", "full_name": "Test"})
    assert r.status_code == 422


# ─── Confirmação de email ──────────────────────────────────────────────────────

async def test_confirm_email_success(client: AsyncClient, db: AsyncSession):
    await _register(client, email="confirm@example.com")
    r = await _confirm(client, db, "confirm@example.com")
    assert r.status_code == 200

    result = await db.execute(select(User).where(User.email == "confirm@example.com"))
    user = result.scalar_one()
    assert user.is_email_confirmed is True
    assert user.email_confirm_token is None


async def test_confirm_email_invalid_token(client: AsyncClient):
    r = await client.get("/auth/confirm-email/token-invalido-qualquer")
    assert r.status_code == 400


# ─── Login ────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, db: AsyncSession):
    await _register(client, email="login@example.com")
    await _confirm(client, db, "login@example.com")
    r = await _login(client, email="login@example.com")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    await _register(client, email="wrongpwd@example.com")
    await _confirm(client, db, "wrongpwd@example.com")
    r = await _login(client, email="wrongpwd@example.com", password="ErradoX9")
    assert r.status_code == 401


async def test_login_unconfirmed_email(client: AsyncClient, db: AsyncSession):
    await _register(client, email="unconf@example.com")
    # NÃO confirma — tenta login direto
    r = await _login(client, email="unconf@example.com")
    assert r.status_code == 403


async def test_login_nonexistent_user(client: AsyncClient):
    r = await _login(client, email="naoexiste@example.com")
    assert r.status_code == 401


# ─── Refresh e Logout ─────────────────────────────────────────────────────────

async def test_refresh_token(client: AsyncClient, db: AsyncSession):
    await _register(client, email="refresh@example.com")
    await _confirm(client, db, "refresh@example.com")
    login_r = await _login(client, email="refresh@example.com")
    old_refresh = login_r.json()["refresh_token"]

    r = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_data = r.json()
    assert new_data["refresh_token"] != old_refresh  # token rotacionado

    # Token antigo não pode mais ser usado
    r2 = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401


async def test_logout(client: AsyncClient, db: AsyncSession):
    await _register(client, email="logout@example.com")
    await _confirm(client, db, "logout@example.com")
    login_r = await _login(client, email="logout@example.com")
    refresh_tok = login_r.json()["refresh_token"]

    r = await client.post("/auth/logout", json={"refresh_token": refresh_tok})
    assert r.status_code == 200

    # Refresh após logout deve falhar
    r2 = await client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert r2.status_code == 401
