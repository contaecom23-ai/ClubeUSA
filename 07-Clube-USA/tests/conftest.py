"""
Fixtures compartilhados. Os testes mocam o banco de dados para rodar sem
uma instância PostgreSQL real (CI-friendly).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Variáveis de ambiente mínimas para inicializar a app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("SECRET_KEY", "testsecretkey_32_chars_minimum_here!")
os.environ.setdefault("FRONTEND_URL", "http://localhost:8000")


@pytest.fixture()
def mock_db():
    """Conexão asyncpg mockada."""
    db = AsyncMock()
    return db


@pytest.fixture()
def client(mock_db):
    """TestClient com dependency override para o banco."""
    from backend.app.main import app
    from backend.app.database import get_db

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
