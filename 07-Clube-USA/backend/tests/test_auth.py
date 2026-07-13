"""
Testes de autenticação (Fase 0.1).

Requerem DATABASE_URL. Pulados automaticamente sem ela.
Cada teste usa email único para isolamento.
"""
import secrets
import uuid

import pytest
from httpx import AsyncClient

from .conftest import requires_db

pytestmark = [requires_db, pytest.mark.anyio]


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


async def register_user(client: AsyncClient, email: str = None, password: str = "Senha@Forte9") -> dict:
    email = email or unique_email()
    res = await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Teste Usuário",
    })
    assert res.status_code == 201, res.text
    return {"email": email, "password": password}


async def confirm_user(client: AsyncClient, email: str) -> None:
    """Confirma email via endpoint dev (DEBUG=true)."""
    res = await client.get(f"/auth/dev/pending-confirmation/{email}")
    assert res.status_code == 200, f"Sem token pendente para {email}"
    token = res.json()["token"]
    res2 = await client.get(f"/auth/confirm-email?token={token}")
    assert res2.status_code == 200


async def login(client: AsyncClient, email: str, password: str) -> dict:
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


# ── Testes ────────────────────────────────────────────────────────────────────

async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


async def test_register_success(client: AsyncClient):
    email = unique_email()
    res = await client.post("/auth/register", json={
        "email": email,
        "password": "Senha@Forte9",
        "full_name": "João Silva",
        "zip_code": "10001",
        "state": "NY",
    })
    assert res.status_code == 201
    assert "email" in res.json()["message"].lower() or "cadastro" in res.json()["message"].lower()


async def test_register_duplicate_email(client: AsyncClient):
    user = await register_user(client)
    res = await client.post("/auth/register", json={
        "email": user["email"],
        "password": "OutraSenha@2",
        "full_name": "Outro Nome",
    })
    assert res.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "email": unique_email(),
        "password": "12345678",  # só números
        "full_name": "Teste",
    })
    assert res.status_code == 422


async def test_register_short_password(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "email": unique_email(),
        "password": "abc123",  # menos de 8
        "full_name": "Teste",
    })
    assert res.status_code == 422


async def test_login_without_confirmation(client: AsyncClient):
    user = await register_user(client)
    res = await client.post("/auth/login", json={"email": user["email"], "password": user["password"]})
    assert res.status_code == 403
    assert "confirmado" in res.json()["detail"].lower()


async def test_confirm_email(client: AsyncClient):
    user = await register_user(client)
    await confirm_user(client, user["email"])


async def test_login_after_confirmation(client: AsyncClient):
    user = await register_user(client)
    await confirm_user(client, user["email"])
    tokens = await login(client, user["email"], user["password"])
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    user = await register_user(client)
    await confirm_user(client, user["email"])
    res = await client.post("/auth/login", json={"email": user["email"], "password": "SenhaErrada9"})
    assert res.status_code == 401


async def test_confirm_token_invalid(client: AsyncClient):
    res = await client.get("/auth/confirm-email?token=token-falso-inexistente")
    assert res.status_code == 400


async def test_confirm_token_replay(client: AsyncClient):
    """Mesmo token não pode ser usado duas vezes."""
    user = await register_user(client)
    res = await client.get(f"/auth/dev/pending-confirmation/{user['email']}")
    token = res.json()["token"]
    await client.get(f"/auth/confirm-email?token={token}")
    res2 = await client.get(f"/auth/confirm-email?token={token}")
    assert res2.status_code == 400


async def test_refresh_token(client: AsyncClient):
    user = await register_user(client)
    await confirm_user(client, user["email"])
    tokens = await login(client, user["email"], user["password"])

    res = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    new_tokens = res.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


async def test_refresh_token_replay(client: AsyncClient):
    """Refresh token rotacionado não pode ser reutilizado."""
    user = await register_user(client)
    await confirm_user(client, user["email"])
    tokens = await login(client, user["email"], user["password"])

    await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    res2 = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res2.status_code == 401


async def test_dev_endpoint_hidden_in_production(client: AsyncClient):
    """Endpoint dev deve retornar 404 quando DEBUG=false."""
    import app.config as cfg
    original = cfg.settings.DEBUG
    cfg.settings.DEBUG = False
    try:
        res = await client.get("/auth/dev/pending-confirmation/qualquer@email.com")
        assert res.status_code == 404
    finally:
        cfg.settings.DEBUG = original
