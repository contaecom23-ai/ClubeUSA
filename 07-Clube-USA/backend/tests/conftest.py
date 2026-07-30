"""
Fixtures de teste.

Requer variável de ambiente TEST_DATABASE_URL apontando para um banco PostgreSQL
de teste (separado do banco de produção).

Exemplo:
    TEST_DATABASE_URL=postgresql://postgres:senha@localhost:5432/clubeusa_test pytest

Sem TEST_DATABASE_URL os testes são pulados automaticamente.

Notas sobre design:
- event_loop é session-scoped: asyncpg connections são bound ao event loop onde
  foram criadas; misturar loop de sessão com loop de função gera o erro
  "cannot perform operation: another operation is in progress".
- client e db usam conexões DISTINTAS do pool: a fixture db fornece uma sessão
  para leituras diretas nos testes; override_get_db cria uma sessão nova por
  request HTTP. Compartilhar a mesma sessão entre os dois causa o mesmo erro acima.
"""
import asyncio
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


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped para que conexões asyncpg sejam reutilizáveis entre testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def session_factory():
    """Cria schema do banco uma vez por sessão de testes e fornece o factory."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL não definida")

    engine = create_async_engine(_async_db_url(TEST_DATABASE_URL), echo=False)

    from app.database import Base
    import app.models  # noqa: F401 — registra modelos no metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(session_factory):
    """Sessão dedicada para leituras/assertions diretas nos testes."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory):
    """
    HTTP client com get_db apontando para o pool de teste.
    Cada request HTTP recebe sua própria sessão (não compartilha com db fixture)
    para evitar conflito asyncpg de operação concorrente.
    """
    from app.main import app
    from app.deps import get_db

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-32chars!")
    os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
