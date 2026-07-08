"""Tests for /api/v1/auth endpoints."""

import uuid
from unittest.mock import MagicMock


# ------------------------------------------------------------------ register --


def test_register_success(client, mock_supabase):
    uid = str(uuid.uuid4())
    mock_user = MagicMock()
    mock_user.id = uid

    mock_supabase.auth.admin.create_user.return_value = MagicMock(user=mock_user)
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": uid}])

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Maria Silva",
            "email": "maria@example.com",
            "password": "senha1234",
            "zip_code": "33101",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "email" in body
    assert "confirmado" in body["message"].lower() or "confirmar" in body["message"].lower()


def test_register_duplicate_email(client, mock_supabase):
    mock_supabase.auth.admin.create_user.side_effect = Exception("User already registered")

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "João Outro",
            "email": "existente@example.com",
            "password": "senha1234",
            "zip_code": "10001",
        },
    )
    assert resp.status_code == 409
    assert "já cadastrado" in resp.json()["detail"].lower()


def test_register_weak_password(client, mock_supabase):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Ana Lima",
            "email": "ana@example.com",
            "password": "123",
            "zip_code": "10001",
        },
    )
    assert resp.status_code == 422


def test_register_invalid_zip(client, mock_supabase):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Pedro Costa",
            "email": "pedro@example.com",
            "password": "senha1234",
            "zip_code": "ABC12",
        },
    )
    assert resp.status_code == 422


def test_register_invalid_email(client, mock_supabase):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "not-an-email",
            "password": "senha1234",
            "zip_code": "10001",
        },
    )
    assert resp.status_code == 422


# -------------------------------------------------------------------- login --


def test_login_success_confirmed(client, mock_supabase, confirmed_user, make_session):
    session = make_session()
    mock_supabase.auth.sign_in_with_password.return_value = MagicMock(
        session=session, user=confirmed_user
    )

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "senha1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == confirmed_user.email


def test_login_unconfirmed_email(client, mock_supabase, unconfirmed_user, make_session):
    session = make_session()
    mock_supabase.auth.sign_in_with_password.return_value = MagicMock(
        session=session, user=unconfirmed_user
    )

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "senha1234"},
    )
    assert resp.status_code == 403
    assert "confirmado" in resp.json()["detail"].lower()


def test_login_wrong_password(client, mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "errada"},
    )
    assert resp.status_code == 401


# --------------------------------------------------------------- rate limit --


def test_register_rate_limit(client, mock_supabase):
    mock_supabase.auth.admin.create_user.side_effect = Exception("some error")

    for _ in range(3):
        client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Rate Limit",
                "email": f"rl{_}@example.com",
                "password": "senha1234",
                "zip_code": "10001",
            },
            headers={"X-Forwarded-For": "10.0.0.99"},
        )

    # 4th attempt from same IP should be rate-limited
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rate Limit",
            "email": "rl4@example.com",
            "password": "senha1234",
            "zip_code": "10001",
        },
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert resp.status_code == 429


# -------------------------------------------------------------- refresh token --


def test_refresh_token_success(client, mock_supabase, make_session):
    new_session = make_session(access_token="new-access", refresh_token="new-refresh")
    mock_supabase.auth.refresh_session.return_value = MagicMock(session=new_session)

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "valid-refresh-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "new-access"


def test_refresh_token_invalid(client, mock_supabase):
    mock_supabase.auth.refresh_session.side_effect = Exception("Invalid refresh token")

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "bad-token"},
    )
    assert resp.status_code == 401


# -------------------------------------------------------------------- /me --


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403


def test_me_returns_user_id(client, mock_supabase, auth_headers, user_id):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id
