from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app import dependencies
from app.main import app
from tests.conftest import (
    TEST_OTHER_USER_ID,
    TEST_USER_ID,
    _make_mock_supabase,
    make_token,
)


# ── GET /users/me ─────────────────────────────────────────────────────────────


def test_get_me_success(client: TestClient, auth_headers: dict) -> None:
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == TEST_USER_ID
    assert data["first_name"] == "João"
    assert data["zip_code"] == "10001"


def test_get_me_unauthenticated(client: TestClient) -> None:
    resp = client.get("/users/me")
    assert resp.status_code == 403


def test_get_me_invalid_token(client: TestClient) -> None:
    resp = client.get("/users/me", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401


def test_get_me_profile_not_found(client: TestClient) -> None:
    mock = _make_mock_supabase()
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=None
    )
    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {make_token()}"})
    dependencies._supabase_client = original

    assert resp.status_code == 404


# ── PATCH /users/me ───────────────────────────────────────────────────────────


def test_update_me_success(client: TestClient, auth_headers: dict) -> None:
    resp = client.patch("/users/me", json={"first_name": "João Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "João Updated"


def test_update_me_invalid_zip(client: TestClient, auth_headers: dict) -> None:
    resp = client.patch("/users/me", json={"zip_code": "ZZZZZ"}, headers=auth_headers)
    assert resp.status_code == 422


def test_update_me_empty_name(client: TestClient, auth_headers: dict) -> None:
    resp = client.patch("/users/me", json={"first_name": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_update_me_no_fields(client: TestClient, auth_headers: dict) -> None:
    resp = client.patch("/users/me", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_update_me_unauthenticated(client: TestClient) -> None:
    resp = client.patch("/users/me", json={"first_name": "Hack"})
    assert resp.status_code == 403


# ── isolamento multi-tenant ───────────────────────────────────────────────────


def test_cross_tenant_get_returns_own_data_only(client: TestClient) -> None:
    """Usuário A não pode acessar dados do usuário B.
    O filtro é sempre feito por sub do JWT, nunca pelo body.
    """
    other_token = make_token(user_id=TEST_OTHER_USER_ID, email="outro@example.com")

    mock = _make_mock_supabase()
    not_found = MagicMock(data=None)
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = not_found

    original = dependencies._supabase_client
    dependencies._supabase_client = mock
    resp = client.get(
        "/users/me", headers={"Authorization": f"Bearer {other_token}"}
    )
    dependencies._supabase_client = original

    assert resp.status_code == 404

    # Verifica que a query usou o ID do TOKEN, não qualquer ID do body
    called_with = mock.table.return_value.select.return_value.eq.call_args
    assert called_with[0][0] == "id"
    assert called_with[0][1] == TEST_OTHER_USER_ID
