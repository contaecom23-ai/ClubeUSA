"""Test configuration and shared fixtures.

All DB calls are mocked — no real Supabase connection needed.
Set env vars before importing app modules so pydantic-settings picks them up.
"""
import os
from unittest.mock import MagicMock

# Must be set before any app import (pydantic-settings reads at import time)
os.environ.update({
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
    "SECRET_KEY": "test-secret-key-that-is-long-enough-for-testing-12345",
    "FRONTEND_URL": "http://localhost:8080",
    "BACKEND_URL": "http://localhost:8000",
    "CORS_ORIGINS": "http://localhost:8080",
    "SMTP_HOST": "",
})

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from main import app


@pytest.fixture()
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client(mock_db: MagicMock) -> TestClient:
    """TestClient with the real DB dependency overridden by a mock."""
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def authed_client(mock_db: MagicMock) -> TestClient:
    """TestClient with both DB and current_user overridden (for protected routes)."""
    fake_user = {
        "id": "user-aaaaaaaa-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "is_email_verified": True,
    }
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def another_user_id() -> str:
    """A different user_id for cross-tenant (IDOR) tests."""
    return "user-bbbbbbbb-0000-0000-0000-000000000002"
