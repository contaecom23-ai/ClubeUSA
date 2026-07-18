"""
Fixtures compartilhadas. O Supabase é mockado — os testes não precisam de
conexão real com banco. Testar a lógica de serviço e as rotas HTTP.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Injeta env vars antes de importar a app
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-service-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("EMAIL_SERVICE", "log")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5500")


@pytest.fixture()
def mock_db():
    """Retorna um mock do Client do Supabase."""
    db = MagicMock()
    # Padrão: table().select().eq().execute() retorna dados vazios
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    db.table.return_value.insert.return_value.execute.return_value.data = []
    db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    return db


@pytest.fixture()
def client(mock_db):
    from main import app
    from app import database
    with patch.object(database, "get_db", return_value=mock_db):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
