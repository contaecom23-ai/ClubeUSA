import os

# Variáveis obrigatórias devem existir antes de importar o app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars-long-ok")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient

from main import app
from middleware.auth import get_current_user

TEST_USER = {
    "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "email": "test@example.com",
    "role": "authenticated",
}


async def _mock_auth() -> dict:
    return TEST_USER


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _mock_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
