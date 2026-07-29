"""
Tests for Fase 0.1 — Cadastro + perfil mínimo + email confirmado.

Covers:
- Registration (success, duplicate email, weak password)
- Email confirmation (success, invalid token, expired token)
- Login (success, wrong password, unconfirmed email)
- Profile get/update (authenticated, unauthenticated)
- IDOR: profile always uses token user_id, never a client-supplied id
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_user_row


# ─── Registration ────────────────────────────────────────────────────────────


def test_register_success(client, db_mock):
    # No existing user with this email
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    db_mock.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[make_user_row(email="novo@example.com", email_confirmed=False)]
    )

    with patch("main.send_confirmation_email") as mock_email:
        resp = client.post(
            "/auth/register",
            json={"email": "novo@example.com", "password": "senha123", "full_name": "Maria Costa"},
        )

    assert resp.status_code == 201
    assert "Conta criada" in resp.json()["message"]
    mock_email.assert_called_once()


def test_register_duplicate_email(client, db_mock):
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[make_user_row()]
    )

    resp = client.post(
        "/auth/register",
        json={"email": "joao@example.com", "password": "senha123", "full_name": "João"},
    )

    assert resp.status_code == 400
    # Must NOT say "email já existe" (would confirm existence — user enumeration)
    assert "não foi possível" in resp.json()["detail"].lower()


def test_register_weak_password(client, db_mock):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "abc", "full_name": "Test"},
    )
    assert resp.status_code == 422


def test_register_blank_name(client, db_mock):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "senha123", "full_name": "   "},
    )
    assert resp.status_code == 422


# ─── Email Confirmation ───────────────────────────────────────────────────────


def test_confirm_email_success(client, db_mock):
    future_time = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    user = make_user_row(
        email_confirmed=False,
        confirmation_token="valid-token-abc",
        confirmation_expires=future_time,
    )
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )
    db_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    with patch("main.send_welcome_email") as mock_welcome:
        resp = client.get("/auth/confirm-email?token=valid-token-abc")

    assert resp.status_code == 200
    assert "confirmado" in resp.json()["message"].lower()
    mock_welcome.assert_called_once()


def test_confirm_email_invalid_token(client, db_mock):
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    resp = client.get("/auth/confirm-email?token=nonexistent-token")
    assert resp.status_code == 400
    assert "inválido" in resp.json()["detail"].lower()


def test_confirm_email_expired_token(client, db_mock):
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    user = make_user_row(
        email_confirmed=False,
        confirmation_token="expired-token",
        confirmation_expires=past_time,
    )
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.get("/auth/confirm-email?token=expired-token")
    assert resp.status_code == 400
    assert "expirado" in resp.json()["detail"].lower()


def test_confirm_email_already_confirmed(client, db_mock):
    user = make_user_row(email_confirmed=True)
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.get("/auth/confirm-email?token=any-token")
    assert resp.status_code == 200
    assert "já confirmado" in resp.json()["message"].lower()


# ─── Login ────────────────────────────────────────────────────────────────────


def test_login_success(client, db_mock):
    user = make_user_row(email_confirmed=True)
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.post("/auth/login", json={"email": "joao@example.com", "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "joao@example.com"
    assert "password_hash" not in str(body)  # never leak password hash


def test_login_wrong_password(client, db_mock):
    user = make_user_row(email_confirmed=True)
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.post("/auth/login", json={"email": "joao@example.com", "password": "wrong!"})
    assert resp.status_code == 401


def test_login_user_not_found(client, db_mock):
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    resp = client.post("/auth/login", json={"email": "ghost@example.com", "password": "senha123"})
    # Same 401 as wrong password — no user enumeration via status code
    assert resp.status_code == 401


def test_login_unconfirmed_email(client, db_mock):
    user = make_user_row(email_confirmed=False)
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.post("/auth/login", json={"email": "joao@example.com", "password": "senha123"})
    assert resp.status_code == 403
    assert "não confirmado" in resp.json()["detail"].lower()


# ─── Profile ─────────────────────────────────────────────────────────────────


def _get_token(client, db_mock) -> str:
    user = make_user_row(email_confirmed=True)
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )
    resp = client.post("/auth/login", json={"email": "joao@example.com", "password": "senha123"})
    return resp.json()["access_token"]


def test_get_profile_authenticated(client, db_mock):
    token = _get_token(client, db_mock)
    user = make_user_row()
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[user]
    )

    resp = client.get("/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "joao@example.com"
    assert "password_hash" not in str(body)


def test_get_profile_unauthenticated(client, db_mock):
    resp = client.get("/profile/me")
    assert resp.status_code == 401


def test_get_profile_invalid_token(client, db_mock):
    resp = client.get("/profile/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_update_profile_name(client, db_mock):
    token = _get_token(client, db_mock)
    updated = make_user_row(full_name="João Atualizado")
    db_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[updated]
    )

    resp = client.put(
        "/profile/me",
        json={"full_name": "João Atualizado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "João Atualizado"


def test_update_profile_empty_name_rejected(client, db_mock):
    token = _get_token(client, db_mock)
    resp = client.put(
        "/profile/me",
        json={"full_name": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_update_profile_no_fields_rejected(client, db_mock):
    token = _get_token(client, db_mock)
    resp = client.put(
        "/profile/me",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ─── IDOR Protection ─────────────────────────────────────────────────────────


def test_idor_profile_uses_token_user_id(client, db_mock):
    """
    Even if a client somehow injects a different user_id, /profile/me
    ALWAYS queries by the user_id extracted from the JWT, never from request body.
    Verified by checking which .eq() call reaches the DB.
    """
    token = _get_token(client, db_mock)
    own_user = make_user_row(user_id="user-123")
    db_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[own_user]
    )

    # Note: /profile/me has no id parameter in the URL — the endpoint enforces
    # this by design (no client-controlled id path param exists).
    resp = client.get("/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == "user-123"

    # Verify the DB was queried with the token's user_id (eq called with "user-123")
    eq_calls = db_mock.table.return_value.select.return_value.eq.call_args_list
    assert any(str("user-123") in str(call) for call in eq_calls)
