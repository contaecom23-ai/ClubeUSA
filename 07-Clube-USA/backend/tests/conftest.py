"""
Test fixtures.

All Supabase interactions are mocked so tests run without real credentials.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Inject dummy env vars BEFORE importing any app module
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-key-test")
os.environ.setdefault("SUPABASE_JWT_SECRET", "super-secret-jwt-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")


def _make_mock_user(
    uid: str | None = None,
    email: str = "test@example.com",
    confirmed: bool = True,
    full_name: str = "Test User",
):
    user = MagicMock()
    user.id = uid or str(uuid.uuid4())
    user.email = email
    user.email_confirmed_at = "2026-01-01T00:00:00" if confirmed else None
    user.user_metadata = {"full_name": full_name}
    return user


def _make_mock_session(access_token: str = "mock-access-token", refresh_token: str = "mock-refresh-token"):
    session = MagicMock()
    session.access_token = access_token
    session.refresh_token = refresh_token
    return session


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    with patch("backend.database._client", mock):
        yield mock


@pytest.fixture
def client(mock_supabase):
    # Import after env vars are set
    from backend.main import create_app

    test_app = create_app()
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def confirmed_user():
    return _make_mock_user(confirmed=True)


@pytest.fixture
def unconfirmed_user():
    return _make_mock_user(confirmed=False)


@pytest.fixture
def make_user():
    return _make_mock_user


@pytest.fixture
def make_session():
    return _make_mock_session


# Helper: a valid Supabase-style HS256 JWT for testing
def _make_test_jwt(user_id: str, secret: str = "super-secret-jwt-key-for-testing-only") -> str:
    from jose import jwt
    import time

    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "role": "authenticated",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers(confirmed_user):
    token = _make_test_jwt(str(confirmed_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_id(confirmed_user):
    return str(confirmed_user.id)
