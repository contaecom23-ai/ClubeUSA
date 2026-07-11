"""Tests for /api/profile/* endpoints.

Key assertions:
- Unauthenticated requests return 401/403.
- user_id ALWAYS comes from JWT — never from request body.
- Cross-tenant IDOR is structurally impossible with /me endpoints,
  but we verify the query filter is applied correctly.
"""
import uuid
from unittest.mock import MagicMock

import pytest

from api.services.token_service import create_access_token


def _db_ok(data=None):
    m = MagicMock()
    m.data = data or []
    return m


def _auth_header(user_id: str) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestGetProfile:
    URL = "/api/profile/me"

    def test_get_profile_authenticated(self, client, mock_db, sample_user, sample_user_id):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": sample_user_id,
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "email_confirmed": True,
                    "created_at": "2026-07-10T00:00:00+00:00",
                }
            ]
        )
        resp = client.get(self.URL, headers=_auth_header(sample_user_id))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "test@example.com"
        assert "password_hash" not in body  # never leak hash

    def test_get_profile_unauthenticated(self, client):
        resp = client.get(self.URL)
        assert resp.status_code in (401, 403)

    def test_get_profile_invalid_token(self, client):
        resp = client.get(self.URL, headers={"Authorization": "Bearer garbage.token.here"})
        assert resp.status_code in (401, 403)

    def test_user_id_from_token_not_body(self, client, mock_db, sample_user_id):
        """Query must filter by the token's user_id, not any id in request body."""
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": sample_user_id,
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "email_confirmed": True,
                    "created_at": "2026-07-10T00:00:00+00:00",
                }
            ]
        )
        # GET /me — no way to pass a different user_id in the request
        resp = client.get(self.URL, headers=_auth_header(sample_user_id))
        assert resp.status_code == 200
        # Verify the eq filter was called with the token's user_id
        call_args = mock_db.table.return_value.select.return_value.eq.call_args
        assert call_args[0][0] == "id"
        assert call_args[0][1] == sample_user_id


class TestUpdateProfile:
    URL = "/api/profile/me"

    def test_update_full_name(self, client, mock_db, sample_user_id):
        mock_db.table.return_value.update.return_value.eq.return_value.select.return_value.execute.return_value = _db_ok(
            [
                {
                    "id": sample_user_id,
                    "email": "test@example.com",
                    "full_name": "Novo Nome",
                    "email_confirmed": True,
                    "created_at": "2026-07-10T00:00:00+00:00",
                }
            ]
        )
        resp = client.patch(
            self.URL,
            json={"full_name": "Novo Nome"},
            headers=_auth_header(sample_user_id),
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Novo Nome"

    def test_update_no_fields(self, client, mock_db, sample_user_id):
        resp = client.patch(self.URL, json={}, headers=_auth_header(sample_user_id))
        assert resp.status_code == 400

    def test_update_xss_name(self, client, mock_db, sample_user_id):
        resp = client.patch(
            self.URL,
            json={"full_name": "<img src=x onerror=alert(1)>"},
            headers=_auth_header(sample_user_id),
        )
        assert resp.status_code == 422

    def test_update_unauthenticated(self, client):
        resp = client.patch(self.URL, json={"full_name": "Hacker"})
        assert resp.status_code in (401, 403)
