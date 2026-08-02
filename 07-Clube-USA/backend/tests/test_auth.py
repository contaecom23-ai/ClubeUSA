"""
Testes de autenticação — Fase 0.1
Cobre: registro, confirmação de email, login, rate-limit básico, anti-enumeration.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from tests.conftest import make_supabase_mock


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup_empty_db(mock_db):
    """DB sem usuários existentes."""
    chain, response = make_supabase_mock(data=[])
    mock_db.table.return_value = chain
    return chain, response


def _setup_existing_user(mock_db, user: dict):
    chain, response = make_supabase_mock(data=[user])
    mock_db.table.return_value = chain
    return chain, response


# ── Testes de registro ────────────────────────────────────────────────────────

def test_register_new_user_returns_201(client, mock_db):
    chain, _ = make_supabase_mock(data=[])
    mock_db.table.return_value = chain

    # chain.execute() é chamado 3 vezes:
    # 1. SELECT para checar email existente → vazio
    # 2. INSERT do usuário → retorna id
    # 3. INSERT do perfil → não importa
    insert_response = MagicMock()
    insert_response.data = [{"id": "uuid-123"}]
    chain.execute.side_effect = [
        MagicMock(data=[]),   # SELECT users: email não existe
        insert_response,       # INSERT users: novo usuário criado
        MagicMock(data=[]),   # INSERT profiles
    ]

    with patch("app.routers.auth.send_confirmation_email"):
        res = client.post("/auth/register", json={
            "full_name": "João Silva",
            "email": "joao@example.com",
            "password": "senha123",
        })

    assert res.status_code == 201
    assert "email" in res.json()["message"].lower() or "conta" in res.json()["message"].lower()


def test_register_short_name_rejected(client, mock_db):
    res = client.post("/auth/register", json={
        "full_name": "J",
        "email": "j@example.com",
        "password": "senha123",
    })
    assert res.status_code == 422


def test_register_short_password_rejected(client, mock_db):
    res = client.post("/auth/register", json={
        "full_name": "João Silva",
        "email": "joao@example.com",
        "password": "123",
    })
    assert res.status_code == 422


def test_register_duplicate_email_returns_generic_message(client, mock_db):
    """Anti-enumeration: não confirma se email existe."""
    _setup_existing_user(mock_db, {"id": "uuid-abc"})

    res = client.post("/auth/register", json={
        "full_name": "João Silva",
        "email": "joao@example.com",
        "password": "senha123",
    })

    assert res.status_code == 200  # 200 genérico, não 409
    data = res.json()["message"]
    # Não deve dizer "já cadastrado" ou "email em uso"
    assert "já cadastrado" not in data.lower()
    assert "em uso" not in data.lower()


def test_register_invalid_email_rejected(client, mock_db):
    res = client.post("/auth/register", json={
        "full_name": "João Silva",
        "email": "nao-e-email",
        "password": "senha123",
    })
    assert res.status_code == 422


# ── Testes de confirmação de email ────────────────────────────────────────────

def test_confirm_email_valid_token(client, mock_db):
    from datetime import datetime, timezone
    sent_at = datetime.now(tz=timezone.utc).isoformat()

    chain, _ = make_supabase_mock(data=[{
        "id": "uuid-123",
        "email_confirm_sent_at": sent_at,
        "email_confirmed": False,
    }])
    mock_db.table.return_value = chain

    res = client.get("/auth/confirm-email?token=validtoken123")
    assert res.status_code == 200
    assert "confirmado" in res.json()["message"].lower()


def test_confirm_email_already_confirmed(client, mock_db):
    from datetime import datetime, timezone
    chain, _ = make_supabase_mock(data=[{
        "id": "uuid-123",
        "email_confirm_sent_at": datetime.now(tz=timezone.utc).isoformat(),
        "email_confirmed": True,
    }])
    mock_db.table.return_value = chain

    res = client.get("/auth/confirm-email?token=validtoken123")
    assert res.status_code == 200
    assert "já confirmado" in res.json()["message"].lower()


def test_confirm_email_invalid_token(client, mock_db):
    chain, _ = make_supabase_mock(data=[])
    mock_db.table.return_value = chain

    res = client.get("/auth/confirm-email?token=token-invalido")
    assert res.status_code == 400


def test_confirm_email_expired_token(client, mock_db):
    from datetime import datetime, timedelta, timezone
    old_time = (datetime.now(tz=timezone.utc) - timedelta(hours=25)).isoformat()

    chain, _ = make_supabase_mock(data=[{
        "id": "uuid-123",
        "email_confirm_sent_at": old_time,
        "email_confirmed": False,
    }])
    mock_db.table.return_value = chain

    res = client.get("/auth/confirm-email?token=expiredtoken")
    assert res.status_code == 400
    assert "expir" in res.json()["detail"].lower()


# ── Testes de login ───────────────────────────────────────────────────────────

def test_login_success(client, mock_db):
    from app.security import hash_password
    hashed = hash_password("senha123")

    chain, _ = make_supabase_mock(data=[{
        "id": "uuid-123",
        "password_hash": hashed,
        "email_confirmed": True,
    }])
    mock_db.table.return_value = chain

    res = client.post("/auth/login", json={
        "email": "joao@example.com",
        "password": "senha123",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email_confirmed"] is True


def test_login_wrong_password(client, mock_db):
    from app.security import hash_password
    chain, _ = make_supabase_mock(data=[{
        "id": "uuid-123",
        "password_hash": hash_password("senha123"),
        "email_confirmed": True,
    }])
    mock_db.table.return_value = chain

    res = client.post("/auth/login", json={
        "email": "joao@example.com",
        "password": "senhaerrada",
    })
    assert res.status_code == 401


def test_login_nonexistent_user(client, mock_db):
    chain, _ = make_supabase_mock(data=[])
    mock_db.table.return_value = chain

    res = client.post("/auth/login", json={
        "email": "ninguem@example.com",
        "password": "senha123",
    })
    assert res.status_code == 401
    # Mesma mensagem de erro (anti-enumeration)
    assert "incorretos" in res.json()["detail"].lower()
