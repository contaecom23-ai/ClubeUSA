"""Testes de perfil de usuário — Fase 0.1."""
import pytest
from httpx import AsyncClient
from tests.conftest import register_and_confirm

pytestmark = pytest.mark.asyncio


async def test_get_profile_requires_auth(client: AsyncClient):
    resp = await client.get("/users/me")
    assert resp.status_code == 403


async def test_get_profile_success(client: AsyncClient):
    token = await register_and_confirm(client, "profile_get@clubeusa.com", full_name="João Lima")
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "profile_get@clubeusa.com"
    assert data["full_name"] == "João Lima"
    assert data["email_confirmed"] is True


async def test_update_profile_full_name(client: AsyncClient):
    token = await register_and_confirm(client, "update_name@clubeusa.com")
    resp = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Carlos Souza"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Carlos Souza"


async def test_update_profile_zip_and_state(client: AsyncClient):
    token = await register_and_confirm(client, "update_loc@clubeusa.com")
    resp = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"zip_code": "90210", "us_state": "CA"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zip_code"] == "90210"
    assert data["us_state"] == "CA"


async def test_update_profile_invalid_zip(client: AsyncClient):
    token = await register_and_confirm(client, "bad_zip@clubeusa.com")
    resp = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"zip_code": "ABCDE"},
    )
    assert resp.status_code == 422


async def test_update_profile_invalid_state(client: AsyncClient):
    token = await register_and_confirm(client, "bad_state@clubeusa.com")
    resp = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"us_state": "XX"},
    )
    assert resp.status_code == 422


async def test_update_profile_bio_strips_html(client: AsyncClient):
    token = await register_and_confirm(client, "xss_bio@clubeusa.com")
    resp = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"bio": "<script>alert('xss')</script>Minha bio"},
    )
    assert resp.status_code == 200
    bio = resp.json()["bio"]
    assert "<script>" not in bio
    assert "Minha bio" in bio


async def test_update_profile_partial(client: AsyncClient):
    """PATCH parcial: campos não enviados não devem ser alterados."""
    token = await register_and_confirm(client, "partial@clubeusa.com", full_name="Ana Costa")

    await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"zip_code": "10001"},
    )
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert data["full_name"] == "Ana Costa"  # não alterado
    assert data["zip_code"] == "10001"       # alterado


async def test_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer token_falso"})
    assert resp.status_code == 401
