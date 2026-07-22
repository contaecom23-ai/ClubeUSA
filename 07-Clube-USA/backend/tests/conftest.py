"""
Fixtures de teste para o Clube USA.
Todos os testes mocam o Supabase e o email — sem dependência de infra real.
Usa FastAPI dependency_overrides para injetar o mock DB.
"""
import os

# Variáveis de ambiente ANTES de qualquer import do app
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-chars-long-abc"
os.environ["SUPABASE_URL"] = ""          # Vazio → init_db() é no-op
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["SMTP_HOST"] = ""             # Modo dev → emails vão para o log

from unittest.mock import AsyncMock, MagicMock
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import get_db


def make_result(data=None, error=None):
    """Cria um resultado mock do Supabase."""
    r = MagicMock()
    r.data = data if data is not None else []
    r.error = error
    return r


@pytest.fixture
def mock_db():
    """
    Mock do cliente Supabase com encadeamento fluente.
    Configure mock_db.execute.side_effect = [result1, result2, ...]
    para controlar respostas sequenciais dentro de uma rota.
    """
    db = MagicMock()
    for method in ["table", "select", "insert", "update", "delete",
                   "eq", "neq", "single", "limit"]:
        getattr(db, method).return_value = db

    db.execute = AsyncMock(return_value=make_result())
    return db


@pytest_asyncio.fixture
async def client(mock_db):
    """
    Cliente HTTP de teste com DB mockado via dependency_overrides.
    Garante limpeza das overrides após cada teste.
    """
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)
