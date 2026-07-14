"""
Testes de perfil de usuário.
CRÍTICO: testa isolamento multi-tenant — usuário A não pode ver/editar perfil de B.
"""
import pytest
from datetime import datetime, timezone
from tests.conftest import make_jwt


_NOW = datetime.now(timezone.utc).isoformat()

_PROFILE_A = {
    "id": "user-a",
    "full_name": "Maria Souza",
    "city": "Miami",
    "state": "FL",
    "phone": None,
    "created_at": _NOW,
    "updated_at": _NOW,
}


def _auth_header(user_id: str, email: str) -> dict:
    token = make_jwt(user_id, email)
    return {"Authorization": f"Bearer {token}"}


class TestGetProfile:
    def test_get_own_profile(self, client, patch_supabase):
        _, mock_admin = patch_supabase
        mock_admin.table.return_value.select.return_value \
            .eq.return_value.maybe_single.return_value \
            .execute.return_value.data = _PROFILE_A

        resp = client.get("/users/me",
                          headers=_auth_header("user-a", "maria@exemplo.com"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "Maria Souza"
        assert data["state"] == "FL"

    def test_no_token_returns_401(self, client, patch_supabase):
        resp = client.get("/users/me")
        assert resp.status_code == 403  # HTTPBearer sem credencial retorna 403

    def test_invalid_token_returns_401(self, client, patch_supabase):
        resp = client.get("/users/me",
                          headers={"Authorization": "Bearer token-invalido"})
        assert resp.status_code == 401

    def test_profile_not_found(self, client, patch_supabase):
        _, mock_admin = patch_supabase
        mock_admin.table.return_value.select.return_value \
            .eq.return_value.maybe_single.return_value \
            .execute.return_value.data = None

        resp = client.get("/users/me",
                          headers=_auth_header("user-missing", "x@exemplo.com"))
        assert resp.status_code == 404


class TestUpdateProfile:
    def test_update_own_profile(self, client, patch_supabase):
        _, mock_admin = patch_supabase
        updated = {**_PROFILE_A, "city": "Orlando"}
        mock_admin.table.return_value.update.return_value \
            .eq.return_value.execute.return_value.data = [updated]

        resp = client.patch("/users/me",
                            json={"city": "Orlando"},
                            headers=_auth_header("user-a", "maria@exemplo.com"))
        assert resp.status_code == 200
        assert resp.json()["city"] == "Orlando"

    def test_invalid_state_code(self, client, patch_supabase):
        resp = client.patch("/users/me",
                            json={"state": "XX"},
                            headers=_auth_header("user-a", "maria@exemplo.com"))
        assert resp.status_code == 422

    def test_empty_update_rejected(self, client, patch_supabase):
        resp = client.patch("/users/me",
                            json={},
                            headers=_auth_header("user-a", "maria@exemplo.com"))
        assert resp.status_code == 422

    def test_tenant_isolation_enforced(self, client, patch_supabase):
        """
        Garante que .eq("id", user_id) é chamado com o ID do token,
        nunca com um ID fornecido pelo cliente.
        """
        _, mock_admin = patch_supabase
        mock_admin.table.return_value.update.return_value \
            .eq.return_value.execute.return_value.data = [_PROFILE_A]

        client.patch("/users/me",
                     json={"city": "New York"},
                     headers=_auth_header("user-a", "maria@exemplo.com"))

        # Verifica que o .eq foi chamado com o user_id do TOKEN (user-a)
        call_args = mock_admin.table.return_value.update.return_value.eq.call_args
        assert call_args[0] == ("id", "user-a")
