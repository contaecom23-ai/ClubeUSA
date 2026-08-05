"""
Test fixtures for Clube USA API.

Unit tests mock the Supabase client (no real DB needed).
Integration tests require a real Supabase instance — set env vars in .env.test.
"""
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Provide minimal env vars before importing the app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SECRET_KEY", "a-very-long-secret-key-used-only-in-tests-1234567890")
os.environ.setdefault("ENVIRONMENT", "test")


def make_table_mock(data_result=None):
    """Create a supabase table-chain MagicMock."""
    table = MagicMock()
    execute_result = MagicMock(data=data_result if data_result is not None else [])
    table.select.return_value = table
    table.insert.return_value = table
    table.update.return_value = table
    table.eq.return_value = table
    table.execute.return_value = execute_result
    return table


@pytest.fixture()
def mock_db():
    """Return a MagicMock mimicking the supabase client. Configure table returns per test."""
    return MagicMock()


@pytest.fixture()
def client(mock_db):
    """TestClient with the Supabase DB dependency overridden."""
    from api.database import get_db
    from api.main import app

    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(user_id=None, email="test@example.com", email_confirmed=True, is_active=True):
    return {
        "id": str(user_id or uuid.uuid4()),
        "email": email,
        "email_confirmed": email_confirmed,
        "is_active": is_active,
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }


def make_profile(user_id, full_name="Test User", zip_code="90210"):
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "full_name": full_name,
        "zip_code": zip_code,
        "phone": None,
        "bio": None,
        "avatar_url": None,
    }
