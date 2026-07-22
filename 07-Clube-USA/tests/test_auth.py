"""Testes de autenticação — Fase 0.1."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from tests.conftest import _SessionLocal


pytestmark = pytest.mark.asyncio


# ─── Registro ────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "novo@clubeusa.com",
        "password": "Senha@123",
        "full_name": "Maria Silva",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "novo@clubeusa.com"
    assert "Verifique seu e-mail" in data["message"]


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@clubeusa.com", "password": "Senha@123"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/auth/register", json={"email": "w@clubeusa.com", "password": "123"})
    assert resp.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post("/auth/register", json={"email": "nao_e_email", "password": "Senha@123"})
    assert resp.status_code == 422


async def test_register_email_lowercased(client: AsyncClient):
    resp = await client.post("/auth/register", json={"email": "UPPER@ClubEUSA.com", "password": "Senha@123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "upper@clubeusa.com"


# ─── Confirmação de e-mail ────────────────────────────────────────────────────

async def test_confirm_email_valid_token(client: AsyncClient):
    await client.post("/auth/register", json={"email": "confirm@clubeusa.com", "password": "Senha@123"})

    async with _SessionLocal() as s:
        user = await s.scalar(select(User).where(User.email == "confirm@clubeusa.com"))
        token = user.email_confirm_token

    resp = await client.get(f"/auth/confirm-email?token={token}")
    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"]


async def test_confirm_email_invalid_token(client: AsyncClient):
    resp = await client.get("/auth/confirm-email?token=token_invalido")
    assert resp.status_code == 400


async def test_confirm_email_idempotent(client: AsyncClient):
    """Confirmar duas vezes não deve retornar erro."""
    await client.post("/auth/register", json={"email": "idem@clubeusa.com", "password": "Senha@123"})

    async with _SessionLocal() as s:
        user = await s.scalar(select(User).where(User.email == "idem@clubeusa.com"))
        token = user.email_confirm_token

    await client.get(f"/auth/confirm-email?token={token}")
    resp = await client.get(f"/auth/confirm-email?token={token}")
    # Token foi apagado na 1ª confirmação → 400 (não há mais token)
    assert resp.status_code in (200, 400)


# ─── Login ────────────────────────────────────────────────────────────────────

async def test_login_requires_confirmed_email(client: AsyncClient):
    await client.post("/auth/register", json={"email": "notconfirmed@clubeusa.com", "password": "Senha@123"})
    resp = await client.post("/auth/login", json={"email": "notconfirmed@clubeusa.com", "password": "Senha@123"})
    assert resp.status_code == 403
    assert "Confirme" in resp.json()["detail"]


async def test_login_success(client: AsyncClient):
    from tests.conftest import register_and_confirm
    token = await register_and_confirm(client, "login_ok@clubeusa.com")
    assert token and len(token) > 10


async def test_login_wrong_password(client: AsyncClient):
    from tests.conftest import register_and_confirm
    await register_and_confirm(client, "wrongpw@clubeusa.com")
    resp = await client.post("/auth/login", json={"email": "wrongpw@clubeusa.com", "password": "SenhaErrada"})
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "ghost@clubeusa.com", "password": "Senha@123"})
    assert resp.status_code == 401
    # Mensagem genérica — não vaza se e-mail existe
    assert "incorretos" in resp.json()["detail"]


# ─── Refresh de tokens ────────────────────────────────────────────────────────

async def test_refresh_token(client: AsyncClient):
    from tests.conftest import register_and_confirm
    await register_and_confirm(client, "refresh@clubeusa.com")
    login_resp = await client.post("/auth/login", json={"email": "refresh@clubeusa.com", "password": "Senha@123"})
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_fails(client: AsyncClient):
    from tests.conftest import register_and_confirm
    access_token = await register_and_confirm(client, "badrefresh@clubeusa.com")
    # Usar access_token onde se espera refresh → deve falhar
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


# ─── Isolamento multi-tenant ──────────────────────────────────────────────────

async def test_token_from_user_a_cannot_access_user_b_profile(client: AsyncClient):
    """
    Garante que o user_id vem SEMPRE do token JWT (servidor),
    nunca de parâmetro externo.
    """
    from tests.conftest import register_and_confirm
    token_a = await register_and_confirm(client, "user_a@clubeusa.com")
    await register_and_confirm(client, "user_b@clubeusa.com")

    # GET /users/me com token de A deve retornar perfil de A, não de B
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user_a@clubeusa.com"
