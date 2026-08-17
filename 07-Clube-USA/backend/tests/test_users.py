"""
Testes de perfil — Fase 0.1.

Cobertura:
- GET /users/me: autenticado, sem token, token inválido
- PUT /users/me: update feliz, ZIP inválido, sem token
- Isolamento multi-tenant: user_id SEMPRE vem do token (nunca do corpo/URL)
"""

from unittest.mock import MagicMock
from tests.conftest import make_jwt

USER_A = "user-aaa-111"
USER_B = "user-bbb-222"

PROFILE_A = {
    "id": USER_A,
    "first_name": "Ana",
    "last_name": "Costa",
    "phone": "555-0000",
    "zip_code": "10001",
    "state": "NY",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


def auth_headers(user_id: str = USER_A) -> dict:
    return {"Authorization": f"Bearer {make_jwt(user_id)}"}


# ───────────────────── GET /users/me ─────────────────

class TestGetProfile:
    def test_get_profile_authenticated(self, client, mock_supabase):
        table_mock = MagicMock()
        (
            table_mock
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.return_value
        ).data = PROFILE_A
        mock_supabase.table.return_value = table_mock

        resp = client.get("/users/me", headers=auth_headers(USER_A))

        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Ana"
        assert resp.json()["id"] == USER_A

    def test_get_profile_unauthenticated(self, client, mock_supabase):
        resp = client.get("/users/me")
        assert resp.status_code == 403  # sem header Authorization

    def test_get_profile_invalid_token(self, client, mock_supabase):
        resp = client.get("/users/me", headers={"Authorization": "Bearer token.lixo"})
        assert resp.status_code == 401

    def test_get_profile_not_found(self, client, mock_supabase):
        table_mock = MagicMock()
        (
            table_mock
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.return_value
        ).data = None
        mock_supabase.table.return_value = table_mock

        resp = client.get("/users/me", headers=auth_headers(USER_A))

        assert resp.status_code == 404

    def test_user_id_from_token_not_modifiable_by_client(self, client, mock_supabase):
        """
        Propriedade de segurança crítica: user_id é lido do JWT, nunca do corpo.
        GET /users/me não aceita user_id no corpo — a rota não tem parâmetros que
        o cliente possa passar para mudar qual perfil é lido.
        """
        table_mock = MagicMock()
        (
            table_mock
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.return_value
        ).data = PROFILE_A
        mock_supabase.table.return_value = table_mock

        # Tenta passar user_id do USER_B no query param (não deve ter efeito)
        resp = client.get(
            f"/users/me?user_id={USER_B}",
            headers=auth_headers(USER_A),
        )

        # Deve retornar perfil do USER_A (do token), não do USER_B
        assert resp.status_code == 200
        eq_call_args = table_mock.select.return_value.eq.call_args
        assert eq_call_args[0][1] == USER_A


# ───────────────────── PUT /users/me ─────────────────

class TestUpdateProfile:
    def _setup_update(self, mock_supabase, updated: dict):
        table_mock = MagicMock()
        (
            table_mock
            .update.return_value
            .eq.return_value
            .execute.return_value
        ).data = [updated]
        mock_supabase.table.return_value = table_mock
        return table_mock

    def test_update_first_name(self, client, mock_supabase):
        updated = {**PROFILE_A, "first_name": "Bruna"}
        table_mock = self._setup_update(mock_supabase, updated)

        resp = client.put(
            "/users/me",
            json={"first_name": "Bruna"},
            headers=auth_headers(USER_A),
        )

        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Bruna"
        # Confirma que o .eq filtra pelo user_id do token, não do corpo
        eq_call = table_mock.update.return_value.eq.call_args
        assert eq_call[0][1] == USER_A

    def test_update_invalid_zip(self, client, mock_supabase):
        resp = client.put(
            "/users/me",
            json={"zip_code": "99999XXXX"},
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    def test_update_unauthenticated(self, client, mock_supabase):
        resp = client.put("/users/me", json={"first_name": "X"})
        assert resp.status_code == 403

    def test_update_ignores_user_id_in_body(self, client, mock_supabase):
        """user_id no corpo não deve mudar o filtro de UPDATE — sempre usa o do token."""
        updated = {**PROFILE_A, "first_name": "Carlos"}
        table_mock = self._setup_update(mock_supabase, updated)

        # Tenta enviar id do USER_B no corpo do update
        resp = client.put(
            "/users/me",
            json={"first_name": "Carlos", "id": USER_B},
            headers=auth_headers(USER_A),
        )

        # Pydantic ignora campos extras por padrão (ProfileUpdateRequest não tem campo "id")
        # O .eq do supabase deve ter sido chamado com USER_A (do token)
        if resp.status_code == 200:
            eq_call = table_mock.update.return_value.eq.call_args
            assert eq_call[0][1] == USER_A
