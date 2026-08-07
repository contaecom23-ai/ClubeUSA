"""
Fixtures de teste com banco mockado.
Nenhuma chamada real ao Supabase aqui — tudo in-memory via pytest-mock.
"""
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Injeta env vars antes de importar a app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "x" * 64)
os.environ.setdefault("JWT_SECRET", "test_secret_key_minimo_32_caracteres_aqui")
os.environ.setdefault("EMAIL_ENABLED", "false")
os.environ.setdefault("FRONTEND_URL", "http://localhost:8080")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:8080")

# Patch do cliente Supabase antes de importar qualquer módulo que o use
_mock_db = MagicMock()


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """Substitui get_db() por um mock em todos os testes."""
    # side_effect=True, return_value=True: limpa side_effects de testes anteriores
    # (reset_mock() padrão não limpa esses atributos, causando StopIteration ao reusar listas)
    _mock_db.reset_mock(side_effect=True, return_value=True)
    monkeypatch.setattr("database.get_db", lambda: _mock_db)
    monkeypatch.setattr("routes.auth.get_db", lambda: _mock_db)
    monkeypatch.setattr("routes.profile.get_db", lambda: _mock_db)
    return _mock_db


@pytest.fixture
def client():
    # Importa aqui para pegar o monkeypatch ativo
    from main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def sample_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def auth_headers(sample_user_id):
    from auth_utils import create_access_token
    token = create_access_token(sample_user_id)
    return {"Authorization": f"Bearer {token}"}
