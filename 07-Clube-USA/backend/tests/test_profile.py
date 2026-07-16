"""
Testes de perfil — Fase 0.1.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock


def _make_user_row(user_id="user-uuid-1", zip_code="10001"):
    return {
        "id": user_id,
        "email": "user@example.com",
        "email_confirmed": True,
        "full_name": "Test User",
        "zip_code": zip_code,
        "phone": None,
        "created_at": datetime.now(timezone.utc),
        "last_login_at": None,
    }


class TestGetProfile:
    def test_unauthenticated_returns_403(self, client):
        resp = client.get("/api/profile/me")
        assert resp.status_code == 403

    def test_invalid_token_returns_401(self, client):
        resp = client.get(
            "/api/profile/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_valid_token_returns_profile(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("user-uuid-1")
        mock_conn.fetchrow = AsyncMock(return_value=_make_user_row())

        resp = client.get(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "Test User"
        assert data["zip_code"] == "10001"
        assert "password" not in data  # nunca expor senha

    def test_response_never_exposes_password(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("user-uuid-1")
        mock_conn.fetchrow = AsyncMock(return_value=_make_user_row())

        resp = client.get(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        body = resp.text
        assert "password" not in body
        assert "hash" not in body


class TestUpdateProfile:
    def test_update_no_fields_returns_400(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("user-uuid-1")

        resp = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert resp.status_code == 400

    def test_update_invalid_zip_returns_422(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("user-uuid-1")

        resp = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"zip_code": "NOTAZIP"},
        )
        assert resp.status_code == 422

    def test_update_valid_zip_succeeds(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("user-uuid-1")
        mock_conn.fetchrow = AsyncMock(return_value=_make_user_row(zip_code="90210"))

        resp = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"zip_code": "90210"},
        )
        assert resp.status_code == 200
        assert resp.json()["zip_code"] == "90210"

    def test_update_user_not_found_returns_404(self, client, mock_conn):
        from app.utils.security import create_access_token
        token, _ = create_access_token("nonexistent-uuid")
        mock_conn.fetchrow = AsyncMock(return_value=None)

        resp = client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Novo Nome"},
        )
        assert resp.status_code == 404
