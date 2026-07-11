"""Tests for profile endpoints — verifying multi-tenant isolation."""
import os
import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-that-is-long-enough-ok")

from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.utils import create_access_token
from app.main import app
from app.database import get_db


def _make_db_returning(data):
    qb = MagicMock()
    qb.select.return_value = qb
    qb.update.return_value = qb
    qb.eq.return_value = qb
    result = MagicMock()
    result.data = data
    qb.execute.return_value = result
    db = MagicMock()
    db.table.return_value = qb
    return db


def _auth_header(user_id: str) -> dict:
    token, _ = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_success():
    user_id = "aaaaaaaa-0000-0000-0000-000000000001"
    profile = {
        "id": user_id, "email": "u@ex.com", "name": "User",
        "zip_code": "33101", "state_abbr": "FL",
        "email_verified": True,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    db = _make_db_returning([profile])
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        resp = client.get("/users/me", headers=_auth_header(user_id))

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


def test_get_profile_requires_auth():
    with TestClient(app) as client:
        resp = client.get("/users/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when header missing


def test_get_profile_invalid_token():
    with TestClient(app) as client:
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


def test_update_profile_success():
    user_id = "aaaaaaaa-0000-0000-0000-000000000002"
    updated = {
        "id": user_id, "email": "u@ex.com", "name": "New Name",
        "zip_code": "10001", "state_abbr": "NY",
        "email_verified": True,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    db = _make_db_returning([updated])
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        resp = client.patch(
            "/users/me",
            json={"name": "New Name", "zip_code": "10001", "state_abbr": "NY"},
            headers=_auth_header(user_id),
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_update_profile_empty_body():
    """Sending no fields should return 422."""
    user_id = "aaaaaaaa-0000-0000-0000-000000000003"
    db = _make_db_returning([])
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        resp = client.patch("/users/me", json={}, headers=_auth_header(user_id))

    app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_cross_tenant_access_returns_404():
    """user_id from JWT must own the resource — if DB returns nothing, 404 (not 200 or 500)."""
    user_id = "aaaaaaaa-0000-0000-0000-000000000004"
    # DB returns empty — user not found (simulates accessing another user's data
    # that would be blocked by the server-side .eq("id", user_id) filter)
    db = _make_db_returning([])
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        resp = client.get("/users/me", headers=_auth_header(user_id))

    app.dependency_overrides.clear()
    assert resp.status_code == 404
