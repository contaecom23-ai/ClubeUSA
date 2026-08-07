from unittest.mock import patch

import pytest

from app.database import DuplicateError


class TestRegister:
    def test_success(self, client, mock_db, user_row):
        mock_db.create_user.return_value = user_row
        mock_db.create_confirmation_token.return_value = "tok123"

        with patch("app.routes.auth.send_confirmation_email") as mock_email:
            resp = client.post("/auth/register", json={
                "email": "joao@example.com",
                "password": "senha1234",
                "full_name": "João Silva",
            })

        assert resp.status_code == 201
        assert "e-mail" in resp.json()["message"].lower()
        mock_email.assert_called_once()

    def test_duplicate_email_returns_400(self, client, mock_db):
        mock_db.create_user.side_effect = DuplicateError("Email já cadastrado.")

        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "senha1234",
            "full_name": "João Silva",
        })

        assert resp.status_code == 400

    def test_password_too_short(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "curto",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    def test_invalid_email(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "senha1234",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    def test_name_too_short(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "senha1234",
            "full_name": "J",
        })
        assert resp.status_code == 422

    def test_xss_in_name_rejected(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "joao@example.com",
            "password": "senha1234",
            "full_name": "<script>alert(1)</script>",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_success_returns_token(self, client, mock_db, user_row):
        mock_db.get_user_by_email.return_value = user_row

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "senha1234",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "joao@example.com"

    def test_wrong_password_returns_401(self, client, mock_db, user_row):
        mock_db.get_user_by_email.return_value = user_row

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "wrong_password",
        })

        assert resp.status_code == 401

    def test_unknown_email_returns_401(self, client, mock_db):
        mock_db.get_user_by_email.return_value = None

        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "senha1234",
        })

        assert resp.status_code == 401

    def test_inactive_user_returns_403(self, client, mock_db, user_row):
        inactive = {**user_row, "is_active": False}
        mock_db.get_user_by_email.return_value = inactive

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "senha1234",
        })

        assert resp.status_code == 403

    def test_unconfirmed_user_can_login(self, client, mock_db, user_row):
        unconfirmed = {**user_row, "email_confirmed": False}
        mock_db.get_user_by_email.return_value = unconfirmed

        resp = client.post("/auth/login", json={
            "email": "joao@example.com",
            "password": "senha1234",
        })

        # Login allowed; client should show "confirm your email" banner
        assert resp.status_code == 200
        assert resp.json()["user"]["email_confirmed"] is False


class TestConfirmEmail:
    def test_success(self, client, mock_db):
        from datetime import datetime, timedelta, timezone
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        mock_db.get_confirmation_token.return_value = {
            "id": "tok-id-1",
            "user_id": "user-id-1",
            "token": "valid-token",
            "expires_at": expires,
            "used_at": None,
        }

        resp = client.get("/auth/confirm-email?token=valid-token")

        assert resp.status_code == 200
        mock_db.confirm_user_email.assert_called_once_with("user-id-1")
        mock_db.mark_confirmation_token_used.assert_called_once_with("tok-id-1")

    def test_invalid_token_returns_400(self, client, mock_db):
        mock_db.get_confirmation_token.return_value = None

        resp = client.get("/auth/confirm-email?token=bad-token")

        assert resp.status_code == 400

    def test_expired_token_returns_400(self, client, mock_db):
        from datetime import datetime, timedelta, timezone
        expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_db.get_confirmation_token.return_value = {
            "id": "tok-id-1",
            "user_id": "user-id-1",
            "token": "expired-token",
            "expires_at": expired,
            "used_at": None,
        }

        resp = client.get("/auth/confirm-email?token=expired-token")

        assert resp.status_code == 400
