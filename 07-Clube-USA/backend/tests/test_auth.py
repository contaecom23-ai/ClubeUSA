"""
Testes de autenticação — Fase 0.1
Cobre: registro, confirmação de email, login, rota protegida /me.
Todos os testes usam pool mockado (sem banco real).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

import asyncpg

from app.auth.service import create_jwt, decode_jwt, hash_password, verify_password
from tests.conftest import make_user_row


# ─── Testes unitários de serviço ────────────────────────────────────────────


def test_password_hash_and_verify():
    password = "SenhaForte123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("SenhaErrada1", hashed)


def test_jwt_create_and_decode():
    uid = str(uuid.uuid4())
    token, expires_in = create_jwt(uid, "teste@email.com")
    payload = decode_jwt(token)
    assert payload["sub"] == uid
    assert payload["email"] == "teste@email.com"
    assert expires_in == 7 * 24 * 3600


def test_jwt_invalid_raises():
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_jwt("token.invalido.aqui")


# ─── Testes de API ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success(client_with_pool):
    user_row = {
        "id": uuid.uuid4(),
        "email": "novo@exemplo.com",
        "full_name": "Maria Silva",
        "zip_code": "90210",
        "email_confirmed": False,
        "created_at": datetime.now(timezone.utc),
    }
    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.post("/api/auth/register", json={
            "email": "novo@exemplo.com",
            "password": "SenhaForte1",
            "full_name": "Maria Silva",
            "zip_code": "90210",
        })
    assert r.status_code == 201
    assert "email" in r.json()["message"].lower() or "cadastro" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.post("/api/auth/register", json={
            "email": "teste@exemplo.com",
            "password": "fraca",
            "full_name": "Teste",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_rejected(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.post("/api/auth/register", json={
            "email": "nao-e-email",
            "password": "SenhaForte1",
            "full_name": "Teste",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_zip_rejected(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.post("/api/auth/register", json={
            "email": "teste@exemplo.com",
            "password": "SenhaForte1",
            "full_name": "Teste",
            "zip_code": "ABCDE",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email_same_response(client_with_pool):
    """Email duplicado retorna mesma mensagem de sucesso (evita enumeração)."""
    ac, conn = await client_with_pool(
        fetchrow_side_effect=asyncpg.UniqueViolationError("duplicate")
    )
    async with ac:
        r = await ac.post("/api/auth/register", json={
            "email": "existente@exemplo.com",
            "password": "SenhaForte1",
            "full_name": "Teste",
        })
    # Deve retornar 201 com mesma mensagem, não 409
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_confirm_email_success(client_with_pool):
    user_row = {
        "id": uuid.uuid4(),
        "email": "user@exemplo.com",
        "full_name": "User",
        "zip_code": None,
        "email_confirmed": True,
        "created_at": datetime.now(timezone.utc),
    }
    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.get("/api/auth/confirm?token=valid-token-aqui")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_confirm_email_invalid_token(client_with_pool):
    ac, conn = await client_with_pool(fetchrow_return=None)
    async with ac:
        r = await ac.get("/api/auth/confirm?token=token-invalido")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client_with_pool):
    password = "SenhaForte1"
    user_row = make_user_row(
        email="joao@exemplo.com",
        email_confirmed=True,
        password_hash=hash_password(password),
    )
    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.post("/api/auth/login", json={
            "email": "joao@exemplo.com",
            "password": password,
        })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client_with_pool):
    user_row = make_user_row(
        email="joao@exemplo.com",
        email_confirmed=True,
        password_hash=hash_password("SenhaCorreta1"),
    )
    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.post("/api/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "SenhaErrada1",
        })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unconfirmed_email(client_with_pool):
    password = "SenhaForte1"
    user_row = make_user_row(
        email_confirmed=False,
        password_hash=hash_password(password),
    )
    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.post("/api/auth/login", json={
            "email": "joao@exemplo.com",
            "password": password,
        })
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_login_nonexistent_user(client_with_pool):
    ac, conn = await client_with_pool(fetchrow_return=None)
    async with ac:
        r = await ac.post("/api/auth/login", json={
            "email": "naoexiste@exemplo.com",
            "password": "SenhaQualquer1",
        })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.get("/api/auth/me")
    assert r.status_code in (401, 403)  # sem credenciais


@pytest.mark.asyncio
async def test_me_returns_profile(client_with_pool):
    uid = str(uuid.uuid4())
    user_row = {
        "id": uuid.UUID(uid),
        "email": "joao@exemplo.com",
        "full_name": "João Silva",
        "zip_code": "10001",
        "email_confirmed": True,
        "created_at": datetime.now(timezone.utc),
    }
    token, _ = create_jwt(uid, "joao@exemplo.com")

    ac, conn = await client_with_pool(fetchrow_return=user_row)
    async with ac:
        r = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "joao@exemplo.com"
    assert data["id"] == uid
    assert data["email_confirmed"] is True


@pytest.mark.asyncio
async def test_me_invalid_token_rejected(client_with_pool):
    ac, _ = await client_with_pool()
    async with ac:
        r = await ac.get("/api/auth/me", headers={"Authorization": "Bearer token.invalido.xxx"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_user_not_in_db(client_with_pool):
    """Token válido mas usuário removido/inativo — deve retornar 401."""
    uid = str(uuid.uuid4())
    token, _ = create_jwt(uid, "apagado@exemplo.com")

    ac, conn = await client_with_pool(fetchrow_return=None)
    async with ac:
        r = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
