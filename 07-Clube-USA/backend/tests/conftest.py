import os
import sys

# Garante que o backend/ esteja no path para imports sem package install
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Env vars mínimas antes de qualquer import do app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
# Secret HS256 precisa de 32+ bytes; usa string longa fixa nos testes
os.environ.setdefault(
    "SUPABASE_JWT_SECRET",
    "test-jwt-secret-with-at-least-32-characters-for-hs256-ok",
)
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from db.supabase import get_supabase


def make_mock_supabase() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_supabase():
    client = make_mock_supabase()
    app.dependency_overrides[get_supabase] = lambda: client
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_supabase):
    with TestClient(app) as c:
        yield c


def make_jwt(user_id: str = "user-123") -> str:
    """Gera um JWT válido para testes (assinado com o secret de teste)."""
    import jwt
    import time

    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(
        payload,
        os.environ["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )
