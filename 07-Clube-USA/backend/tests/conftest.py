"""
Test fixtures using pytest + in-memory mocks.
We do NOT hit the real Supabase in unit tests — the service functions are tested
by injecting a fake DB client. Integration tests (TODO) would use a real test project.
"""
import os
import pytest

# Set environment to "test" before importing app modules so validate_secrets() relaxes
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-32-chars-long-ok")

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


# ── Fake Supabase client ──────────────────────────────────────────────────────

class FakeQueryBuilder:
    """Chainable fake for db.table(...).select(...).eq(...).execute()"""

    def __init__(self, return_data=None, return_count=None):
        self._data = return_data or []
        self._count = return_count

    def select(self, *args, **kwargs): return self
    def insert(self, *args, **kwargs): return self
    def update(self, *args, **kwargs): return self
    def delete(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def gte(self, *args, **kwargs): return self
    def neq(self, *args, **kwargs): return self
    def execute(self):
        result = MagicMock()
        result.data = self._data
        result.count = self._count
        return result


@pytest.fixture
def fake_db():
    db = MagicMock()
    db.table.return_value = FakeQueryBuilder()
    return db


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
