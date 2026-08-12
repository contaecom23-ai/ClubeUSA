"""Testa as rotas de perfil e isolamento multi-tenant."""
from unittest.mock import patch

from tests.conftest import TEST_USER_ID, TEST_USER_ID_2

SAMPLE_PROFILE = {
    "id": TEST_USER_ID,
    "full_name": "João Silva",
    "phone": "+1 305 555 1234",
    "zip_code": "33101",
    "state": "FL",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


def test_get_profile_success(client, auth_headers):
    with patch("app.profile.router.get_profile", return_value=SAMPLE_PROFILE):
        r = client.get("/api/profile", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["full_name"] == "João Silva"
    assert r.json()["zip_code"] == "33101"


def test_get_profile_not_found(client, auth_headers):
    with patch("app.profile.router.get_profile", return_value=None):
        r = client.get("/api/profile", headers=auth_headers)
    assert r.status_code == 404


def test_update_profile_success(client, auth_headers):
    updated = {**SAMPLE_PROFILE, "zip_code": "10001", "state": "NY"}
    with patch("app.profile.router.upsert_profile", return_value=updated) as mock_up:
        r = client.put("/api/profile", json={"zip_code": "10001", "state": "NY"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["state"] == "NY"
    # Garante que o user_id usado foi do JWT, não do body
    called_user_id = mock_up.call_args[0][0]
    assert called_user_id == TEST_USER_ID


def test_update_profile_invalid_zip(client, auth_headers):
    r = client.put("/api/profile", json={"zip_code": "abc"}, headers=auth_headers)
    assert r.status_code == 422


def test_update_profile_invalid_state(client, auth_headers):
    r = client.put("/api/profile", json={"state": "XX"}, headers=auth_headers)
    assert r.status_code == 422


def test_update_profile_invalid_name_too_short(client, auth_headers):
    r = client.put("/api/profile", json={"full_name": "A"}, headers=auth_headers)
    assert r.status_code == 422


def test_update_profile_invalid_phone(client, auth_headers):
    r = client.put("/api/profile", json={"phone": "not-a-phone!!!"}, headers=auth_headers)
    assert r.status_code == 422


def test_tenant_isolation_user_id_from_token(client, auth_headers, auth_headers_user2):
    """user_id sempre vem do token — usuário não pode passar o id de outro."""
    captured = {}

    def mock_upsert(user_id, fields):
        captured["user_id"] = user_id
        return {**SAMPLE_PROFILE, "id": user_id}

    with patch("app.profile.router.upsert_profile", side_effect=mock_upsert):
        # user2 tenta fazer PUT sem conseguir mudar para user1
        r = client.put(
            "/api/profile",
            json={"full_name": "Hacker Attempt"},
            headers=auth_headers_user2,
        )

    assert r.status_code == 200
    assert captured["user_id"] == TEST_USER_ID_2  # sempre o do JWT
    assert captured["user_id"] != TEST_USER_ID    # nunca o de outro usuário


def test_profile_requires_auth(client):
    r = client.put("/api/profile", json={"full_name": "Sem token"})
    assert r.status_code == 401
