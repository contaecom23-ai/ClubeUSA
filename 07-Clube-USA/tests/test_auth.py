"""Tests for Phase 0.1 — Register, Email Confirm, Login, Profile."""
import pytest
from conftest import _db


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    res = client.post("/auth/register", json={
        "email": "alice@test.com",
        "password": "password123",
        "full_name": "Alice Silva",
    })
    assert res.status_code == 201
    body = res.json()
    assert "criada" in body["message"].lower()
    assert "user_id" in body

    user = _db.find_by_email("alice@test.com")
    assert user is not None
    assert user["full_name"] == "Alice Silva"
    assert user["email_confirmed"] is False


def test_register_duplicate_email_returns_200(client):
    """Duplicate email must NOT return 409 — prevents email enumeration."""
    payload = {"email": "bob@test.com", "password": "password123", "full_name": "Bob"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 200  # Same 200, no info leakage


def test_register_short_password(client):
    res = client.post("/auth/register", json={
        "email": "carol@test.com", "password": "short", "full_name": "Carol"
    })
    assert res.status_code == 422


def test_register_invalid_email(client):
    res = client.post("/auth/register", json={
        "email": "not-an-email", "password": "password123", "full_name": "Dave"
    })
    assert res.status_code == 422


def test_register_empty_name(client):
    res = client.post("/auth/register", json={
        "email": "eve@test.com", "password": "password123", "full_name": ""
    })
    assert res.status_code == 422


# ── Email Confirmation ────────────────────────────────────────────────────────

def test_confirm_email_success(client, registered_user):
    token = registered_user["email_confirm_token"]
    res = client.get(f"/auth/confirm-email?token={token}")
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["email_confirmed"] is True


def test_confirm_email_invalid_token(client):
    res = client.get("/auth/confirm-email?token=totally-bogus-token")
    assert res.status_code == 404


def test_confirm_email_already_confirmed(client, registered_user):
    token = registered_user["email_confirm_token"]
    client.get(f"/auth/confirm-email?token={token}")  # First confirm
    # Token is now None in fake DB; second call should 404 (not find the token)
    res = client.get(f"/auth/confirm-email?token={token}")
    assert res.status_code == 404


def test_confirm_email_expired_token(client, registered_user):
    from datetime import timezone
    # Force-expire the token
    registered_user["email_confirm_expires_at"] = \
        registered_user["email_confirm_expires_at"].replace(year=2000)
    token = registered_user["email_confirm_token"]
    res = client.get(f"/auth/confirm-email?token={token}")
    assert res.status_code == 410


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client, registered_user, confirmed_user_token):
    res = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "securePass1",
    })
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user, confirmed_user_token):
    res = client.post("/auth/login", json={
        "email": "test@example.com", "password": "wrongPassword!"
    })
    assert res.status_code == 401


def test_login_wrong_email(client):
    res = client.post("/auth/login", json={
        "email": "nobody@test.com", "password": "password123"
    })
    assert res.status_code == 401


def test_login_unconfirmed_email(client, registered_user):
    """Login before confirming email must be rejected with 403."""
    res = client.post("/auth/login", json={
        "email": "test@example.com", "password": "securePass1"
    })
    assert res.status_code == 403
    assert "confirme" in res.json()["detail"].lower()


# ── Profile (authenticated routes) ────────────────────────────────────────────

def test_get_me_unauthenticated(client):
    res = client.get("/api/me")
    assert res.status_code == 403  # HTTPBearer returns 403 when no auth header


def test_get_me_authenticated(client, confirmed_user_token):
    res = client.get("/api/me", headers={"Authorization": f"Bearer {confirmed_user_token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["email"] == "test@example.com"
    assert "profile" in body


def test_get_me_invalid_token(client):
    res = client.get("/api/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


def test_update_profile(client, confirmed_user_token):
    res = client.put("/api/me",
        headers={"Authorization": f"Bearer {confirmed_user_token}"},
        json={"us_state": "FL", "us_city": "Miami", "bio": "Morei em SP antes."},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["full_name"] == "Test User"


def test_update_profile_invalid_state(client, confirmed_user_token):
    res = client.put("/api/me",
        headers={"Authorization": f"Bearer {confirmed_user_token}"},
        json={"us_state": "XX"},
    )
    assert res.status_code == 422


def test_update_profile_bio_too_long(client, confirmed_user_token):
    res = client.put("/api/me",
        headers={"Authorization": f"Bearer {confirmed_user_token}"},
        json={"bio": "x" * 501},
    )
    assert res.status_code == 422


# ── Referral stats ────────────────────────────────────────────────────────────

def test_referral_stats(client, confirmed_user_token):
    res = client.get("/api/referral-stats",
        headers={"Authorization": f"Bearer {confirmed_user_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "referral_code" in body
    assert "total_referrals" in body
    assert body["total_referrals"] == 0


# ── Status check ──────────────────────────────────────────────────────────────

def test_status(client):
    res = client.get("/status")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
