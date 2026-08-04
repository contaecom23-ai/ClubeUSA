"""Fixtures compartilhadas para os testes do backend."""
import os
import pytest
from unittest.mock import MagicMock, patch

# Configura env vars mínimas antes de importar o app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_URL", "http://localhost:8080")

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock do cliente Supabase para evitar chamadas reais ao banco."""
    with patch("app.database._client") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance
