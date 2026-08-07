import os
from unittest.mock import MagicMock

# Must set env vars BEFORE any app module is imported
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256!")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.dependencies import get_db, get_current_user, limit_login, limit_register, limit_resend
from app.main import app
from app.services.auth import create_access_token, hash_password


def _no_limit() -> None:
    """Override rate-limit dependencies in tests so they never block."""
    return None


def _user_row(**overrides) -> dict:
    row = {
        "id": "user-id-1",
        "email": "joao@example.com",
        "password_hash": hash_password("senha1234"),
        "full_name": "João Silva",
        "phone": None,
        "zip_code": None,
        "state": None,
        "city": None,
        "bio": None,
        "email_confirmed": True,
        "email_confirmed_at": "2026-01-01T00:00:00+00:00",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    row.update(overrides)
    return row


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Database)


@pytest.fixture
def user_row() -> dict:
    return _user_row()


@pytest.fixture
def client(mock_db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[limit_register] = _no_limit
    app.dependency_overrides[limit_login] = _no_limit
    app.dependency_overrides[limit_resend] = _no_limit
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(user_row) -> dict:
    token = create_access_token(user_id=user_row["id"], email=user_row["email"])
    return {"Authorization": f"Bearer {token}"}
