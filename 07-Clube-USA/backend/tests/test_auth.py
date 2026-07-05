"""
Testes da Fase 0.1 — Cadastro, login e perfil.

Estratégia: banco mockado via dependency override.
Testa o contrato da API e lógica de negócio, sem infraestrutura real.
"""

import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.utils.auth import create_access_token, hash_password, verify_password


# ── Utilitários ────────────────────────────────────────────────────────────────

class TestPasswordUtils:
    def test_hash_differs_from_original(self):
        pw = "SenhaSegura123"
        assert hash_password(pw) != pw

    def test_verify_correct_password(self):
        pw = "SenhaSegura123"
        assert verify_password(pw, hash_password(pw))

    def test_verify_wrong_password(self):
        assert not verify_password("errada", hash_password("SenhaSegura123"))

    def test_two_hashes_differ(self):
        pw = "SenhaSegura123"
        assert hash_password(pw) != hash_password(pw)  # salt aleatorio


# ── POST /auth/register ────────────────────────────────────────────────────────

class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        ac, mock_db = client
        mock_db.fetchval.side_effect = [None, "uuid-novo"]  # sem duplicata; retorna id

        with patch("app.routers.auth.send_confirmation_email", new_callable=AsyncMock):
            resp = await ac.post("/auth/register", json={
                "email": "joao@exemplo.com",
                "password": "SenhaSegura123",
                "full_name": "João Silva",
                "zip_code": "10001",
            })

        assert resp.status_code == 201
        body = resp.json()
        assert "message" in body
        assert body["user_id"] == "uuid-novo"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        ac, mock_db = client
        mock_db.fetchval.return_value = "id-existente"

        resp = await ac.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
            "full_name": "João Silva",
        })

        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        ac, _ = client
        resp = await ac.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "123",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        ac, _ = client
        resp = await ac.post("/auth/register", json={
            "email": "nao-e-email",
            "password": "SenhaSegura123",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_zip(self, client):
        ac, mock_db = client
        mock_db.fetchval.return_value = None

        resp = await ac.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
            "full_name": "João Silva",
            "zip_code": "abc",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_blank_name(self, client):
        ac, _ = client
        resp = await ac.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
            "full_name": "   ",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_email_failure_does_not_break_registration(self, client):
        ac, mock_db = client
        mock_db.fetchval.side_effect = [None, "uuid-novo"]

        with patch("app.routers.auth.send_confirmation_email", side_effect=Exception("SMTP error")):
            resp = await ac.post("/auth/register", json={
                "email": "joao@exemplo.com",
                "password": "SenhaSegura123",
                "full_name": "João Silva",
            })

        # Cadastro deve funcionar mesmo com falha no email
        assert resp.status_code == 201


# ── POST /auth/login ───────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = {
            "id": "uuid-123",
            "email": "joao@exemplo.com",
            "password_hash": hash_password("SenhaSegura123"),
            "email_confirmed": True,
            "is_active": True,
        }

        resp = await ac.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = {
            "id": "uuid-123",
            "email": "joao@exemplo.com",
            "password_hash": hash_password("SenhaSegura123"),
            "email_confirmed": True,
            "is_active": True,
        }

        resp = await ac.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "SenhaErrada",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_email_not_confirmed(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = {
            "id": "uuid-123",
            "email": "joao@exemplo.com",
            "password_hash": hash_password("SenhaSegura123"),
            "email_confirmed": False,
            "is_active": True,
        }

        resp = await ac.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
        })
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = None

        resp = await ac.post("/auth/login", json={
            "email": "naoexiste@exemplo.com",
            "password": "SenhaSegura123",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = {
            "id": "uuid-123",
            "email": "joao@exemplo.com",
            "password_hash": hash_password("SenhaSegura123"),
            "email_confirmed": True,
            "is_active": False,
        }

        resp = await ac.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSegura123",
        })
        assert resp.status_code == 401


# ── GET /auth/confirm/{token} ──────────────────────────────────────────────────

class TestConfirmEmail:
    @pytest.mark.asyncio
    async def test_confirm_valid_token(self, client):
        ac, mock_db = client
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=23)
        mock_db.fetchrow.return_value = {"id": "uuid-123", "email_confirm_expires_at": future}
        mock_db.execute.return_value = None

        resp = await ac.get("/auth/confirm/token-valido", follow_redirects=False)
        # Deve redirecionar para login com ?confirmed=1
        assert resp.status_code in (302, 307)
        assert "confirmed=1" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_confirm_invalid_token(self, client):
        ac, mock_db = client
        mock_db.fetchrow.return_value = None

        resp = await ac.get("/auth/confirm/token-invalido", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "confirm_error=invalid" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_confirm_expired_token(self, client):
        ac, mock_db = client
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        mock_db.fetchrow.return_value = {"id": "uuid-123", "email_confirm_expires_at": past}

        resp = await ac.get("/auth/confirm/token-expirado", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "confirm_error=expired" in resp.headers["location"]


# ── GET /auth/me ───────────────────────────────────────────────────────────────

class TestProfile:
    @pytest.mark.asyncio
    async def test_get_me_without_auth(self, client):
        ac, _ = client
        resp = await ac.get("/auth/me")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_success(self, client):
        ac, mock_db = client
        token = create_access_token("uuid-123", "joao@exemplo.com")
        now = datetime.datetime.now(datetime.timezone.utc)
        mock_db.fetchrow.return_value = {
            "id": "uuid-123",
            "email": "joao@exemplo.com",
            "full_name": "João Silva",
            "zip_code": "10001",
            "email_confirmed": True,
            "created_at": now,
        }

        resp = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "joao@exemplo.com"
        assert body["full_name"] == "João Silva"
        assert body["email_confirmed"] is True

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client):
        ac, _ = client
        resp = await ac.get("/auth/me", headers={"Authorization": "Bearer token-invalido"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_success(self, client):
        ac, mock_db = client
        token = create_access_token("uuid-123", "joao@exemplo.com")
        now = datetime.datetime.now(datetime.timezone.utc)

        # get_current_user faz fetchrow; update_me faz outro fetchrow
        mock_db.fetchrow.side_effect = [
            {
                "id": "uuid-123",
                "email": "joao@exemplo.com",
                "full_name": "João Silva",
                "zip_code": None,
                "email_confirmed": True,
                "created_at": now,
            },
            {
                "id": "uuid-123",
                "email": "joao@exemplo.com",
                "full_name": "João Silva Atualizado",
                "zip_code": "90210",
                "email_confirmed": True,
                "created_at": now,
            },
        ]

        resp = await ac.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "João Silva Atualizado", "zip_code": "90210"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["full_name"] == "João Silva Atualizado"
        assert body["zip_code"] == "90210"
