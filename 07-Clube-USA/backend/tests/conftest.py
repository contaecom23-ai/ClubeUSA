"""
Fixtures compartilhadas dos testes.
O cliente Supabase e o serviço de e-mail são mockados para que os testes
rodem sem infraestrutura real (sem DB, sem SMTP).

Arquitetura do mock_db:
  mock_db.table("users")         → um TableMock
  table._select.execute          → mock para select queries
  table._insert.execute          → mock para insert queries
  table._update.execute          → mock para update queries
  table._select.eq/is_/maybe_single → retornam _select (encadeamento fluente)
"""
import os
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars!!!")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("DEBUG", "true")

import pytest
from fastapi.testclient import TestClient

from main import app
from app import database, email_service


def _api_response(data):
    r = MagicMock()
    r.data = data
    return r


def _make_op_builder(default_data):
    """Builder para uma operação (select/insert/update) com execute próprio."""
    b = MagicMock()
    b.eq.return_value = b
    b.neq.return_value = b
    b.is_.return_value = b
    b.maybe_single.return_value = b
    b.single.return_value = b
    b.execute = AsyncMock(return_value=_api_response(default_data))
    return b


def _make_table():
    t = MagicMock()
    t._select = _make_op_builder(None)    # select: não encontrado por padrão
    t._insert = _make_op_builder([{}])    # insert: sucesso por padrão
    t._update = _make_op_builder([{}])    # update: sucesso por padrão
    t.select.return_value = t._select
    t.insert.return_value = t._insert
    t.update.return_value = t._update
    return t


@pytest.fixture
def mock_db():
    """
    Mock do AsyncClient do Supabase com builders por operação (select/insert/update).
    Cada nome de tabela retorna o mesmo mock na sessão (cacheado por nome).

    Acesse os builders nos testes assim:
        users = mock_db.table('users')
        users._select.execute = AsyncMock(return_value=_api_response(my_data))
    """
    db = AsyncMock()
    _tables: dict = {}

    def _get_table(name: str):
        if name not in _tables:
            _tables[name] = _make_table()
        return _tables[name]

    db.table = MagicMock(side_effect=_get_table)
    db._tables = _tables
    return db


@pytest.fixture
def client(mock_db):
    """TestClient com Supabase e e-mail mockados."""
    app.dependency_overrides[database.get_db] = lambda: mock_db

    original_send = email_service.send_confirmation_email
    email_service.send_confirmation_email = AsyncMock()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    email_service.send_confirmation_email = original_send
