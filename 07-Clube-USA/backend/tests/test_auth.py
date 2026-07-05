"""Tests for /api/v1/auth — register, login, verify-email, resend-verification."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call

import pytest

from app.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers to wire up mock_db method-chain return values
# ---------------------------------------------------------------------------

def _setup_select_none(mock_db: MagicMock, table: str) -> None:
    """Make db.table(table).select(...).eq(...).execute() return empty data."""
    mock_db.table(table).select.return_value.eq.return_value.execute.return_value.data = []


def _table_mock(mock_db: MagicMock, table: str) -> MagicMock:
    return mock_db.table(table)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_success(self, client: "TestClient", mock_db: MagicMock):
        # No duplicate user
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        # User insert returns new user
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "user-001"}
        ]

        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "Secure1Pass",
            "full_name": "Maria Silva",
        })
        assert resp.status_code == 201
        assert "Cadastro realizado" in resp.json()["message"]

    def test_duplicate_email_returns_400(self, client: "TestClient", mock_db: MagicMock):
        # Existing user found
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-existing"}
        ]

        resp = client.post("/api/v1/auth/register", json={
            "email": "taken@example.com",
            "password": "Secure1Pass",
            "full_name": "Already Exists",
        })
        # Must be 400, NOT 409 — don't reveal account existence
        assert resp.status_code == 400

    def test_weak_password_no_uppercase(self, client: "TestClient", mock_db: MagicMock):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "alllower1",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_weak_password_no_digit(self, client: "TestClient", mock_db: MagicMock):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "NoDigitHere",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_weak_password_too_short(self, client: "TestClient", mock_db: MagicMock):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "Ab1",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_invalid_email_rejected(self, client: "TestClient", mock_db: MagicMock):
        resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Secure1Pass",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_empty_name_rejected(self, client: "TestClient", mock_db: MagicMock):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com",
            "password": "Secure1Pass",
            "full_name": "  ",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def _setup_user(self, mock_db: MagicMock, verified: bool = True) -> None:
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "user-001",
                "email": "user@example.com",
                "password_hash": hash_password("Correct1"),
                "is_email_verified": verified,
            }
        ]

    def test_success(self, client: "TestClient", mock_db: MagicMock):
        self._setup_user(mock_db, verified=True)
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "Correct1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client: "TestClient", mock_db: MagicMock):
        self._setup_user(mock_db, verified=True)
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "Wrong1Pass",
        })
        assert resp.status_code == 401

    def test_user_not_found_returns_401(self, client: "TestClient", mock_db: MagicMock):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Secure1Pass",
        })
        assert resp.status_code == 401
        # Same error message as wrong password — prevents user enumeration
        assert "inválidos" in resp.json()["detail"]

    def test_unverified_email_returns_403(self, client: "TestClient", mock_db: MagicMock):
        self._setup_user(mock_db, verified=False)
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "Correct1",
        })
        assert resp.status_code == 403
        assert "confirmado" in resp.json()["detail"]

    def test_jwt_contains_user_id(self, client: "TestClient", mock_db: MagicMock):
        self._setup_user(mock_db, verified=True)
        resp = client.post("/api/v1/auth/login", json={
            "email": "user@example.com",
            "password": "Correct1",
        })
        assert resp.json()["user_id"] == "user-001"


# ---------------------------------------------------------------------------
# Verify Email
# ---------------------------------------------------------------------------

class TestVerifyEmail:
    def _valid_token_rec(self) -> dict:
        future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        return {"id": "tok-001", "user_id": "user-001", "expires_at": future, "used_at": None}

    def test_success(self, client: "TestClient", mock_db: MagicMock):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            self._valid_token_rec()
        ]
        resp = client.get("/api/v1/auth/verify-email?token=validtoken123")
        assert resp.status_code == 200
        assert "confirmado" in resp.json()["message"]

    def test_invalid_token(self, client: "TestClient", mock_db: MagicMock):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        resp = client.get("/api/v1/auth/verify-email?token=doesnotexist")
        assert resp.status_code == 400

    def test_already_used_token(self, client: "TestClient", mock_db: MagicMock):
        rec = self._valid_token_rec()
        rec["used_at"] = "2025-01-01T00:00:00+00:00"
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [rec]
        resp = client.get("/api/v1/auth/verify-email?token=usedtoken")
        assert resp.status_code == 400
        assert "já foi utilizado" in resp.json()["detail"]

    def test_expired_token(self, client: "TestClient", mock_db: MagicMock):
        rec = self._valid_token_rec()
        rec["expires_at"] = "2020-01-01T00:00:00+00:00"  # Past
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [rec]
        resp = client.get("/api/v1/auth/verify-email?token=expiredtoken")
        assert resp.status_code == 400
        assert "expirado" in resp.json()["detail"]

    def test_empty_token_rejected(self, client: "TestClient", mock_db: MagicMock):
        resp = client.get("/api/v1/auth/verify-email?token=")
        assert resp.status_code == 400

    def test_oversized_token_rejected(self, client: "TestClient", mock_db: MagicMock):
        huge = "x" * 200
        resp = client.get(f"/api/v1/auth/verify-email?token={huge}")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Resend Verification
# ---------------------------------------------------------------------------

class TestResendVerification:
    def test_always_returns_200(self, client: "TestClient", mock_db: MagicMock):
        # Even when user doesn't exist — prevent enumeration
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        resp = client.post("/api/v1/auth/resend-verification", json={"email": "ghost@example.com"})
        assert resp.status_code == 200

    def test_sends_new_token_for_unverified(self, client: "TestClient", mock_db: MagicMock):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-001", "is_email_verified": False}
        ]
        resp = client.post("/api/v1/auth/resend-verification", json={"email": "pend@example.com"})
        assert resp.status_code == 200

    def test_skips_already_verified(self, client: "TestClient", mock_db: MagicMock):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-001", "is_email_verified": True}
        ]
        resp = client.post("/api/v1/auth/resend-verification", json={"email": "done@example.com"})
        # Returns 200 with generic message — doesn't reveal verification state
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health(client: "TestClient", mock_db: MagicMock):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
