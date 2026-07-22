"""
Fixtures compartilhadas.
Usa banco SQLite em memória para isolamento total entre testes.
Rate limiting desativado via override de env var.
"""
import os
import sys
import uuid
from pathlib import Path

# Adiciona 'api/' ao path antes de qualquer import do app
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# Env vars devem ser configuradas ANTES de importar o app/settings
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-chars-ok-xxx"
os.environ["EMAIL_BACKEND"] = "console"
os.environ["ENVIRONMENT"] = "development"
os.environ["RATE_LIMIT_REGISTER"] = "1000/minute"
os.environ["RATE_LIMIT_LOGIN"] = "1000/minute"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.user import Base
from core.database import get_db
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session():
    async with _SessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession):
    """Cliente HTTP com DB isolado (rollback após cada teste)."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ─── Helper reutilizável ──────────────────────────────────────────────────────

async def register_and_confirm(
    client: AsyncClient,
    email: str,
    password: str = "Senha@123",
    full_name: str = "Test User",
) -> str:
    """Registra, confirma e-mail no banco direto e retorna o access_token."""
    from sqlalchemy import select, update
    from models.user import User

    resp = await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
    })
    assert resp.status_code == 201, f"Registro falhou: {resp.text}"

    # Confirma direto no banco sem depender do fluxo de e-mail
    async with _SessionLocal() as s:
        user = await s.scalar(select(User).where(User.email == email.lower()))
        await s.execute(
            update(User)
            .where(User.id == user.id)
            .values(email_confirmed=True, email_confirm_token=None)
        )
        await s.commit()

    login_resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200, f"Login falhou: {login_resp.text}"
    return login_resp.json()["access_token"]
