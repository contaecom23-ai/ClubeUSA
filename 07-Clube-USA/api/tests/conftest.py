import os
from unittest.mock import MagicMock

# Vars de ambiente ANTES de qualquer import do app
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-32chars!")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("EMAIL_PROVIDER", "log")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_app():
    from main import app
    return app


@pytest.fixture
def mock_db():
    """Mock do cliente Supabase para injeção nos testes."""
    return MagicMock()


@pytest.fixture
def client(test_app, mock_db):
    """TestClient com DB mockado via dependency override."""
    from deps import get_db
    test_app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c
    test_app.dependency_overrides.clear()


def configure_select(mock_db, data: list):
    """Helper: configura a cadeia .table().select().eq().execute() para retornar data."""
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = data


def configure_insert(mock_db, data: list):
    """Helper: configura a cadeia .table().insert().execute() para retornar data."""
    mock_db.table.return_value.insert.return_value.execute.return_value.data = data


def configure_update(mock_db, data: list):
    """Helper: configura a cadeia .table().update().eq().execute()."""
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = data
