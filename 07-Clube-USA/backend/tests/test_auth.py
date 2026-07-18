"""
Tests for auth routes and service logic.
All Supabase calls are mocked via the mock_db fixture from conftest.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.auth.utils import (
    hash_password, verify_password, create_access_token, decode_access_token,
    generate_refresh_token, generate_email_confirm_token,
)
from app.auth.service import (
    AuthError, register_user, confirm_email, login_user,
)


# ---------------------------------------------------------------------------
# Unit tests — utils
# ---------------------------------------------------------------------------

def test_password_hash_and_verify():
    hashed = hash_password("s3cr3tPass!")
    assert verify_password("s3cr3tPass!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-uuid-123")
    uid = decode_access_token(token)
    assert uid == "user-uuid-123"


def test_decode_invalid_token():
    assert decode_access_token("garbage.token.value") is None


def test_tokens_are_unique():
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2

    c1 = generate_email_confirm_token()
    c2 = generate_email_confirm_token()
    assert c1 != c2


# ---------------------------------------------------------------------------
# Unit tests — service
# ---------------------------------------------------------------------------

def _make_db_empty():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    db.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "uuid-1", "email": "a@b.com", "full_name": "Ana"}
    ]
    return db


def test_register_user_success():
    db = _make_db_empty()
    with patch("app.auth.service.send_confirmation_email") as mock_email:
        result = register_user(db, "user@test.com", "password123", "João Silva")
    mock_email.assert_called_once()
    assert result["email"] == "a@b.com"


def test_register_user_duplicate_email():
    db = MagicMock()
    # Simulates existing email found
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "existing"}
    ]
    with pytest.raises(AuthError) as exc:
        register_user(db, "dup@test.com", "password123", "Nome")
    assert exc.value.status_code == 400


def test_confirm_email_success():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "uid-1", "email_confirmed": False}
    ]
    db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
    assert confirm_email(db, "valid-token") is True


def test_confirm_email_invalid_token():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    assert confirm_email(db, "bad-token") is False


def test_confirm_email_already_confirmed():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "uid-1", "email_confirmed": True}
    ]
    assert confirm_email(db, "token") is True


def test_login_wrong_password():
    from app.auth.utils import hash_password
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "uid-1",
        "password_hash": hash_password("correctpassword"),
        "email_confirmed": True,
    }]
    with pytest.raises(AuthError) as exc:
        login_user(db, "user@test.com", "wrongpassword")
    assert exc.value.status_code == 401


def test_login_email_not_confirmed():
    from app.auth.utils import hash_password
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "uid-1",
        "password_hash": hash_password("pass12345"),
        "email_confirmed": False,
    }]
    with pytest.raises(AuthError) as exc:
        login_user(db, "user@test.com", "pass12345")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Integration-style tests — HTTP routes via TestClient
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_route_success(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_db.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "uid-new", "email": "new@test.com", "full_name": "Maria"}
    ]
    with patch("app.auth.service.send_confirmation_email"):
        r = client.post("/auth/register", json={
            "email": "new@test.com",
            "password": "senha1234",
            "full_name": "Maria Silva",
        })
    assert r.status_code == 201
    assert "email" in r.json()["message"].lower()


def test_register_route_password_too_short(client):
    r = client.post("/auth/register", json={
        "email": "x@test.com",
        "password": "123",
        "full_name": "Nome",
    })
    assert r.status_code == 422


def test_confirm_email_invalid(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    r = client.get("/auth/confirm-email?token=badtoken")
    assert r.status_code == 400


def test_login_route_unconfirmed(client, mock_db):
    from app.auth.utils import hash_password
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "uid-1",
        "password_hash": hash_password("mypassword"),
        "email_confirmed": False,
    }]
    r = client.post("/auth/login", json={"email": "u@test.com", "password": "mypassword"})
    assert r.status_code == 403


def test_get_me_no_token(client):
    r = client.get("/users/me")
    assert r.status_code == 403  # HTTPBearer returns 403 when header missing


def test_get_me_invalid_token(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code == 401


def test_get_me_valid_token(client, mock_db):
    from app.auth.utils import create_access_token
    token = create_access_token("uid-abc")
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "uid-abc",
        "email": "u@test.com",
        "email_confirmed": True,
        "full_name": "Ana Banana",
        "phone": None,
        "zip_code": "10001",
        "city": "New York",
        "state": "NY",
        "created_at": "2026-01-01T00:00:00+00:00",
    }]
    r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "u@test.com"


def test_cross_tenant_isolation(client, mock_db):
    """PUT /users/me must only update the authenticated user's own record."""
    from app.auth.utils import create_access_token
    token_user_a = create_access_token("uid-a")

    updated_row = {
        "id": "uid-a", "email": "a@test.com", "email_confirmed": True,
        "full_name": "Updated Name", "phone": None, "zip_code": None,
        "city": None, "state": None, "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [updated_row]

    r = client.put(
        "/users/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert r.status_code == 200
    # Verify the update was called with user A's id — never user B's
    mock_db.table.return_value.update.return_value.eq.assert_called_once_with("id", "uid-a")
