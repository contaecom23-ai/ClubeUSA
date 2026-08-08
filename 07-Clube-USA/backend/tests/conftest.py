"""
Fixtures compartilhadas.
O Supabase client é substituído por um mock para que os testes
rodem sem banco real. Os testes validam a lógica de serviço e
os controles de segurança (isolamento, rate-limit, etc.).
"""
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Injetar env vars antes de importar o app (evita crash de validação)
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-de-32-chars-xyzxyz")

from app.database import get_db
from app.main import app


def _make_supabase_mock(rows=None, count=0):
    """Constrói um mock do supabase client com resultado fixo."""
    mock_db = MagicMock()
    execute_result = MagicMock()
    execute_result.data = rows or []
    execute_result.count = count

    # Encadeamento: db.table(...).select(...).eq(...).execute()
    chain = MagicMock()
    chain.execute.return_value = execute_result
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain

    mock_db.table.return_value = chain
    return mock_db


@pytest.fixture
def db_mock():
    return _make_supabase_mock()


@pytest.fixture
def client(db_mock):
    app.dependency_overrides[get_db] = lambda: db_mock
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
