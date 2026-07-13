"""
Configuração de testes.

Os testes de integração requerem DATABASE_URL configurada.
Sem ela, são pulados automaticamente.

Para rodar localmente:
  export DATABASE_URL=postgresql://...
  cd backend && pytest
"""
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Configurar env para testes antes de importar o app
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-x1y2z3")
os.environ.setdefault("EMAIL_BACKEND", "console")
os.environ.setdefault("FRONTEND_URL", "http://testserver")
os.environ.setdefault("APP_URL", "http://testserver")

HAS_DB = bool(os.environ.get("DATABASE_URL"))
requires_db = pytest.mark.skipif(not HAS_DB, reason="DATABASE_URL não configurada")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def client():
    from main import app
    from app import database as db

    await db.startup()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    await db.shutdown()
