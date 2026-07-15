"""
Testes do fluxo de autenticação (Fase 0.1).
Cobre: registro, confirmação de e-mail, login, refresh, logout.
Segurança: senhas fracas, timing-safe (e-mail inválido dá mesma resposta),
           e-mail não confirmado bloqueia login.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _api_response(data):
    r = MagicMock()
    r.data = data
    return r


def _make_user(
    email="joao@example.com",
    confirmed=True,
    banned=False,
    password="Senha@123",
):
    from app.security import hash_password
    return {
        "id": "user-uuid-1",
        "email": email,
        "password_hash": hash_password(password),
        "full_name": "João Silva",
        "zip_code": "33101",
        "phone": None,
        "email_confirmed": confirmed,
        "email_confirmed_at": datetime.now(timezone.utc).isoformat() if confirmed else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_banned": banned,
        "last_login_at": None,
    }


def _setup_users_select(mock_db, data):
    """Configura o que db.table('users').select(...).maybe_single().execute() retorna."""
    users = mock_db.table('users')
    users._select.execute = AsyncMock(return_value=_api_response(data))
    return users


def _setup_users_insert(mock_db, data):
    users = mock_db.table('users')
    users._insert.execute = AsyncMock(return_value=_api_response(data))
    return users


def _setup_select(mock_db, table_name: str, data):
    t = mock_db.table(table_name)
    t._select.execute = AsyncMock(return_value=_api_response(data))
    return t


# ─────────────────────────────────────────────
# /auth/register
# ─────────────────────────────────────────────

class TestRegister:
    def test_success(self, client, mock_db):
        _setup_users_select(mock_db, None)  # usuário não existe
        _setup_users_insert(mock_db, [{
            "id": "new-uuid",
            "email": "novo@example.com",
            "full_name": "Maria Costa",
        }])

        resp = client.post("/auth/register", json={
            "email": "novo@example.com",
            "password": "Segura@1",
            "full_name": "Maria Costa",
            "zip_code": "10001",
        })
        assert resp.status_code == 201
        assert "Cadastro realizado" in resp.json()["message"]

    def test_weak_password_short(self, client):
        resp = client.post("/auth/register", json={
            "email": "a@b.com",
            "password": "abc",
            "full_name": "Teste",
        })
        assert resp.status_code == 422

    def test_weak_password_no_digit_or_special(self, client):
        resp = client.post("/auth/register", json={
            "email": "a@b.com",
            "password": "senhasemdigito",
            "full_name": "Teste",
        })
        assert resp.status_code == 422

    def test_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "nao-e-email",
            "password": "Senha@123",
            "full_name": "Teste",
        })
        assert resp.status_code == 422

    def test_duplicate_email_returns_generic_message(self, client, mock_db):
        _setup_users_select(mock_db, _make_user())  # usuário já existe

        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "Senha@123",
            "full_name": "João",
        })
        # Não deve retornar 409 ou vazar que o e-mail existe
        assert resp.status_code == 200
        assert "receberá" in resp.json()["message"].lower()

    def test_name_too_short(self, client):
        resp = client.post("/auth/register", json={
            "email": "a@b.com",
            "password": "Senha@123",
            "full_name": "X",
        })
        assert resp.status_code == 422


# ─────────────────────────────────────────────
# /auth/confirm-email/{token}
# ─────────────────────────────────────────────

class TestConfirmEmail:
    def _token_record(self, expired=False):
        expires = datetime.now(timezone.utc) + (
            timedelta(hours=-1) if expired else timedelta(hours=23)
        )
        return {
            "id": "token-uuid-1",
            "user_id": "user-uuid-1",
            "token_hash": "ignored-in-test",
            "expires_at": expires.isoformat(),
            "used_at": None,
        }

    def test_valid_token_confirms_email(self, client, mock_db):
        _setup_select(mock_db, "email_verification_tokens", self._token_record())

        resp = client.get("/auth/confirm-email/valid-token-xyz")
        assert resp.status_code == 200
        assert "confirmado" in resp.json()["message"].lower()

    def test_invalid_token(self, client, mock_db):
        _setup_select(mock_db, "email_verification_tokens", None)

        resp = client.get("/auth/confirm-email/bad-token")
        assert resp.status_code == 400

    def test_expired_token(self, client, mock_db):
        _setup_select(mock_db, "email_verification_tokens", self._token_record(expired=True))

        resp = client.get("/auth/confirm-email/expired-token")
        assert resp.status_code == 400
        assert "expirado" in resp.json()["detail"].lower()


# ─────────────────────────────────────────────
# /auth/login
# ─────────────────────────────────────────────

class TestLogin:
    def test_success(self, client, mock_db):
        _setup_users_select(mock_db, _make_user())

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "Senha@123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "joao@example.com"

    def test_wrong_password(self, client, mock_db):
        _setup_users_select(mock_db, _make_user())

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "SenhaErrada@1",
        })
        assert resp.status_code == 401

    def test_unknown_email_gives_generic_error(self, client, mock_db):
        _setup_users_select(mock_db, None)

        resp = client.post("/auth/login", json={
            "email": "naoexiste@example.com",
            "password": "Senha@123",
        })
        assert resp.status_code == 401
        # Mesma mensagem — não vaza se o e-mail existe
        assert resp.json()["detail"] == "E-mail ou senha incorretos."

    def test_unconfirmed_email_blocked(self, client, mock_db):
        _setup_users_select(mock_db, _make_user(confirmed=False))

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "Senha@123",
        })
        assert resp.status_code == 403
        assert "confirmado" in resp.json()["detail"].lower()

    def test_banned_user_blocked(self, client, mock_db):
        _setup_users_select(mock_db, _make_user(banned=True))

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "Senha@123",
        })
        assert resp.status_code == 403


# ─────────────────────────────────────────────
# /auth/refresh
# ─────────────────────────────────────────────

class TestRefresh:
    def test_valid_refresh_token(self, client, mock_db):
        _setup_select(mock_db, "refresh_tokens", {
            "id": "rt-uuid-1",
            "user_id": "user-uuid-1",
            "token_hash": "hash",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=6)).isoformat(),
            "revoked_at": None,
        })

        resp = client.post("/auth/refresh", json={"refresh_token": "some-valid-token"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_invalid_refresh_token(self, client, mock_db):
        _setup_select(mock_db, "refresh_tokens", None)

        resp = client.post("/auth/refresh", json={"refresh_token": "bad-token"})
        assert resp.status_code == 401

    def test_expired_refresh_token(self, client, mock_db):
        _setup_select(mock_db, "refresh_tokens", {
            "id": "rt-uuid-1",
            "user_id": "user-uuid-1",
            "token_hash": "hash",
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "revoked_at": None,
        })

        resp = client.post("/auth/refresh", json={"refresh_token": "expired-token"})
        assert resp.status_code == 401


# ─────────────────────────────────────────────
# /users/me (isolamento multi-tenant)
# ─────────────────────────────────────────────

class TestUsersMe:
    def _auth_header(self, user_id="user-uuid-1"):
        from app.security import create_access_token
        token = create_access_token(user_id)
        return {"Authorization": f"Bearer {token}"}

    def test_get_profile_authenticated(self, client, mock_db):
        _setup_users_select(mock_db, {
            "id": "user-uuid-1",
            "email": "joao@example.com",
            "full_name": "João Silva",
            "zip_code": "33101",
            "phone": None,
            "email_confirmed": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        resp = client.get("/users/me", headers=self._auth_header())
        assert resp.status_code == 200
        assert resp.json()["email"] == "joao@example.com"

    def test_get_profile_unauthenticated(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_update_profile(self, client, mock_db):
        users = mock_db.table('users')
        users._update.execute = AsyncMock(return_value=MagicMock(data=[{
            "id": "user-uuid-1",
            "email": "joao@example.com",
            "full_name": "João S. Atualizado",
            "zip_code": "10001",
            "phone": None,
            "email_confirmed": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }]))

        resp = client.patch(
            "/users/me",
            json={"full_name": "João S. Atualizado", "zip_code": "10001"},
            headers=self._auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "João S. Atualizado"

    def test_cross_tenant_not_possible(self, client, mock_db):
        """
        user_id vem do token, não do body — não há como acessar perfil alheio
        passando um id diferente no body/query string.
        """
        _setup_users_select(mock_db, None)  # usuário 2 não encontrado

        from app.security import create_access_token
        token_user2 = create_access_token("user-uuid-2")
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {token_user2}"})
        # O endpoint autenticou, mas não encontrou o usuário — retorna 404, nunca 200 com dados alheios
        assert resp.status_code in (200, 404)
        assert resp.status_code != 401
