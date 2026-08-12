import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

TEST_JWT_SECRET = "test-secret-key-for-unit-tests-only-32chars"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID_2 = "00000000-0000-0000-0000-000000000002"


def make_token(user_id: str = TEST_USER_ID, role: str = "authenticated", expired: bool = False) -> str:
    exp = int(time.time()) + (-10 if expired else 3600)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": exp, "aud": "authenticated"},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    """Injeta settings de teste sem depender de .env real."""
    mock_settings = MagicMock()
    mock_settings.supabase_url = "https://test.supabase.co"
    mock_settings.supabase_service_key = "test-service-key"
    mock_settings.supabase_jwt_secret = TEST_JWT_SECRET
    mock_settings.origins_list = ["http://localhost:5500"]
    mock_settings.is_production = False

    with patch("app.config.get_settings", return_value=mock_settings):
        with patch("app.auth.middleware.get_settings", return_value=mock_settings):
            with patch("app.profile.service.get_settings", return_value=mock_settings):
                yield mock_settings


@pytest.fixture
def client(patch_settings):
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {make_token()}"}


@pytest.fixture
def auth_headers_user2():
    return {"Authorization": f"Bearer {make_token(user_id=TEST_USER_ID_2)}"}
