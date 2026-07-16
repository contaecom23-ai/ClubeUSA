"""Testes de integração das rotas de auth — DB mockado via dependency override."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from security import create_access_token, hash_password


# ─── helpers ──────────────────────────────────────────────────────────────────

def _set_select(mock_db, data):
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = data


def _set_insert(mock_db, data=None):
    mock_db.table.return_value.insert.return_value.execute.return_value.data = data or []


def _set_update(mock_db, data=None):
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = data or []


# ─── /api/auth/register ───────────────────────────────────────────────────────

class TestRegister:
    def test_success(self, client, mock_db):
        _set_select(mock_db, [])      # email não existe
        _set_insert(mock_db, [{"id": "uuid-new"}])

        r = client.post("/api/auth/register", json={
            "email": "novo@example.com",
            "password": "senha1234",
            "name": "Maria Silva",
        })
        assert r.status_code == 201
        assert "message" in r.json()

    def test_duplicate_email_returns_201_anti_enum(self, client, mock_db):
        _set_select(mock_db, [{"id": "existing-id"}])  # email já existe

        r = client.post("/api/auth/register", json={
            "email": "existente@example.com",
            "password": "senha1234",
            "name": "João",
        })
        # Anti-enumeração: mesmo status code
        assert r.status_code == 201

    def test_weak_password_rejected(self, client, mock_db):
        r = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "curto",
            "name": "Test",
        })
        assert r.status_code == 422

    def test_blank_name_rejected(self, client, mock_db):
        r = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "senha1234",
            "name": "   ",
        })
        assert r.status_code == 422

    def test_invalid_email_rejected(self, client, mock_db):
        r = client.post("/api/auth/register", json={
            "email": "nao-e-um-email",
            "password": "senha1234",
            "name": "Test",
        })
        assert r.status_code == 422

    def test_missing_required_fields(self, client, mock_db):
        r = client.post("/api/auth/register", json={"email": "a@b.com"})
        assert r.status_code == 422


# ─── /api/auth/confirm-email ──────────────────────────────────────────────────

class TestConfirmEmail:
    def test_success(self, client, mock_db):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        _set_select(mock_db, [{
            "id": "user-123",
            "email_confirm_token_expires_at": future,
            "email_confirmed_at": None,
        }])
        _set_update(mock_db)

        r = client.get("/api/auth/confirm-email?token=valid-token-abc")
        assert r.status_code == 200
        assert "confirmado" in r.json()["message"].lower()

    def test_invalid_token(self, client, mock_db):
        _set_select(mock_db, [])  # token não encontrado

        r = client.get("/api/auth/confirm-email?token=token-invalido")
        assert r.status_code == 400

    def test_expired_token(self, client, mock_db):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        _set_select(mock_db, [{
            "id": "user-123",
            "email_confirm_token_expires_at": past,
            "email_confirmed_at": None,
        }])

        r = client.get("/api/auth/confirm-email?token=expired-token")
        assert r.status_code == 400
        assert "expirado" in r.json()["detail"].lower()

    def test_already_confirmed(self, client, mock_db):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        _set_select(mock_db, [{
            "id": "user-123",
            "email_confirm_token_expires_at": future,
            "email_confirmed_at": "2026-07-01T00:00:00+00:00",
        }])

        r = client.get("/api/auth/confirm-email?token=some-token")
        assert r.status_code == 200
        assert "já confirmado" in r.json()["message"].lower()


# ─── /api/auth/login ──────────────────────────────────────────────────────────

class TestLogin:
    def _user(self, confirmed=True, active=True):
        return [{
            "id": "user-123",
            "password_hash": hash_password("senha1234"),
            "email_confirmed_at": "2026-07-01T00:00:00+00:00" if confirmed else None,
            "is_active": active,
        }]

    def test_success(self, client, mock_db):
        _set_select(mock_db, self._user())
        _set_insert(mock_db, [{"id": "rt-id"}])

        r = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "senha1234",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client, mock_db):
        _set_select(mock_db, self._user())

        r = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "senha_errada",
        })
        assert r.status_code == 401

    def test_user_not_found(self, client, mock_db):
        _set_select(mock_db, [])

        r = client.post("/api/auth/login", json={
            "email": "naoexiste@example.com",
            "password": "qualquercoisa",
        })
        assert r.status_code == 401

    def test_email_not_confirmed(self, client, mock_db):
        _set_select(mock_db, self._user(confirmed=False))

        r = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "senha1234",
        })
        assert r.status_code == 403
        assert "confirmado" in r.json()["detail"].lower()

    def test_inactive_account(self, client, mock_db):
        _set_select(mock_db, self._user(active=False))

        r = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "senha1234",
        })
        assert r.status_code == 403
        assert "desativada" in r.json()["detail"].lower()


# ─── /api/auth/logout ─────────────────────────────────────────────────────────

class TestLogout:
    def test_success(self, client, mock_db):
        _set_update(mock_db)

        r = client.post("/api/auth/logout", json={"refresh_token": "qualquer-token"})
        assert r.status_code == 200
        assert "logout" in r.json()["message"].lower()


# ─── /api/health ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client, mock_db):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["message"] == "ok"
