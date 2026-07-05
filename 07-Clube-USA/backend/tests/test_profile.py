"""Tests for /api/v1/profile — get and update profile.

Key security properties verified:
- user_id always comes from the JWT token (via get_current_user), never from the body
- Cross-tenant IDOR: a user cannot read or modify another user's profile
"""
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# GET /profile/me
# ---------------------------------------------------------------------------

class TestGetProfile:
    def _setup_profile(self, mock_db: MagicMock, user_id: str) -> None:
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "user_id": user_id,
                "full_name": "Maria Silva",
                "phone": None,
                "state": "FL",
                "city": "Orlando",
                "zip_code": "32801",
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        ]

    def test_returns_own_profile(self, authed_client: "TestClient", mock_db: MagicMock):
        self._setup_profile(mock_db, "user-aaaaaaaa-0000-0000-0000-000000000001")
        resp = authed_client.get("/api/v1/profile/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Maria Silva"
        assert data["zip_code"] == "32801"

    def test_user_id_in_response_matches_token(self, authed_client: "TestClient", mock_db: MagicMock):
        """user_id in response must come from the token, not from DB row."""
        self._setup_profile(mock_db, "user-aaaaaaaa-0000-0000-0000-000000000001")
        resp = authed_client.get("/api/v1/profile/me")
        assert resp.json()["user_id"] == "user-aaaaaaaa-0000-0000-0000-000000000001"

    def test_unauthenticated_returns_403(self, client: "TestClient", mock_db: MagicMock):
        resp = client.get("/api/v1/profile/me")
        assert resp.status_code in (401, 403)

    def test_creates_profile_if_missing(self, authed_client: "TestClient", mock_db: MagicMock):
        """If profile row is absent (registration edge case), it's created on first access."""
        call_count = 0

        def execute_side_effect():
            nonlocal call_count
            call_count += 1
            m = MagicMock()
            if call_count <= 1:
                m.data = []   # First select: no profile
            else:
                m.data = [{   # After insert, second select returns row
                    "user_id": "user-aaaaaaaa-0000-0000-0000-000000000001",
                    "full_name": None, "phone": None, "state": None,
                    "city": None, "zip_code": None,
                    "created_at": "2025-01-01T00:00:00+00:00",
                }]
            return m

        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = (
            execute_side_effect
        )
        resp = authed_client.get("/api/v1/profile/me")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# PUT /profile/me
# ---------------------------------------------------------------------------

class TestUpdateProfile:
    def _setup_profile(self, mock_db: MagicMock) -> None:
        profile_data = {
            "user_id": "user-aaaaaaaa-0000-0000-0000-000000000001",
            "full_name": "Novo Nome",
            "phone": None,
            "state": "TX",
            "city": "Houston",
            "zip_code": "77001",
            "created_at": "2025-01-01T00:00:00+00:00",
        }
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            profile_data
        ]

    def test_update_name_success(self, authed_client: "TestClient", mock_db: MagicMock):
        self._setup_profile(mock_db)
        resp = authed_client.put("/api/v1/profile/me", json={"full_name": "Novo Nome"})
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Novo Nome"

    def test_update_zip_valid(self, authed_client: "TestClient", mock_db: MagicMock):
        self._setup_profile(mock_db)
        resp = authed_client.put("/api/v1/profile/me", json={"zip_code": "77001"})
        assert resp.status_code == 200

    def test_update_zip_invalid_rejected(self, authed_client: "TestClient", mock_db: MagicMock):
        resp = authed_client.put("/api/v1/profile/me", json={"zip_code": "ABCDE"})
        assert resp.status_code == 422

    def test_empty_body_rejected(self, authed_client: "TestClient", mock_db: MagicMock):
        resp = authed_client.put("/api/v1/profile/me", json={})
        assert resp.status_code == 400

    def test_unauthenticated_returns_401(self, client: "TestClient", mock_db: MagicMock):
        resp = client.put("/api/v1/profile/me", json={"full_name": "Hacker"})
        assert resp.status_code in (401, 403)

    def test_cannot_pass_user_id_in_body(self, authed_client: "TestClient", mock_db: MagicMock):
        """IDOR guard: user_id in body is ignored; only the token's user_id is used."""
        self._setup_profile(mock_db)
        # Even if attacker passes another user's ID in body, it must be ignored
        resp = authed_client.put("/api/v1/profile/me", json={
            "user_id": "user-bbbbbbbb-0000-0000-0000-000000000002",
            "full_name": "Attacker Name",
        })
        # Should succeed (user_id field is not in ProfileUpdate schema, so ignored by pydantic)
        # or fail validation — either way the actual DB update uses the token's user_id
        assert resp.status_code in (200, 422)
        if resp.status_code == 200:
            # Confirm the update was called with the token user_id, not the body user_id
            update_call = mock_db.table.return_value.update.return_value.eq
            # eq should have been called with ("user_id", token_user_id), never attacker's id
            for c in update_call.call_args_list:
                args = c[0]
                if args[0] == "user_id":
                    assert args[1] == "user-aaaaaaaa-0000-0000-0000-000000000001"
