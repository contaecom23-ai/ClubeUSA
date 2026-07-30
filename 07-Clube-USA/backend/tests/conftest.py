"""
Fixtures de teste.

Requer variável de ambiente TEST_DATABASE_URL apontando para um banco PostgreSQL
de teste (separado do banco de produção).

Exemplo:
    TEST_DATABASE_URL=postgresql://postgres:senha@localhost:5432/clubeusa_test pytest

Sem TEST_DATABASE_URL os testes são pulados automaticamente.
"""
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")


def _async_db_url(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL não definida")
    engine = create_async_engine(_async_db_url(TEST_DATABASE_URL), echo=False)
    # Importa modelos para criar tabelas
    from app.database import Base
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    from app.main import app
    from app.deps import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-32chars!")
    os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
