import os

# Setar antes de qualquer import do app
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-32-chars-ok!!")
os.environ.setdefault("RATE_LIMIT_REGISTER", "1000/minute")
os.environ.setdefault("RATE_LIMIT_LOGIN", "1000/minute")

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.execute = AsyncMock(return_value=None)
    return conn


@pytest.fixture
def mock_pool(mock_conn):
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_conn)
    cm.__aexit__ = AsyncMock(return_value=False)

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool
