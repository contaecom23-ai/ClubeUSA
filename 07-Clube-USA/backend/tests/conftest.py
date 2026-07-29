"""
Test configuration.

Sets env vars BEFORE any app module is imported, so config.py picks them up
without needing a real .env file or Supabase connection.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("DEBUG", "true")

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def db_mock():
    """Module-scoped mock for the Supabase client returned by database.get_db()."""
    return MagicMock()


@pytest.fixture(scope="session")
def client(db_mock):
    """FastAPI TestClient with database.get_db patched to return the mock."""
    with patch("database.get_db", return_value=db_mock):
        from main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


def make_user_row(
    user_id="user-123",
    email="joao@example.com",
    full_name="João Silva",
    zip_code="10001",
    email_confirmed=True,
    confirmation_token=None,
    confirmation_expires=None,
    password_hash=None,
    created_at="2026-01-01T00:00:00+00:00",
):
    from auth import hash_password

    return {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "zip_code": zip_code,
        "email_confirmed": email_confirmed,
        "email_confirmation_token": confirmation_token,
        "email_confirmation_expires_at": confirmation_expires,
        "password_hash": password_hash or hash_password("senha123"),
        "created_at": created_at,
    }
