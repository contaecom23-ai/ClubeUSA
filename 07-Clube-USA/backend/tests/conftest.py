import os
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

# Variáveis de ambiente mínimas para os testes rodarem sem infraestrutura real
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-needs-32-chars!")
os.environ.setdefault("ENVIRONMENT", "test")

from app.database import get_db  # noqa: E402 — importar depois de setar env
from app.main import app  # noqa: E402


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
async def client(mock_db: AsyncMock):
    """Client com banco de dados mockado via dependency override."""

    async def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, mock_db

    app.dependency_overrides.clear()
