"""Testa a camada de autenticação JWT (middleware)."""
from tests.conftest import make_token, TEST_USER_ID


def test_health_is_public(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_profile_requires_auth(client):
    r = client.get("/api/profile")
    assert r.status_code == 401


def test_expired_token_rejected(client):
    headers = {"Authorization": f"Bearer {make_token(expired=True)}"}
    r = client.get("/api/profile", headers=headers)
    assert r.status_code == 401
    assert "expirada" in r.json()["detail"].lower()


def test_invalid_token_rejected(client):
    r = client.get("/api/profile", headers={"Authorization": "Bearer token.invalido.aqui"})
    assert r.status_code == 401


def test_anon_role_rejected(client):
    token = make_token(role="anon")
    r = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert "email" in r.json()["detail"].lower()


def test_missing_bearer_prefix(client):
    r = client.get("/api/profile", headers={"Authorization": make_token()})
    assert r.status_code == 401 or r.status_code == 403


def test_valid_token_passes_middleware(client, auth_headers):
    """Com token válido, o middleware não bloqueia (o 404 do profile é da lógica de negócio)."""
    from unittest.mock import patch
    with patch("app.profile.router.get_profile", return_value=None):
        r = client.get("/api/profile", headers=auth_headers)
    assert r.status_code == 404  # sem perfil, mas auth passou
