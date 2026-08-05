"""
Configuração de testes.
Usa JWT secret de teste e mock do cliente Supabase.
Nenhuma chamada real ao Supabase ocorre durante os testes.
"""
import os
import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# ─── JWT de teste ─────────────────────────────────────────────────────────────
TEST_JWT_SECRET = "x" * 64  # 64 chars — válido para HS256
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID_B = "00000000-0000-0000-0000-000000000002"

# Env vars de teste (antes de importar o app)
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("FRONTEND_URL", "http://localhost:8000")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:8000")


def make_token(user_id: str, expired: bool = False) -> str:
    exp = int(time.time()) + (-3600 if expired else 3600)
    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "exp": exp,
        "iat": int(time.time()),
        "email": f"{user_id}@example.com",
        "role": "authenticated",
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def client(mocker):
    """
    TestClient com Supabase mockado.
    Nenhuma conexão real ocorre.
    """
    # Importa depois de setar env vars
    from core.config import get_settings
    from main import app

    get_settings.cache_clear()

    # Mock do cliente Supabase — retornado por get_supabase()
    mock_sb = _build_supabase_mock(mocker)
    mocker.patch("core.supabase_client.get_supabase", return_value=mock_sb)
    mocker.patch("routers.auth.get_supabase", return_value=mock_sb)

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, mock_sb


def _build_supabase_mock(mocker):
    """Constrói mock do cliente Supabase com comportamentos padrão."""
    import types

    sb = mocker.MagicMock()

    # auth.sign_up padrão: sucesso
    user_obj = mocker.MagicMock()
    user_obj.id = TEST_USER_ID
    user_obj.email = "user@example.com"
    user_obj.email_confirmed_at = None
    auth_response = mocker.MagicMock()
    auth_response.user = user_obj
    sb.auth.sign_up.return_value = auth_response

    # auth.sign_in_with_password padrão: sucesso
    session_obj = mocker.MagicMock()
    session_obj.access_token = make_token(TEST_USER_ID)
    session_obj.refresh_token = "test-refresh-token"
    login_response = mocker.MagicMock()
    login_response.session = session_obj
    sb.auth.sign_in_with_password.return_value = login_response

    # auth.admin.get_user_by_id padrão
    admin_user = mocker.MagicMock()
    admin_user.user = user_obj
    sb.auth.admin.get_user_by_id.return_value = admin_user

    # table("users_profile").insert(...).execute()
    insert_result = mocker.MagicMock()
    insert_result.data = [
        {
            "user_id": TEST_USER_ID,
            "full_name": "João Silva",
            "email": "user@example.com",
        }
    ]
    sb.table.return_value.insert.return_value.execute.return_value = insert_result

    # table("users_profile").select(...).eq(...).single().execute()
    select_result = mocker.MagicMock()
    select_result.data = {
        "user_id": TEST_USER_ID,
        "full_name": "João Silva",
        "email": "user@example.com",
    }
    (
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value
    ) = select_result

    # table("users_profile").update(...).eq(...).execute()
    update_result = mocker.MagicMock()
    update_result.data = [
        {
            "user_id": TEST_USER_ID,
            "full_name": "Novo Nome",
            "email": "user@example.com",
        }
    ]
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = (
        update_result
    )

    return sb
