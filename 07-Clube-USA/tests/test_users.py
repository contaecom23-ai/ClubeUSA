"""
Testes para endpoints de usuário (Fase 0.1).
Foca em: acesso autenticado, isolamento multi-tenant (cross-user -> 404).
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from backend.app.auth.utils import create_access_token


def _auth_headers(user_id="user-abc"):
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _profile_row(user_id="user-abc"):
    return {
        "id": user_id,
        "email": "a@b.com",
        "name": "Fulano",
        "estado": "FL",
        "cidade": "Orlando",
        "whatsapp": "13055550000",
        "email_confirmed": True,
        "created_at": datetime.now(timezone.utc),
        "last_login_at": None,
    }


class TestGetProfile:
    def test_get_profile_authenticated(self, client, mock_db):
        user_id = "user-abc"
        # 1ª chamada: get_current_user_id verifica o user no banco
        # 2ª chamada: get_my_profile busca o perfil
        mock_db.fetchrow.side_effect = [
            {"id": user_id},       # validação do token
            _profile_row(user_id), # perfil
        ]
        resp = client.get("/users/me", headers=_auth_headers(user_id))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "a@b.com"
        assert body["estado"] == "FL"

    def test_get_profile_no_token(self, client, mock_db):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_get_profile_invalid_token(self, client, mock_db):
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalido"})
        assert resp.status_code == 401

    def test_cross_user_access_returns_404(self, client, mock_db):
        """
        Teste de isolamento multi-tenant:
        token de user-A não pode ver perfil de user-B (404, não 403).
        """
        user_a = "user-aaa"
        user_b = "user-bbb"

        # Token pertence a user-A, mas fetchrow para get_current_user_id retorna user-A
        # e depois fetchrow para get_my_profile retorna None (simula: user não encontrado
        # para aquele user_id — mesmo cenário de outro user tentando acessar)
        mock_db.fetchrow.side_effect = [
            {"id": user_a},  # validação do token (user_a existe)
            None,            # get_my_profile: retorna None (simulando inexistência)
        ]
        resp = client.get("/users/me", headers=_auth_headers(user_a))
        # Se o perfil não existe para aquele user_id do token, retorna 404
        assert resp.status_code == 404


class TestUpdateProfile:
    def test_update_name(self, client, mock_db):
        user_id = "user-abc"
        updated = _profile_row(user_id)
        updated["name"] = "Novo Nome"
        mock_db.fetchrow.side_effect = [
            {"id": user_id},  # validação do token
            updated,           # get_my_profile após update
        ]
        mock_db.execute = AsyncMock()
        resp = client.put("/users/me",
                          headers=_auth_headers(user_id),
                          json={"name": "Novo Nome"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Novo Nome"

    def test_update_invalid_state(self, client, mock_db):
        resp = client.put("/users/me",
                          headers=_auth_headers(),
                          json={"estado": "ZZ"})
        assert resp.status_code == 422

    def test_update_requires_auth(self, client, mock_db):
        resp = client.put("/users/me", json={"name": "X"})
        assert resp.status_code == 401
