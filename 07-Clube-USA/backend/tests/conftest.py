"""
Fixtures de teste. Usa um banco em memória simulado via mocks do Supabase
para não precisar de credenciais reais em CI.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Injeta env vars antes de importar o app
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-service-role-key")
os.environ.setdefault("SECRET_KEY", "x" * 64)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("APP_BASE_URL", "http://localhost:8000")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture
def mock_db():
    """Mock do cliente Supabase — simula respostas sem rede."""
    with patch("app.database._client") as mock:
        yield mock


@pytest.fixture
def client(mock_db):
    from app.main import app
    return TestClient(app, raise_server_exceptions=True)


def make_supabase_mock(data: list | None = None, error=None):
    """Cria um mock que imita o retorno do Supabase: .execute() -> Response."""
    response = MagicMock()
    response.data = data or []
    response.error = error

    chain = MagicMock()
    chain.execute.return_value = response

    # Suporta encadeamento: .table().select().eq().execute()
    for method in ("select", "insert", "update", "delete", "eq", "neq", "limit"):
        getattr(chain, method).return_value = chain

    return chain, response
