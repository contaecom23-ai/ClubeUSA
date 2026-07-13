"""
Tests for auth endpoints: register, login, confirm-email, refresh, resend-confirmation.
All DB and email calls are mocked — no real Supabase required.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.security import create_access_token, generate_confirmation_token, hash_password
from tests.conftest import empty_result, make_table_result

VALID_USER = {
    "id": str(uuid.uuid4()),
    "email": "joao@example.com",
    "password_hash": hash_password("Senha123"),
    "full_name": "Joao Silva",
    "email_confirmed": True,
    "is_active": True,
    "last_login_at": None,
}


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client, mock_email):
    new_id = str(uuid.uuid4())
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        # No existing user
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_result()
        # Insert user
        db.table.return_value.insert.return_value.execute.return_value = make_table_result([
            {"id": new_id, "email": "joao@example.com", "full_name": "Joao Silva", "email_confirmed": False}
        ])

        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "Senha123",
            "full_name": "Joao Silva",
        })

    assert resp.status_code == 201
    assert "Cadastro realizado" in resp.json()["message"]


def test_register_duplicate_email(client):
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = make_table_result([
            {"id": "existing-id"}
        ])

        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "Senha123",
            "full_name": "Joao Silva",
        })

    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/auth/register", json={
        "email": "joao@example.com",
        "password": "abc",
        "full_name": "Joao Silva",
    })
    assert resp.status_code == 422


def test_register_missing_number_in_password(client):
    resp = client.post("/auth/register", json={
        "email": "joao@example.com",
        "password": "abcdefgh",  # no digit
        "full_name": "Joao Silva",
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db

        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([VALID_USER])
        db.table.return_value.insert.return_value.execute.return_value = make_table_result([{}])
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = make_table_result([{}])

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "Senha123",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([VALID_USER])

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "WrongPass999",
        })

    assert resp.status_code == 401


def test_login_unconfirmed_email(client):
    unconfirmed = {**VALID_USER, "email_confirmed": False}
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([unconfirmed])

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "Senha123",
        })

    assert resp.status_code == 403


# ── Confirm email ─────────────────────────────────────────────────────────────

def test_confirm_email_success(client):
    token = generate_confirmation_token()
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()

    conf = {"id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "token": token, "expires_at": future, "used_at": None}

    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = make_table_result([conf])
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = make_table_result([{}])

        resp = client.post("/auth/confirm-email", json={"token": token})

    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()


def test_confirm_email_invalid_token(client):
    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_result()

        resp = client.post("/auth/confirm-email", json={"token": "invalid-token"})

    assert resp.status_code == 400


def test_confirm_email_expired_token(client):
    token = generate_confirmation_token()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conf = {"id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "token": token, "expires_at": past, "used_at": None}

    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = make_table_result([conf])

        resp = client.post("/auth/confirm-email", json={"token": token})

    assert resp.status_code == 400
    assert "expirado" in resp.json()["detail"].lower()


def test_confirm_email_already_used(client):
    token = generate_confirmation_token()
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
    conf = {
        "id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()),
        "token": token, "expires_at": future,
        "used_at": datetime.now(timezone.utc).isoformat()
    }

    with patch("app.auth.service.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = make_table_result([conf])

        resp = client.post("/auth/confirm-email", json={"token": token})

    assert resp.status_code == 400


# ── Protected route (GET /users/me) ──────────────────────────────────────────

def test_protected_route_no_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_protected_route_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
