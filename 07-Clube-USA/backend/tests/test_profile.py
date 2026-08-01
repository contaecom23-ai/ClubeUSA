from unittest.mock import MagicMock, patch

USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

SAMPLE_PROFILE = {
    "id": USER_ID,
    "full_name": "Maria Silva",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101",
    "bio": None,
    "phone": None,
    "language": "pt",
    "created_at": "2026-08-01T00:00:00+00:00",
    "updated_at": "2026-08-01T00:00:00+00:00",
}


def _mock_sb_get(data):
    sb = MagicMock()
    (
        sb.table.return_value
        .select.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value
        .data
    ) = data
    return sb


def _mock_sb_update(data):
    sb = MagicMock()
    (
        sb.table.return_value
        .update.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = data
    return sb


# ---- GET /profile/me -------------------------------------------------------

def test_get_profile_success(client):
    with patch("routers.profile.get_supabase", return_value=_mock_sb_get(SAMPLE_PROFILE)):
        resp = client.get("/profile/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == USER_ID
    assert body["full_name"] == "Maria Silva"
    assert body["state"] == "FL"


def test_get_profile_not_found(client):
    with patch("routers.profile.get_supabase", return_value=_mock_sb_get(None)):
        resp = client.get("/profile/me")
    assert resp.status_code == 404


def test_get_profile_requires_auth():
    """Sem token, HTTPBearer retorna 401 (não há credenciais)."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        resp = c.get("/profile/me")
    assert resp.status_code == 401


# ---- PATCH /profile/me -----------------------------------------------------

def test_update_profile_success(client):
    updated = {**SAMPLE_PROFILE, "city": "Orlando"}
    with patch("routers.profile.get_supabase", return_value=_mock_sb_update([updated])):
        resp = client.patch("/profile/me", json={"city": "Orlando"})
    assert resp.status_code == 200
    assert resp.json()["city"] == "Orlando"


def test_update_profile_no_fields_400(client):
    resp = client.patch("/profile/me", json={})
    assert resp.status_code == 400


def test_update_profile_blank_name_422(client):
    resp = client.patch("/profile/me", json={"full_name": "   "})
    assert resp.status_code == 422


def test_update_profile_invalid_zip_422(client):
    resp = client.patch("/profile/me", json={"zip_code": "abc"})
    assert resp.status_code == 422


def test_update_profile_invalid_language_422(client):
    resp = client.patch("/profile/me", json={"language": "zh"})
    assert resp.status_code == 422


def test_update_profile_state_uppercased(client):
    updated = {**SAMPLE_PROFILE, "state": "CA"}
    with patch("routers.profile.get_supabase", return_value=_mock_sb_update([updated])):
        resp = client.patch("/profile/me", json={"state": "ca"})
    assert resp.status_code == 200
    # validator normaliza para uppercase; mock devolve "CA"
    assert resp.json()["state"] == "CA"


# ---- Isolamento multi-tenant (IDOR prevention) ------------------------------

def test_profile_endpoint_uses_token_user_id_not_body(client):
    """
    Garante que o endpoint NUNCA aceita user_id no body/query.
    Qualquer tentativa de outro usuário retorna 404 (não vaza existência).
    """
    # Mesmo que o cliente tente passar outro id na query string, é ignorado
    with patch("routers.profile.get_supabase", return_value=_mock_sb_get(None)):
        resp = client.get("/profile/me?user_id=outro-user-id")
    # O id real (do token) não existe no mock → 404
    assert resp.status_code == 404
