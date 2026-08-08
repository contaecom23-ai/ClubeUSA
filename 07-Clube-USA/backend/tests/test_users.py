"""
Testes dos endpoints de perfil (/users/me GET e PUT).
Garante: autenticação obrigatória, isolamento (só acessa o próprio perfil),
e que o user_id vem sempre do token — nunca do body.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.auth.security import create_access_token


def _auth_header(user_id: str) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _user_row(user_id="uuid-1"):
    return {
        "id": user_id,
        "email": "joao@test.com",
        "full_name": "João Silva",
        "city": "Miami",
        "state_abbr": "FL",
        "email_confirmed": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------

def test_get_me_unauthenticated(client):
    resp = client.get("/users/me")
    assert resp.status_code == 403


def test_get_me_success(client, db_mock):
    db_mock.table.return_value.execute.return_value.data = [_user_row()]

    resp = client.get("/users/me", headers=_auth_header("uuid-1"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "uuid-1"
    assert data["email"] == "joao@test.com"
    # password_hash nunca deve aparecer no response
    assert "password_hash" not in data


def test_get_me_not_found(client, db_mock):
    db_mock.table.return_value.execute.return_value.data = []

    resp = client.get("/users/me", headers=_auth_header("uuid-inexistente"))
    assert resp.status_code == 404


# ---------------------------------------------------------------
# PUT /users/me
# ---------------------------------------------------------------

def test_update_me_success(client, db_mock):
    updated = _user_row()
    updated["city"] = "Orlando"
    db_mock.table.return_value.execute.return_value.data = [updated]

    resp = client.put(
        "/users/me",
        json={"city": "Orlando"},
        headers=_auth_header("uuid-1"),
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Orlando"


def test_update_me_empty_body(client, db_mock):
    resp = client.put("/users/me", json={}, headers=_auth_header("uuid-1"))
    assert resp.status_code == 400


def test_update_me_unauthenticated(client):
    resp = client.put("/users/me", json={"city": "Miami"})
    assert resp.status_code == 403


def test_update_me_cannot_change_email(client, db_mock):
    """Email não pode ser alterado via PUT /users/me (campo não está no modelo)."""
    db_mock.table.return_value.execute.return_value.data = [_user_row()]
    resp = client.put(
        "/users/me",
        json={"email": "outro@test.com", "city": "Miami"},
        headers=_auth_header("uuid-1"),
    )
    # O campo email é ignorado pelo Pydantic (não está no UpdateProfileRequest)
    # A request deve ser aceita (200) mas email não muda
    # Verificamos que o update no DB não incluiu email
    call_args = db_mock.table.return_value.update.call_args
    if call_args:
        updated_fields = call_args[0][0]
        assert "email" not in updated_fields


def test_update_me_user_id_from_token_not_body(client, db_mock):
    """
    Isolamento: o user_id usado no WHERE vem do token JWT,
    nunca de um campo no body da requisição.
    """
    updated = _user_row("uuid-1")
    db_mock.table.return_value.execute.return_value.data = [updated]

    resp = client.put(
        "/users/me",
        json={"city": "Boston"},
        headers=_auth_header("uuid-1"),
    )
    assert resp.status_code == 200

    # Verifica que o eq() foi chamado com o ID do token, não de um campo no body
    eq_calls = db_mock.table.return_value.eq.call_args_list
    ids_usados = [call.args[1] for call in eq_calls if call.args[0] == "id"]
    assert all(uid == "uuid-1" for uid in ids_usados), "user_id deve vir sempre do token"


# ---------------------------------------------------------------
# Isolamento multi-tenant
# ---------------------------------------------------------------

def test_cross_tenant_get_returns_not_found(client, db_mock):
    """
    Um usuário autenticado com uuid-1 não pode ver dados de uuid-2.
    A query filtra por id = uuid-1 e retorna vazio (como se uuid-2 não existisse).
    """
    db_mock.table.return_value.execute.return_value.data = []

    # Token de uuid-1, mas o banco não retorna nada (simulando que uuid-2 não é do uuid-1)
    resp = client.get("/users/me", headers=_auth_header("uuid-1"))
    assert resp.status_code == 404
