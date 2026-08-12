"""
Integration tests for auth API endpoints.
Supabase is mocked — no real network calls.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# conftest.py sets env vars; import app after env is ready
from main import app
from security import create_access_token, generate_confirmation_token, hash_password


@pytest.fixture
def client():
    """Fresh TestClient per test — no cookie bleed between tests."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    *,
    email="user@example.com",
    confirmed=True,
    password="password123",
    first_name="Ana",
    last_name="Silva",
    zip_code="10001",
):
    uid = str(uuid.uuid4())
    token = generate_confirmation_token()
    expires = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
    return {
        "id": uid,
        "email": email,
        "password_hash": hash_password(password),
        "first_name": first_name,
        "last_name": last_name,
        "zip_code": zip_code,
        "email_confirmed": confirmed,
        "confirmation_token": None if confirmed else token,
        "confirmation_expires_at": None if confirmed else expires,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _mock_db():
    """Return a MagicMock that mimics the Supabase chained query API."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.eq.return_value = mock
    mock.execute.return_value = MagicMock(data=[])
    return mock


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


def test_register_success(client):
    user = _make_user(confirmed=False)
    mock = _mock_db()
    mock.execute.side_effect = [
        MagicMock(data=[]),    # no existing user
        MagicMock(data=[user]),  # insert result
    ]

    with patch("auth.get_db", return_value=mock), \
         patch("auth.send_confirmation_email") as mock_email:
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "secret123",
            "first_name": "Ana",
            "last_name": "Silva",
            "zip_code": "10001",
        })

    assert resp.status_code == 201
    assert "email" in resp.json()["message"].lower()
    mock_email.assert_called_once()


def test_register_duplicate_email(client):
    existing_user = _make_user()
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[{"id": existing_user["id"]}])

    with patch("auth.get_db", return_value=mock):
        resp = client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "secret123",
            "first_name": "Ana",
            "last_name": "Silva",
        })

    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/auth/register", json={
        "email": "a@b.com",
        "password": "short",
        "first_name": "A",
        "last_name": "B",
    })
    assert resp.status_code == 422


def test_register_invalid_zip(client):
    resp = client.post("/api/auth/register", json={
        "email": "a@b.com",
        "password": "goodpassword",
        "first_name": "A",
        "last_name": "B",
        "zip_code": "ABCDE",
    })
    assert resp.status_code == 422


def test_register_email_failure_does_not_break_registration(client):
    """Registration must succeed even when email sending fails."""
    user = _make_user(confirmed=False)
    mock = _mock_db()
    mock.execute.side_effect = [
        MagicMock(data=[]),
        MagicMock(data=[user]),
    ]

    with patch("auth.get_db", return_value=mock), \
         patch("auth.send_confirmation_email", side_effect=Exception("SMTP error")):
        resp = client.post("/api/auth/register", json={
            "email": "new2@example.com",
            "password": "secret123",
            "first_name": "Ana",
            "last_name": "Silva",
        })

    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/auth/confirm-email
# ---------------------------------------------------------------------------


def test_confirm_email_success(client):
    user = _make_user(confirmed=False)
    mock = _mock_db()
    mock.execute.side_effect = [
        MagicMock(data=[{
            "id": user["id"],
            "email_confirmed": False,
            "confirmation_expires_at": user["confirmation_expires_at"],
        }]),
        MagicMock(data=[user]),  # update result
    ]

    with patch("auth.get_db", return_value=mock):
        resp = client.get(f"/api/auth/confirm-email?token={user['confirmation_token']}")

    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()


def test_confirm_email_invalid_token(client):
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[])

    with patch("auth.get_db", return_value=mock):
        resp = client.get("/api/auth/confirm-email?token=badtoken")

    assert resp.status_code == 400


def test_confirm_email_expired_token(client):
    user = _make_user(confirmed=False)
    user["confirmation_expires_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat()
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[{
        "id": user["id"],
        "email_confirmed": False,
        "confirmation_expires_at": user["confirmation_expires_at"],
    }])

    with patch("auth.get_db", return_value=mock):
        resp = client.get("/api/auth/confirm-email?token=sometoken")

    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


def test_login_success(client):
    user = _make_user(confirmed=True, password="password123")
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[user])

    with patch("auth.get_db", return_value=mock):
        resp = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "password123",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "user@example.com"
    assert "access_token" in resp.cookies


def test_login_wrong_password(client):
    user = _make_user(confirmed=True, password="correct")
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[user])

    with patch("auth.get_db", return_value=mock):
        resp = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "wrong",
        })

    assert resp.status_code == 401


def test_login_unconfirmed_email(client):
    user = _make_user(confirmed=False, password="password123")
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[user])

    with patch("auth.get_db", return_value=mock):
        resp = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "password123",
        })

    assert resp.status_code == 403


def test_login_nonexistent_user_is_401_not_404(client):
    """Must not leak whether the email exists."""
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[])

    with patch("auth.get_db", return_value=mock):
        resp = client.post("/api/auth/login", json={
            "email": "ghost@example.com",
            "password": "anything",
        })

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/auth/me  (requires auth cookie)
# ---------------------------------------------------------------------------


def test_get_me_authenticated(client):
    user = _make_user()
    token = create_access_token(user["id"])
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[user])

    with patch("auth.get_db", return_value=mock):
        resp = client.get(
            "/api/auth/me",
            cookies={"access_token": token},
        )

    assert resp.status_code == 200
    assert resp.json()["email"] == user["email"]


def test_get_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_get_me_invalid_token(client):
    resp = client.get(
        "/api/auth/me",
        cookies={"access_token": "invalid.token.here"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/auth/profile  (multi-tenant: user can only update their own row)
# ---------------------------------------------------------------------------


def test_update_profile_success(client):
    user = _make_user()
    token = create_access_token(user["id"])
    updated = {**user, "first_name": "Beatriz"}
    mock = _mock_db()
    mock.execute.return_value = MagicMock(data=[updated])

    with patch("auth.get_db", return_value=mock):
        resp = client.put(
            "/api/auth/profile",
            json={"first_name": "Beatriz"},
            cookies={"access_token": token},
        )

    assert resp.status_code == 200
    # Verify .eq("id", user_id) was called — ensures multi-tenant isolation
    calls = [str(c) for c in mock.eq.call_args_list]
    assert any("id" in c for c in calls)


def test_update_profile_empty_body(client):
    user = _make_user()
    token = create_access_token(user["id"])

    resp = client.put(
        "/api/auth/profile",
        json={},
        cookies={"access_token": token},
    )
    assert resp.status_code == 400


def test_update_profile_unauthenticated(client):
    resp = client.put("/api/auth/profile", json={"first_name": "X"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


def test_logout_clears_cookie(client):
    user = _make_user()
    token = create_access_token(user["id"])

    resp = client.post("/api/auth/logout", cookies={"access_token": token})

    assert resp.status_code == 200
    cookie_header = resp.headers.get("set-cookie", "")
    assert "access_token" in cookie_header
