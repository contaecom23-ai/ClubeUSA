"""Tests for /api/auth/* endpoints."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.services import password_service, token_service


def _db_ok(data=None):
    """Return a mock Supabase response with data."""
    m = MagicMock()
    m.data = data or []
    return m


class TestRegister:
    URL = "/api/auth/register"
    VALID_BODY = {
        "email": "novo@example.com",
        "password": "senha-forte-123",
        "full_name": "João Silva",
    }

    def test_register_success(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok([])
        mock_db.table.return_value.insert.return_value.execute.return_value = _db_ok(
            [{"id": str(uuid.uuid4())}]
        )

        with patch("api.services.email_service.send_confirmation_email"):
            resp = client.post(self.URL, json=self.VALID_BODY)

        assert resp.status_code == 201
        assert "Conta criada" in resp.json()["message"]

    def test_register_duplicate_email(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [{"id": str(uuid.uuid4())}]
        )

        resp = client.post(self.URL, json=self.VALID_BODY)
        assert resp.status_code == 409

    def test_register_password_too_short(self, client, mock_db):
        body = {**self.VALID_BODY, "password": "short"}
        resp = client.post(self.URL, json=body)
        assert resp.status_code == 422

    def test_register_invalid_email(self, client, mock_db):
        body = {**self.VALID_BODY, "email": "not-an-email"}
        resp = client.post(self.URL, json=body)
        assert resp.status_code == 422

    def test_register_name_xss(self, client, mock_db):
        body = {**self.VALID_BODY, "full_name": "<script>alert(1)</script>"}
        resp = client.post(self.URL, json=body)
        assert resp.status_code == 422


class TestVerifyEmail:
    URL = "/api/auth/verify-email"

    def _make_token(self):
        return str(uuid.uuid4())

    def _future_expiry(self):
        return (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()

    def _past_expiry(self):
        return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    def test_verify_success(self, client, mock_db):
        token = self._make_token()
        uid = str(uuid.uuid4())
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": uid,
                    "email": "test@example.com",
                    "full_name": "Test",
                    "email_confirmed": False,
                    "email_confirm_expires_at": self._future_expiry(),
                }
            ]
        )
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = _db_ok()

        with patch("api.services.email_service.send_welcome_email"):
            resp = client.post(self.URL, json={"token": token})

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_verify_invalid_token(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok([])
        resp = client.post(self.URL, json={"token": str(uuid.uuid4())})
        assert resp.status_code == 400

    def test_verify_expired_token(self, client, mock_db):
        token = self._make_token()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": str(uuid.uuid4()),
                    "email": "test@example.com",
                    "full_name": "Test",
                    "email_confirmed": False,
                    "email_confirm_expires_at": self._past_expiry(),
                }
            ]
        )
        resp = client.post(self.URL, json={"token": token})
        assert resp.status_code == 400
        assert "expirado" in resp.json()["detail"].lower()

    def test_verify_already_confirmed(self, client, mock_db):
        token = self._make_token()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": str(uuid.uuid4()),
                    "email": "test@example.com",
                    "full_name": "Test",
                    "email_confirmed": True,
                    "email_confirm_expires_at": self._future_expiry(),
                }
            ]
        )
        resp = client.post(self.URL, json={"token": token})
        assert resp.status_code == 400


class TestLogin:
    URL = "/api/auth/login"

    def _hashed(self, password: str) -> str:
        return password_service.hash_password(password)

    def test_login_success(self, client, mock_db):
        uid = str(uuid.uuid4())
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": uid,
                    "password_hash": self._hashed("senha-forte-123"),
                    "email_confirmed": True,
                }
            ]
        )
        resp = client.post(self.URL, json={"email": "test@example.com", "password": "senha-forte-123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in_days"] == 1  # access token is 1 day

    def test_login_wrong_password(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": str(uuid.uuid4()),
                    "password_hash": self._hashed("correct-password"),
                    "email_confirmed": True,
                }
            ]
        )
        resp = client.post(self.URL, json={"email": "test@example.com", "password": "wrong-password"})
        assert resp.status_code == 401

    def test_login_unknown_email(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok([])
        resp = client.post(self.URL, json={"email": "nobody@example.com", "password": "any-password"})
        assert resp.status_code == 401

    def test_login_unconfirmed_email(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": str(uuid.uuid4()),
                    "password_hash": self._hashed("senha-forte-123"),
                    "email_confirmed": False,
                }
            ]
        )
        resp = client.post(self.URL, json={"email": "test@example.com", "password": "senha-forte-123"})
        assert resp.status_code == 403
        assert "confirmado" in resp.json()["detail"].lower()


class TestRefresh:
    URL = "/api/auth/refresh"

    def test_refresh_with_valid_refresh_token(self, client, mock_db):
        uid = str(uuid.uuid4())
        refresh_tok = token_service.create_refresh_token(uid)

        resp = client.post(self.URL, json={"refresh_token": refresh_tok})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["expires_in_days"] == 1

    def test_refresh_with_access_token_rejected(self, client, mock_db):
        uid = str(uuid.uuid4())
        access_tok = token_service.create_access_token(uid)

        resp = client.post(self.URL, json={"refresh_token": access_tok})
        assert resp.status_code == 401

    def test_refresh_with_garbage_token(self, client, mock_db):
        resp = client.post(self.URL, json={"refresh_token": "not.a.real.token"})
        assert resp.status_code == 401

    def test_refresh_returns_same_refresh_token(self, client, mock_db):
        uid = str(uuid.uuid4())
        refresh_tok = token_service.create_refresh_token(uid)

        resp = client.post(self.URL, json={"refresh_token": refresh_tok})
        assert resp.status_code == 200
        assert resp.json()["refresh_token"] == refresh_tok
