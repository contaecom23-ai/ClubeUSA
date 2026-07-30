"""
Testes de integração: perfil de usuário.

Inclui teste de isolamento multi-tenant: usuário A não pode acessar dados de B.
Requer TEST_DATABASE_URL — veja conftest.py.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _full_register_and_login(client: AsyncClient, db: AsyncSession, email: str) -> str:
    """Registra, confirma email e retorna access_token."""
    from sqlalchemy import select
    from app.models import User

    await client.post("/auth/register", json={"email": email, "password": "Senha123", "full_name": "Test User"})
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    await client.get(f"/auth/confirm-email/{user.email_confirm_token}")
    login_r = await client.post("/auth/login", json={"email": email, "password": "Senha123"})
    return login_r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Perfil ───────────────────────────────────────────────────────────────────

async def test_get_profile(client: AsyncClient, db: AsyncSession):
    token = await _full_register_and_login(client, db, "profile@example.com")
    r = await client.get("/users/me", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_email_confirmed"] is True


async def test_get_profile_without_token(client: AsyncClient):
    r = await client.get("/users/me")
    assert r.status_code == 403  # HTTPBearer retorna 403 quando header ausente


async def test_get_profile_invalid_token(client: AsyncClient):
    r = await client.get("/users/me", headers=_auth("token.invalido.qualquer"))
    assert r.status_code == 401


async def test_update_profile_success(client: AsyncClient, db: AsyncSession):
    token = await _full_register_and_login(client, db, "update@example.com")
    r = await client.patch("/users/me", headers=_auth(token), json={
        "full_name": "Nome Atualizado",
        "state_us": "FL",
        "zip_code": "33101",
        "city": "Miami",
        "phone": "5551234567",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["full_name"] == "Nome Atualizado"
    assert data["state_us"] == "FL"
    assert data["zip_code"] == "33101"


async def test_update_profile_invalid_zip(client: AsyncClient, db: AsyncSession):
    token = await _full_register_and_login(client, db, "ziptest@example.com")
    r = await client.patch("/users/me", headers=_auth(token), json={"zip_code": "123"})
    assert r.status_code == 422


async def test_update_profile_invalid_state(client: AsyncClient, db: AsyncSession):
    token = await _full_register_and_login(client, db, "statetest@example.com")
    r = await client.patch("/users/me", headers=_auth(token), json={"state_us": "FLO"})
    assert r.status_code == 422


# ─── Isolamento multi-tenant ───────────────────────────────────────────────────
# /users/me sempre retorna O PRÓPRIO usuário (user_id vem do JWT, não do input).
# Garantir que o token do usuário A nunca retorne dados do usuário B.

async def test_profile_isolation(client: AsyncClient, db: AsyncSession):
    token_a = await _full_register_and_login(client, db, "usera@example.com")
    token_b = await _full_register_and_login(client, db, "userb@example.com")

    profile_a = (await client.get("/users/me", headers=_auth(token_a))).json()
    profile_b = (await client.get("/users/me", headers=_auth(token_b))).json()

    assert profile_a["email"] == "usera@example.com"
    assert profile_b["email"] == "userb@example.com"
    assert profile_a["id"] != profile_b["id"]
    # Token A não retorna dados de B
    assert profile_a["email"] != profile_b["email"]
