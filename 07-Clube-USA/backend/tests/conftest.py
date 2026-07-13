import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Set required env vars before any imports that call get_settings()
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long-for-testing-only")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_db():
    """Patch get_db() to return a MagicMock so no real Supabase calls are made."""
    with patch("app.db.get_db") as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


@pytest.fixture()
def mock_email():
    """Suppress SMTP in tests."""
    with patch("app.email.send_email", return_value=True):
        yield


def make_table_result(data: list):
    """Build a fake supabase query result."""
    result = MagicMock()
    result.data = data
    return result


def empty_result():
    return make_table_result([])
