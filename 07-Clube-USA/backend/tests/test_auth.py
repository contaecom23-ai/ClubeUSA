"""Auth endpoint tests.

Covers: registration, email confirmation, login, token refresh, logout,
and key security invariants.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from core.security import generate_email_confirm_token
from tests.conftest import DBResult, auth_header, make_db_mock, make_user


# ── Registration ──────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        # Calls: 1=select(existing?), 2=insert(user), 3=insert(profile)
        db = make_db_mock(
            DBResult(data=[]),                        # no existing user
            DBResult(data=[{"id": "new-uuid"}]),      # user inserted
            DBResult(data=[{"id": "profile-uuid"}]),  # profile inserted
        )
        c, _ = client(db)

        with patch("services.auth_service.send_confirmation_email"):
            resp = c.post("/api/v1/auth/register", json={
                "email": "novo@example.com",
                "password": "Senha123!",
                "full_name": "Maria Silva",
            })

        assert resp.status_code == 201, resp.json()
        assert "email" in resp.json()["message"].lower()

    def test_register_duplicate_email(self, client):
        db = make_db_mock(DBResult(data=[{"id": "existing"}]))
        c, _ = client(db)

        resp = c.post("/api/v1/auth/register", json={
            "email": "existe@example.com",
            "password": "Senha123!",
            "full_name": "Alguém",
        })
        assert resp.status_code == 409

    def test_register_weak_password(self, client):
        c, _ = client(make_db_mock())
        resp = c.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "fraca",
            "full_name": "Alguém",
        })
        assert resp.status_code == 422

    def test_register_password_no_number_or_special(self, client):
        c, _ = client(make_db_mock())
        resp = c.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "SenhaLonga",
            "full_name": "Alguém",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        c, _ = client(make_db_mock())
        resp = c.post("/api/v1/auth/register", json={
            "email": "nao-e-email",
            "password": "Senha123!",
            "full_name": "Alguém",
        })
        assert resp.status_code == 422


# ── Email confirmation ────────────────────────────────────────────────────────

class TestConfirmEmail:
    def test_confirm_success(self, client):
        future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        raw_token = generate_email_confirm_token()

        # Calls: 1=select(token), 2=update(confirmed=True)
        db = make_db_mock(
            DBResult(data=[{"id": "user-uuid", "email_confirmed": False, "email_confirm_expires": future}]),
            DBResult(data=[{"id": "user-uuid"}]),  # update
        )
        c, _ = client(db)

        resp = c.get(f"/api/v1/auth/confirm-email?token={raw_token}")
        assert resp.status_code == 200
        assert "sucesso" in resp.json()["message"].lower()

    def test_confirm_invalid_token(self, client):
        db = make_db_mock(DBResult(data=[]))
        c, _ = client(db)

        resp = c.get("/api/v1/auth/confirm-email?token=badtoken")
        assert resp.status_code == 400

    def test_confirm_expired_token(self, client):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        raw_token = generate_email_confirm_token()

        db = make_db_mock(
            DBResult(data=[{"id": "user-uuid", "email_confirmed": False, "email_confirm_expires": past}]),
        )
        c, _ = client(db)

        resp = c.get(f"/api/v1/auth/confirm-email?token={raw_token}")
        assert resp.status_code == 400

    def test_confirm_already_confirmed(self, client):
        future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        raw_token = generate_email_confirm_token()

        db = make_db_mock(
            DBResult(data=[{"id": "user-uuid", "email_confirmed": True, "email_confirm_expires": future}]),
        )
        c, _ = client(db)

        resp = c.get(f"/api/v1/auth/confirm-email?token={raw_token}")
        assert resp.status_code == 200
        assert "já confirmado" in resp.json()["message"].lower()


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client):
        user = make_user()
        # Calls: 1=select(user by email), 2=insert(refresh token)
        db = make_db_mock(
            DBResult(data=[user]),
            DBResult(data=[{"id": "rt-uuid"}]),
        )
        c, _ = client(db)

        resp = c.post("/api/v1/auth/login", json={"email": user["email"], "password": "Password1!"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        user = make_user()
        db = make_db_mock(DBResult(data=[user]))
        c, _ = client(db)

        resp = c.post("/api/v1/auth/login", json={"email": user["email"], "password": "ErradaXX1!"})
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        db = make_db_mock(DBResult(data=[]))
        c, _ = client(db)

        resp = c.post("/api/v1/auth/login", json={"email": "nao@existe.com", "password": "Qualquer1!"})
        assert resp.status_code == 401

    def test_login_unconfirmed_email(self, client):
        user = make_user(confirmed=False)
        db = make_db_mock(DBResult(data=[user]))
        c, _ = client(db)

        resp = c.post("/api/v1/auth/login", json={"email": user["email"], "password": "Password1!"})
        assert resp.status_code == 403


# ── Protected route — auth required ──────────────────────────────────────────

class TestAuthRequired:
    def test_no_token_returns_403(self, client):
        c, _ = client(make_db_mock())
        resp = c.get("/api/v1/profile/me")
        assert resp.status_code in (401, 403)

    def test_invalid_token_returns_401(self, client):
        c, _ = client(make_db_mock())
        resp = c.get("/api/v1/profile/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401


# ── Refresh ───────────────────────────────────────────────────────────────────

class TestRefresh:
    def test_refresh_success(self, client):
        future = (datetime.now(timezone.utc) + timedelta(days=6)).isoformat()
        # Calls: 1=select(token), 2=update(revoked), 3=insert(new token)
        db = make_db_mock(
            DBResult(data=[{"id": "rt-uuid", "user_id": "user-uuid-1", "expires_at": future, "revoked_at": None}]),
            DBResult(data=[{"id": "rt-uuid"}]),      # revoke old
            DBResult(data=[{"id": "new-rt-uuid"}]),  # insert new
        )
        c, _ = client(db)

        resp = c.post("/api/v1/auth/refresh", json={"refresh_token": "some-valid-refresh-token"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_revoked_token(self, client):
        future = (datetime.now(timezone.utc) + timedelta(days=6)).isoformat()
        db = make_db_mock(
            DBResult(data=[{"id": "rt-uuid", "user_id": "user-uuid-1", "expires_at": future, "revoked_at": "2024-01-01T00:00:00+00:00"}]),
        )
        c, _ = client(db)

        resp = c.post("/api/v1/auth/refresh", json={"refresh_token": "any-token"})
        assert resp.status_code == 401
