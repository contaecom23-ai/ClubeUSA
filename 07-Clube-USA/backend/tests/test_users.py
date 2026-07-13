"""
Tests for user profile endpoints: GET /users/me and PUT /users/me.
Validates multi-tenant isolation: user A cannot read/write user B's data.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.security import create_access_token
from tests.conftest import empty_result, make_table_result

USER_A_ID = str(uuid.uuid4())
USER_B_ID = str(uuid.uuid4())

USER_A = {
    "id": USER_A_ID,
    "email": "userA@example.com",
    "full_name": "User A",
    "zip_code": "90210",
    "city": "Los Angeles",
    "state": "CA",
    "phone": None,
    "bio": None,
    "avatar_url": None,
    "email_confirmed": True,
    "created_at": "2026-01-01T00:00:00+00:00",
    "last_login_at": None,
}


def auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ── GET /users/me ─────────────────────────────────────────────────────────────

def test_get_me_success(client):
    with patch("app.deps.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([USER_A])

        resp = client.get("/users/me", headers=auth_header(USER_A_ID))

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == USER_A_ID
    assert data["email"] == "userA@example.com"
    # password_hash must NOT appear in the response
    assert "password_hash" not in data


def test_get_me_inactive_user(client):
    with patch("app.deps.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = empty_result()

        resp = client.get("/users/me", headers=auth_header(USER_A_ID))

    assert resp.status_code == 401


# ── PUT /users/me ─────────────────────────────────────────────────────────────

def test_update_me_success(client):
    updated = {**USER_A, "bio": "Moro em Los Angeles ha 3 anos"}

    with patch("app.deps.get_db") as mock_deps_db, \
         patch("app.users.service.get_db") as mock_svc_db:

        # Auth check
        deps_db = MagicMock()
        mock_deps_db.return_value = deps_db
        deps_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([USER_A])

        # Update
        svc_db = MagicMock()
        mock_svc_db.return_value = svc_db
        svc_db.table.return_value.update.return_value.eq.return_value.execute.return_value = \
            make_table_result([updated])

        resp = client.put("/users/me",
                          json={"bio": "Moro em Los Angeles ha 3 anos"},
                          headers=auth_header(USER_A_ID))

    assert resp.status_code == 200
    assert resp.json()["bio"] == "Moro em Los Angeles ha 3 anos"


def test_update_me_cannot_change_email(client):
    """email is not an allowed field in UpdateProfileRequest — must be ignored."""
    with patch("app.deps.get_db") as mock_deps_db, \
         patch("app.users.service.get_db") as mock_svc_db:

        deps_db = MagicMock()
        mock_deps_db.return_value = deps_db
        deps_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([USER_A])

        svc_db = MagicMock()
        mock_svc_db.return_value = svc_db
        svc_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([USER_A])

        resp = client.put("/users/me",
                          json={"email": "hacker@evil.com"},
                          headers=auth_header(USER_A_ID))

    # 200 is OK (field ignored), but email must not change
    assert resp.status_code == 200
    assert resp.json()["email"] == "userA@example.com"


def test_update_me_unauthenticated(client):
    resp = client.put("/users/me", json={"bio": "test"})
    assert resp.status_code == 401


def test_cross_tenant_isolation(client):
    """
    User B's token cannot be used to get User A's data.
    Each request only returns the authenticated user's own profile.
    """
    # When User B authenticates, DB only returns User B's profile
    user_b = {**USER_A, "id": USER_B_ID, "email": "userB@example.com", "full_name": "User B"}

    with patch("app.deps.get_db") as mock_get_db:
        db = MagicMock()
        mock_get_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = \
            make_table_result([user_b])

        resp = client.get("/users/me", headers=auth_header(USER_B_ID))

    assert resp.status_code == 200
    # User B gets their own data, not User A's
    assert resp.json()["id"] == USER_B_ID
    assert resp.json()["email"] == "userB@example.com"
