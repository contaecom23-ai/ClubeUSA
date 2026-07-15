"""
Fixtures de teste para o Clube USA backend.

Usa um banco PostgreSQL real via TEST_DATABASE_URL.
Para testes locais rápidos sem banco, muitos casos usam mocks de conexão.
"""
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Configura env mínima antes de importar app (evita sys.exit por falta de envs)
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-64-chars-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_conn():
    """Conexão asyncpg mockada para testes unitários sem banco real."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    return conn


@pytest.fixture
def app_with_mock_db(mock_conn):
    """App FastAPI com banco mockado."""
    from app.main import app
    from app.database import get_conn

    async def override_get_conn():
        yield mock_conn

    app.dependency_overrides[get_conn] = override_get_conn
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_with_mock_db):
    return TestClient(app_with_mock_db, raise_server_exceptions=True)
