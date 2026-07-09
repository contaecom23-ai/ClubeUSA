"""Testes de autenticação: middleware JWT, rotas públicas e protegidas."""
from tests.conftest import make_expired_jwt, USER_A_ID


def test_health_public(client):
    """Rota /health é pública e retorna 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_me_sem_token(client):
    """/auth/me sem token retorna 403 (HTTPBearer rejeita antes de 401)."""
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)


def test_me_token_invalido(client):
    """/auth/me com token inválido retorna 401."""
    resp = client.get("/auth/me", headers={"Authorization": "Bearer token.falso.aqui"})
    assert resp.status_code == 401


def test_me_token_expirado(client):
    """/auth/me com token expirado retorna 401."""
    token = make_expired_jwt(USER_A_ID)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_me_token_valido(client, token_a):
    """/auth/me com token válido retorna user_id e email."""
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == USER_A_ID
    assert "email" in data
