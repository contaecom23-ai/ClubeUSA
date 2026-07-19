"""
Fixtures e mocks compartilhados.
Todos os testes rodam sem Supabase real — usamos mocks.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Força modo testing para que config.py não valide segredos reais
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-at-least-32-chars-long!!")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture(autouse=True)
def patch_supabase():
    """Substitui os clientes Supabase por mocks em todos os testes."""
    mock_auth = MagicMock()
    mock_admin = MagicMock()
    with (
        patch("app.database.get_auth_client", return_value=mock_auth),
        patch("app.database.get_admin_client", return_value=mock_admin),
        patch("app.auth.service.get_auth_client", return_value=mock_auth),
        patch("app.users.service.get_admin_client", return_value=mock_admin),
    ):
        yield mock_auth, mock_admin


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def make_jwt(user_id: str, email: str) -> str:
    """Gera JWT de teste assinado com a secret de teste."""
    from jose import jwt
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
    }
    return jwt.encode(payload, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
