"""
Test configuration.
All external dependencies (Supabase, email) are mocked.
Tests never hit real DB or send real emails.
"""
import os
import secrets
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Inject required env vars before importing the app
os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(32))
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("FRONTEND_URL", "https://clubeusa.test")
os.environ.setdefault("ALLOWED_ORIGINS", "https://clubeusa.test")


@pytest.fixture(scope="session")
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    from api.main import create_app
    from api.database import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: mock_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def sample_user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def sample_user(sample_user_id):
    return {
        "id": sample_user_id,
        "email": "test@example.com",
        "full_name": "Test User",
        "email_confirmed": True,
        "created_at": "2026-07-10T00:00:00+00:00",
        "password_hash": "$2b$12$dummy",
    }
