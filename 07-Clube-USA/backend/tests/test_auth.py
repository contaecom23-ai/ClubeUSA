"""
Tests for /auth endpoints.

All Supabase calls are mocked — these tests run without any real credentials.
"""
from unittest.mock import MagicMock

from tests.conftest import TEST_EMAIL, TEST_USER_ID, next_ip


# ── /auth/register ────────────────────────────────────────────────────────────

def test_register_success(client, mock_supabase):
    mock_user = MagicMock()
    mock_user.id = TEST_USER_ID
    mock_supabase.auth.admin.create_user.return_value = MagicMock(user=mock_user)
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "Password1", "full_name": "João Silva"},
        headers=next_ip(),
    )

    assert res.status_code == 201
    body = res.json()
    assert "user_id" in body
    assert body["user_id"] == TEST_USER_ID


def test_register_weak_password_too_short(client, mock_supabase):
    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "abc", "full_name": "João"},
        headers=next_ip(),
    )
    assert res.status_code == 422


def test_register_weak_password_no_uppercase(client, mock_supabase):
    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "password1", "full_name": "João"},
        headers=next_ip(),
    )
    assert res.status_code == 422


def test_register_weak_password_no_number(client, mock_supabase):
    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "Password", "full_name": "João"},
        headers=next_ip(),
    )
    assert res.status_code == 422


def test_register_invalid_email(client, mock_supabase):
    res = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "Password1", "full_name": "João"},
        headers=next_ip(),
    )
    assert res.status_code == 422


def test_register_empty_name(client, mock_supabase):
    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "Password1", "full_name": "J"},
        headers=next_ip(),
    )
    assert res.status_code == 422


def test_register_duplicate_email(client, mock_supabase):
    mock_supabase.auth.admin.create_user.side_effect = Exception("User already registered")

    res = client.post(
        "/auth/register",
        json={"email": TEST_EMAIL, "password": "Password1", "full_name": "João Silva"},
        headers=next_ip(),
    )

    assert res.status_code == 400
    assert "já cadastrado" in res.json()["detail"]


# ── /auth/login ───────────────────────────────────────────────────────────────

def test_login_success(client, mock_supabase):
    mock_session = MagicMock()
    mock_session.access_token = "valid-jwt"
    mock_user = MagicMock()
    mock_user.id = TEST_USER_ID
    mock_user.email = TEST_EMAIL
    mock_supabase.auth.sign_in_with_password.return_value = MagicMock(
        session=mock_session, user=mock_user
    )

    res = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "Password1"},
        headers=next_ip(),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] == "valid-jwt"
    assert body["token_type"] == "bearer"
    assert body["user_id"] == TEST_USER_ID
    assert body["email"] == TEST_EMAIL


def test_login_wrong_password(client, mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    res = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "WrongPass1"},
        headers=next_ip(),
    )

    assert res.status_code == 401
    assert "inválidos" in res.json()["detail"]


def test_login_no_session_returned(client, mock_supabase):
    mock_supabase.auth.sign_in_with_password.return_value = MagicMock(
        session=None, user=MagicMock()
    )

    res = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": "Password1"},
        headers=next_ip(),
    )

    assert res.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_me_authenticated(client, mock_supabase):
    from tests.conftest import make_confirmed_user
    from datetime import datetime, timezone

    mock_user_obj = MagicMock()
    mock_user_obj.id = TEST_USER_ID
    mock_user_obj.email = TEST_EMAIL
    mock_user_obj.email_confirmed_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mock_supabase.auth.admin.get_user.return_value = MagicMock(user=mock_user_obj)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"full_name": "João Silva"}
    )

    res = client.get("/auth/me", headers={"Authorization": "Bearer test-token"})

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == TEST_USER_ID
    assert body["email"] == TEST_EMAIL
    assert body["email_confirmed"] is True
    assert body["full_name"] == "João Silva"


def test_me_unauthenticated(client, mock_supabase):
    res = client.get("/auth/me")
    assert res.status_code == 403  # HTTPBearer returns 403 when no Authorization header


def test_me_invalid_token(client, mock_supabase):
    mock_supabase.auth.admin.get_user.side_effect = Exception("invalid JWT")

    res = client.get("/auth/me", headers={"Authorization": "Bearer bad-token"})

    assert res.status_code == 401


# ── /auth/resend-confirmation ─────────────────────────────────────────────────

def test_resend_confirmation_always_200(client, mock_supabase):
    """Should return 200 even for unknown email (anti-enumeration)."""
    mock_supabase.auth.resend.side_effect = Exception("user not found")

    res = client.post(
        "/auth/resend-confirmation",
        json={"email": "unknown@example.com"},
        headers=next_ip(),
    )

    assert res.status_code == 200
    assert "link de confirmação" in res.json()["message"]
