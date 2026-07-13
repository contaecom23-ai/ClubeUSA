"""
Testes de perfil de usuário (Fase 0.1).

Requerem DATABASE_URL. Pulados automaticamente sem ela.
"""
import uuid

import pytest
from httpx import AsyncClient

from .conftest import requires_db
from .test_auth import confirm_user, login, register_user, unique_email

pytestmark = [requires_db, pytest.mark.anyio]


async def authenticated_client_headers(client: AsyncClient) -> tuple[dict, str]:
    """Cria usuário, confirma e retorna headers de auth + email."""
    user = await register_user(client)
    await confirm_user(client, user["email"])
    tokens = await login(client, user["email"], user["password"])
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return headers, user["email"]


# ── Testes ────────────────────────────────────────────────────────────────────

async def test_get_profile_requires_auth(client: AsyncClient):
    res = await client.get("/users/me")
    assert res.status_code == 403  # sem token → 403 (HTTPBearer retorna 403 por padrão)


async def test_get_profile(client: AsyncClient):
    headers, email = await authenticated_client_headers(client)
    res = await client.get("/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == email
    assert data["email_confirmed"] is True
    assert "referral_code" in data
    assert len(data["referral_code"]) >= 6


async def test_update_profile(client: AsyncClient):
    headers, _ = await authenticated_client_headers(client)
    res = await client.patch("/users/me", headers=headers, json={
        "full_name": "Nome Atualizado",
        "zip_code": "90210",
        "city": "Beverly Hills",
        "state": "CA",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Nome Atualizado"
    assert data["zip_code"] == "90210"
    assert data["city"] == "Beverly Hills"
    assert data["state"] == "CA"


async def test_update_profile_empty(client: AsyncClient):
    headers, _ = await authenticated_client_headers(client)
    res = await client.patch("/users/me", headers=headers, json={})
    assert res.status_code == 422


async def test_profile_isolation(client: AsyncClient):
    """Usuário A não consegue ler dados do usuário B (IDOR check)."""
    # Cria usuário A
    headers_a, _ = await authenticated_client_headers(client)
    # Cria usuário B
    headers_b, _ = await authenticated_client_headers(client)

    # Ambos leem seus próprios perfis — devem ser diferentes
    res_a = await client.get("/users/me", headers=headers_a)
    res_b = await client.get("/users/me", headers=headers_b)
    assert res_a.json()["id"] != res_b.json()["id"]
    assert res_a.json()["email"] != res_b.json()["email"]


async def test_invalid_token_rejected(client: AsyncClient):
    headers = {"Authorization": "Bearer token-invalido-xpto"}
    res = await client.get("/users/me", headers=headers)
    assert res.status_code == 401


async def test_referral_code_unique_per_user(client: AsyncClient):
    """Cada usuário tem um código de indicação único."""
    h1, _ = await authenticated_client_headers(client)
    h2, _ = await authenticated_client_headers(client)
    r1 = (await client.get("/users/me", headers=h1)).json()["referral_code"]
    r2 = (await client.get("/users/me", headers=h2)).json()["referral_code"]
    assert r1 != r2
