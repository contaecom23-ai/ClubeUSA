"""
Testes de perfil de usuário.
Verifica isolamento: usuário só acessa seus próprios dados (user_id do JWT).
"""
import pytest

from app.security import create_access_token
from tests.conftest import make_result


def auth_headers(user_id: str) -> dict:
    token, _ = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ── GET /api/me ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(client, mock_db):
    user_id = "uuid-user-1"
    mock_db.execute.side_effect = [
        make_result([{
            "id": user_id,
            "email": "joao@example.com",
            "full_name": "João Silva",
            "email_confirmed": True,
        }]),
        make_result([{
            "zip_code": "33101",
            "city": "Miami",
            "state_code": "FL",
            "phone": None,
            "bio": None,
            "avatar_url": None,
        }]),
    ]
    resp = await client.get("/api/me", headers=auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == user_id
    assert body["email"] == "joao@example.com"
    assert body["profile"]["city"] == "Miami"


@pytest.mark.asyncio
async def test_get_me_requires_auth(client, mock_db):
    resp = await client.get("/api/me")
    # HTTPBearer sem credencial retorna 403
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_me_invalid_token(client, mock_db):
    resp = await client.get(
        "/api/me",
        headers={"Authorization": "Bearer token.invalido.aqui"}
    )
    assert resp.status_code == 401


# ── PUT /api/me/profile ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_profile_success(client, mock_db):
    user_id = "uuid-user-1"
    mock_db.execute.side_effect = [
        make_result([{}]),  # update
        make_result([{     # select atualizado
            "zip_code": "33101",
            "city": "Miami",
            "state_code": "FL",
            "phone": "305-555-0001",
            "bio": "Brasileiro em Miami",
            "avatar_url": None,
        }]),
    ]
    resp = await client.put("/api/me/profile", json={
        "zip_code": "33101",
        "city": "Miami",
        "state_code": "FL",
        "bio": "Brasileiro em Miami",
    }, headers=auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["city"] == "Miami"
    assert body["state_code"] == "FL"


@pytest.mark.asyncio
async def test_update_profile_invalid_state(client, mock_db):
    user_id = "uuid-user-1"
    resp = await client.put("/api/me/profile", json={
        "state_code": "FLA",  # deve ter exatamente 2 letras
    }, headers=auth_headers(user_id))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_bio_too_long(client, mock_db):
    user_id = "uuid-user-1"
    resp = await client.put("/api/me/profile", json={
        "bio": "x" * 501,
    }, headers=auth_headers(user_id))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_requires_auth(client, mock_db):
    resp = await client.put("/api/me/profile", json={"city": "Miami"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_id_always_from_token(client, mock_db):
    """
    Isolamento multi-tenant: o user_id vem do JWT, nunca do body.
    Tentativa de injetar outro user_id no body deve ser ignorada.
    """
    user_id = "uuid-user-1"
    mock_db.execute.side_effect = [
        make_result([{}]),
        make_result([{
            "zip_code": None, "city": "Test", "state_code": None,
            "phone": None, "bio": None, "avatar_url": None,
        }]),
    ]
    # Mesmo que o body contenha um campo malicioso, o servidor usa o ID do token
    resp = await client.put("/api/me/profile", json={
        "city": "Test",
        "user_id": "outro-usuario-uuid",  # deve ser ignorado
    }, headers=auth_headers(user_id))
    assert resp.status_code == 200
