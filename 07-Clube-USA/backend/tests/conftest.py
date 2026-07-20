import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add backend to path so imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch settings before any app import so we don't need a real .env
_mock_settings = MagicMock()
_mock_settings.SUPABASE_URL = "https://test.supabase.co"
_mock_settings.SUPABASE_SERVICE_ROLE_KEY = "test-service-role-key"
_mock_settings.origins_list = ["http://localhost:3000"]
_mock_settings.is_production = False

with patch("config.get_settings", return_value=_mock_settings):
    from fastapi.testclient import TestClient
    from main import app
    from core.supabase_client import get_supabase

TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_EMAIL = "user@example.com"
TEST_TOKEN = "test-jwt-token"

# IP cycling to stay under rate limits (each test should pass a unique IP)
_ip_counter = 0


def next_ip() -> dict:
    global _ip_counter
    _ip_counter += 1
    return {"X-Forwarded-For": f"10.0.{_ip_counter // 255}.{_ip_counter % 255}"}


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    app.dependency_overrides[get_supabase] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_supabase):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def make_confirmed_user(user_id: str = TEST_USER_ID, email: str = TEST_EMAIL) -> dict:
    from datetime import datetime, timezone
    return {
        "id": user_id,
        "email": email,
        "email_confirmed_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }


def make_unconfirmed_user(user_id: str = TEST_USER_ID, email: str = TEST_EMAIL) -> dict:
    return {"id": user_id, "email": email, "email_confirmed_at": None}
