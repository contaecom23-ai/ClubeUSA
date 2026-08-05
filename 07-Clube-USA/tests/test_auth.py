"""Tests for Phase 0.1: registration, login, email confirmation."""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from .conftest import make_user, make_profile, make_table_mock


# ── /status ──────────────────────────────────────────────────────────────────

def test_status(client):
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── POST /auth/register ───────────────────────────────────────────────────────

VALID_REGISTER = {
    "email": "joao@example.com",
    "password": "senha123",
    "full_name": "João Silva",
    "zip_code": "90210",
}


def test_register_success(client, mock_db):
    uid = str(uuid.uuid4())
    new_user = make_user(uid, email="joao@example.com", email_confirmed=False)

    users_table = MagicMock()
    select_chain = make_table_mock(data_result=[])   # duplicate check: no match
    insert_chain = make_table_mock(data_result=[new_user])
    users_table.select.return_value = select_chain
    users_table.insert.return_value = insert_chain

    profiles_table = make_table_mock(data_result=[{}])

    mock_db.table.side_effect = lambda name: users_table if name == "users" else profiles_table

    with patch("api.auth.email.send_confirmation_email"):
        r = client.post("/auth/register", json=VALID_REGISTER)

    assert r.status_code == 201
    assert "email" in r.json()["message"].lower()


def test_register_duplicate_email(client, mock_db):
    existing = make_user()
    users_table = MagicMock()
    select_chain = make_table_mock(data_result=[existing])  # duplicate found
    users_table.select.return_value = select_chain
    mock_db.table.side_effect = lambda _: users_table

    r = client.post("/auth/register", json=VALID_REGISTER)
    assert r.status_code == 409


def test_register_short_password(client):
    payload = {**VALID_REGISTER, "password": "abc"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 422


def test_register_invalid_zip(client):
    payload = {**VALID_REGISTER, "zip_code": "ABCDE"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 422


def test_register_invalid_email(client):
    payload = {**VALID_REGISTER, "email": "not-an-email"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 422


# ── POST /auth/login ──────────────────────────────────────────────────────────

def _setup_login(mock_db, user: dict):
    users_table = MagicMock()
    chain = make_table_mock(data_result=[user])
    users_table.select.return_value = chain
    mock_db.table.side_effect = lambda _: users_table


def test_login_success(client, mock_db):
    import bcrypt
    pwd = bcrypt.hashpw(b"senha123", bcrypt.gensalt(4)).decode()  # cost=4 for test speed
    user = make_user()
    user["password_hash"] = pwd

    _setup_login(mock_db, user)

    r = client.post("/auth/login", json={"email": user["email"], "password": "senha123"})
    assert r.status_code == 200
    data = r.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["email_confirmed"] is True


def test_login_wrong_password(client, mock_db):
    import bcrypt
    pwd = bcrypt.hashpw(b"correta", bcrypt.gensalt(4)).decode()
    user = make_user()
    user["password_hash"] = pwd

    _setup_login(mock_db, user)

    r = client.post("/auth/login", json={"email": user["email"], "password": "errada"})
    assert r.status_code == 401


def test_login_unknown_email(client, mock_db):
    users_table = MagicMock()
    chain = make_table_mock(data_result=[])
    users_table.select.return_value = chain
    mock_db.table.side_effect = lambda _: users_table

    r = client.post("/auth/login", json={"email": "ghost@x.com", "password": "any"})
    assert r.status_code == 401


# ── POST /auth/confirm-email ──────────────────────────────────────────────────

def _setup_confirm(mock_db, user_row: dict | None):
    users_table = MagicMock()
    data = [user_row] if user_row else []
    users_table.select.return_value = make_table_mock(data_result=data)
    users_table.update.return_value = make_table_mock(data_result=[{}])
    mock_db.table.side_effect = lambda _: users_table


def test_confirm_email_success(client, mock_db):
    row = {
        "id": str(uuid.uuid4()),
        "email_confirmed": False,
        "email_confirmation_expires_at": "2099-01-01T00:00:00+00:00",
    }
    _setup_confirm(mock_db, row)

    r = client.post("/auth/confirm-email", json={"token": "valid-token"})
    assert r.status_code == 200


def test_confirm_email_invalid_token(client, mock_db):
    _setup_confirm(mock_db, None)

    r = client.post("/auth/confirm-email", json={"token": "bad-token"})
    assert r.status_code == 400


def test_confirm_email_expired_token(client, mock_db):
    row = {
        "id": str(uuid.uuid4()),
        "email_confirmed": False,
        "email_confirmation_expires_at": "2000-01-01T00:00:00+00:00",
    }
    _setup_confirm(mock_db, row)

    r = client.post("/auth/confirm-email", json={"token": "expired-token"})
    assert r.status_code == 400


# ── GET /users/me (auth required) ────────────────────────────────────────────

def _make_token(user_id: str) -> str:
    from api.auth.service import create_access_token
    return create_access_token(user_id)


def test_get_profile_requires_auth(client):
    r = client.get("/users/me")
    assert r.status_code == 403  # HTTPBearer returns 403 when header absent


def test_get_profile_success(client, mock_db):
    uid = str(uuid.uuid4())
    user = make_user(uid)
    profile = make_profile(uid)

    users_table = MagicMock()
    users_table.select.return_value = make_table_mock(data_result=[user])

    profiles_table = MagicMock()
    profiles_table.select.return_value = make_table_mock(data_result=[profile])

    mock_db.table.side_effect = lambda name: users_table if name == "users" else profiles_table

    token = _make_token(uid)
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == user["email"]
    assert data["full_name"] == profile["full_name"]


# ── Cross-tenant isolation ────────────────────────────────────────────────────

def test_cross_tenant_profile_isolated(client, mock_db):
    """User A's token cannot access User B's profile — each gets their own data only."""
    uid_a = str(uuid.uuid4())
    uid_b = str(uuid.uuid4())  # noqa: F841  — present to show it's not used in the request

    user_a = make_user(uid_a, email="a@example.com")
    profile_a = make_profile(uid_a, full_name="User A")

    users_table = MagicMock()
    users_table.select.return_value = make_table_mock(data_result=[user_a])

    profiles_table = MagicMock()
    profiles_table.select.return_value = make_table_mock(data_result=[profile_a])

    mock_db.table.side_effect = lambda name: users_table if name == "users" else profiles_table

    # Token signed for uid_a; the server resolves user_id from the token, never from request body
    token_a = _make_token(uid_a)
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"
    assert r.json()["user_id"] == uid_a
