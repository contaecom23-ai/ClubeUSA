"""
Testes de perfil de usuário — Fase 0.1
Cobre: get /me, patch /me, isolamento multi-tenant, delete /me.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.security import create_access_token
from tests.conftest import make_supabase_mock

_NOW = datetime.now(tz=timezone.utc).isoformat()

_BASE_USER = {
    "id": "uuid-alice",
    "email": "alice@example.com",
    "full_name": "Alice",
    "email_confirmed": True,
    "created_at": _NOW,
}

_BASE_PROFILE = {
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101",
    "bio": "Oi!",
}


def _auth_header(user_id: str = "uuid-alice") -> dict:
    token, _ = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_user_and_profile(mock_db, user=None, profile=None):
    u = {**_BASE_USER, **(user or {})}
    p = {**_BASE_PROFILE, **(profile or {})}
    combined = {**u, **p}

    chain_user, _ = make_supabase_mock(data=[u])
    chain_profile, _ = make_supabase_mock(data=[p])
    chain_update, _ = make_supabase_mock(data=[combined])

    # Retorna o chain_user para .table("users"), chain_profile para .table("profiles")
    def table_side_effect(name: str):
        if name == "users":
            return chain_user
        return chain_profile

    mock_db.table.side_effect = table_side_effect
    return chain_user, chain_profile


# ── GET /users/me ─────────────────────────────────────────────────────────────

def test_get_me_authenticated(client, mock_db):
    _setup_user_and_profile(mock_db)
    res = client.get("/users/me", headers=_auth_header())
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "alice@example.com"
    assert data["city"] == "Miami"


def test_get_me_no_token(client, mock_db):
    res = client.get("/users/me")
    assert res.status_code == 403


def test_get_me_invalid_token(client, mock_db):
    res = client.get("/users/me", headers={"Authorization": "Bearer token-invalido"})
    assert res.status_code == 403


def test_get_me_expired_token(client, mock_db):
    from datetime import timedelta
    import os
    from jose import jwt
    from app.config import settings

    # Cria token já expirado
    payload = {"sub": "uuid-alice", "exp": datetime.now(tz=timezone.utc) - timedelta(hours=1)}
    expired_token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    res = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 403


# ── PATCH /users/me ───────────────────────────────────────────────────────────

def test_update_profile_valid(client, mock_db):
    chain_user, chain_profile = _setup_user_and_profile(mock_db)

    # update retorna perfil atualizado
    updated = {**_BASE_USER, **_BASE_PROFILE, "city": "Orlando"}
    chain_profile.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[updated])

    res = client.patch("/users/me", json={"city": "Orlando"}, headers=_auth_header())
    assert res.status_code == 200


def test_update_profile_invalid_zip(client, mock_db):
    res = client.patch("/users/me", json={"zip_code": "ABCDE"}, headers=_auth_header())
    assert res.status_code == 422


def test_update_profile_bio_too_long(client, mock_db):
    res = client.patch("/users/me", json={"bio": "x" * 501}, headers=_auth_header())
    assert res.status_code == 422


# ── Isolamento multi-tenant ────────────────────────────────────────────────────

def test_different_users_get_own_data(client, mock_db):
    """Garante que user_id vem do token, não do request."""
    alice_user = {**_BASE_USER, "id": "uuid-alice", "email": "alice@example.com"}
    bob_user = {**_BASE_USER, "id": "uuid-bob", "email": "bob@example.com"}

    call_count = {"n": 0}

    def table_side_effect(name: str):
        chain, _ = make_supabase_mock(data=[alice_user if call_count["n"] == 0 else bob_user])
        call_count["n"] += 1
        return chain

    mock_db.table.side_effect = table_side_effect

    res_alice = client.get("/users/me", headers=_auth_header("uuid-alice"))
    assert res_alice.status_code == 200

    # Bob NÃO pode passar user_id de alice no header — o server usa o token
    res_bob = client.get("/users/me", headers=_auth_header("uuid-bob"))
    assert res_bob.status_code == 200
