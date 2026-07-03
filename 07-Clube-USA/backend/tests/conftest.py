import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Define env vars antes de importar qualquer módulo da app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32bytes-xxxxxxxxxxx")
os.environ.setdefault("APP_BASE_URL", "http://testserver")
os.environ.setdefault("CORS_ORIGINS", '["http://testserver"]')
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SMTP_HOST", "")  # Sem SMTP em testes

from app.database import get_pool
from main import app


def make_mock_pool(fetchrow_return=None, fetchrow_side_effect=None):
    """Cria um mock de asyncpg.Pool configurável."""
    pool = MagicMock()
    conn = AsyncMock()

    if fetchrow_side_effect:
        conn.fetchrow = AsyncMock(side_effect=fetchrow_side_effect)
    else:
        conn.fetchrow = AsyncMock(return_value=fetchrow_return)

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=None)
    pool.acquire = MagicMock(return_value=cm)

    return pool, conn


@pytest_asyncio.fixture
async def client_with_pool(monkeypatch):
    """Retorna (AsyncClient, mock_conn) com pool mockado."""

    async def _make(fetchrow_return=None, fetchrow_side_effect=None):
        pool, conn = make_mock_pool(fetchrow_return, fetchrow_side_effect)
        app.dependency_overrides[get_pool] = lambda: pool

        # Mock do serviço de email
        monkeypatch.setattr(
            "app.email_service.send_confirmation_email",
            AsyncMock(return_value=None),
        )

        transport = ASGITransport(app=app)
        ac = AsyncClient(transport=transport, base_url="http://testserver")
        return ac, conn

    yield _make
    app.dependency_overrides.clear()


def make_user_row(
    user_id: str | None = None,
    email: str = "joao@exemplo.com",
    full_name: str = "João Silva",
    zip_code: str | None = "10001",
    email_confirmed: bool = True,
    password_hash: str = "$2b$12$KIXnKH.YKmXmxUCFtXZzFeQDZbOlW0ORkNbxEo3gWp18ZL5x6Wm1S",
):
    return {
        "id": uuid.UUID(user_id) if user_id else uuid.uuid4(),
        "email": email,
        "full_name": full_name,
        "zip_code": zip_code,
        "email_confirmed": email_confirmed,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }
