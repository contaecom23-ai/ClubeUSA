"""Shared fixtures for all tests.

Supabase is fully mocked via FastAPI's dependency_overrides — no real DB needed.
Each test creates its own DBMock and injects it cleanly through the DI system.
"""
import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Provide env vars before importing anything that reads them
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-64-chars-long-for-testing-purposes-xyzz")
os.environ.setdefault("ENVIRONMENT", "development")

# Prevent supabase from actually connecting at import time
from unittest.mock import patch
with patch("supabase.create_client", return_value=MagicMock()):
    from main import app

from db.client import get_db
from core.security import create_access_token, hash_password


class DBResult:
    """Simple stand-in for supabase's response — avoids MagicMock attribute quirks."""
    def __init__(self, data):
        self.data = data


def make_db_mock(*responses):
    """Build a mock DB client where sequential execute() calls consume `responses` in order.

    All .table().select().eq().insert()... chains share one builder with
    `side_effect` so each call to .execute() pops the next prepared response.

    Pass as many DBResult objects as the code path will call .execute().
    """
    db = MagicMock()
    builder = MagicMock()
    builder.select.return_value = builder
    builder.insert.return_value = builder
    builder.update.return_value = builder
    builder.eq.return_value = builder
    builder.execute.side_effect = list(responses) if responses else [DBResult(data=[])]
    db.table.return_value = builder
    return db


@pytest.fixture
def client():
    """Factory fixture — each test calls client(db_mock) and gets (TestClient, db)."""
    overrides_applied = []

    class Factory:
        def __call__(self, db):
            app.dependency_overrides[get_db] = lambda: db
            overrides_applied.append(db)
            tc = TestClient(app, raise_server_exceptions=False)
            return tc, db

    factory = Factory()
    yield factory

    app.dependency_overrides.pop(get_db, None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(user_id="user-uuid-1", email="test@example.com", confirmed=True):
    return {
        "id": user_id,
        "email": email,
        "password_hash": hash_password("Password1!"),
        "email_confirmed": confirmed,
        "email_confirm_token": None,
        "email_confirm_expires": None,
    }


def make_profile(user_id="user-uuid-1", full_name="João Silva"):
    return {
        "id": "profile-uuid-1",
        "user_id": user_id,
        "full_name": full_name,
        "phone": None,
        "zip_code": None,
        "state": None,
        "city": None,
        "bio": None,
    }


def auth_header(user_id="user-uuid-1"):
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}
