"""
Tests for /profile endpoints.

Key invariant: user_id ALWAYS comes from the JWT, never from client input (IDOR prevention).
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

from tests.conftest import TEST_EMAIL, TEST_USER_ID

CONFIRMED_AT = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _setup_auth(mock_supabase, user_id=TEST_USER_ID, email=TEST_EMAIL, confirmed=True):
    mock_user_obj = MagicMock()
    mock_user_obj.id = user_id
    mock_user_obj.email = email
    mock_user_obj.email_confirmed_at = CONFIRMED_AT if confirmed else None
    mock_supabase.auth.admin.get_user.return_value = MagicMock(user=mock_user_obj)


AUTH_HEADERS = {"Authorization": "Bearer test-token"}

FULL_PROFILE_DATA = {
    "id": TEST_USER_ID,
    "full_name": "João Silva",
    "state": "FL",
    "city": "Orlando",
    "zip_code": "32801",
}


# ── GET /profile ──────────────────────────────────────────────────────────────

def test_get_profile_success(client, mock_supabase):
    _setup_auth(mock_supabase)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=FULL_PROFILE_DATA
    )

    res = client.get("/profile", headers=AUTH_HEADERS)

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == TEST_USER_ID
    assert body["full_name"] == "João Silva"
    assert body["state"] == "FL"
    assert body["zip_code"] == "32801"


def test_get_profile_unconfirmed_email(client, mock_supabase):
    _setup_auth(mock_supabase, confirmed=False)

    res = client.get("/profile", headers=AUTH_HEADERS)

    assert res.status_code == 403
    assert "confirmado" in res.json()["detail"]


def test_get_profile_unauthenticated(client, mock_supabase):
    res = client.get("/profile")
    assert res.status_code == 403


def test_get_profile_creates_if_missing(client, mock_supabase):
    """Profile not found in DB → auto-create and return empty profile."""
    _setup_auth(mock_supabase)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    res = client.get("/profile", headers=AUTH_HEADERS)

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == TEST_USER_ID
    assert body["full_name"] is None


# ── PUT /profile ──────────────────────────────────────────────────────────────

def test_update_profile_success(client, mock_supabase):
    _setup_auth(mock_supabase)
    updated = {**FULL_PROFILE_DATA, "city": "Miami"}
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[updated]
    )

    res = client.put("/profile", json={"city": "Miami"}, headers=AUTH_HEADERS)

    assert res.status_code == 200
    assert res.json()["city"] == "Miami"


def test_update_profile_invalid_state(client, mock_supabase):
    _setup_auth(mock_supabase)

    res = client.put("/profile", json={"state": "XX"}, headers=AUTH_HEADERS)

    assert res.status_code == 422


def test_update_profile_invalid_zip(client, mock_supabase):
    _setup_auth(mock_supabase)

    res = client.put("/profile", json={"zip_code": "ABCDE"}, headers=AUTH_HEADERS)

    assert res.status_code == 422


def test_update_profile_zip_valid_formats(client, mock_supabase):
    _setup_auth(mock_supabase)
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{**FULL_PROFILE_DATA, "zip_code": "32801-1234"}]
    )

    res = client.put("/profile", json={"zip_code": "32801-1234"}, headers=AUTH_HEADERS)

    assert res.status_code == 200
    assert res.json()["zip_code"] == "32801-1234"


def test_update_profile_empty_body(client, mock_supabase):
    _setup_auth(mock_supabase)

    res = client.put("/profile", json={}, headers=AUTH_HEADERS)

    assert res.status_code == 400
    assert "atualizar" in res.json()["detail"]


def test_update_profile_no_cross_tenant_access(client, mock_supabase):
    """
    IDOR check: even if the client sends a different user_id in the body,
    the update must always use the user_id from the JWT.
    """
    victim_id = "aaaaaaaa-0000-0000-0000-000000000000"
    _setup_auth(mock_supabase, user_id=TEST_USER_ID)

    # Attempt to send victim's id — our schema ignores unknown fields,
    # and the router always uses current_user["id"] from the JWT.
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[FULL_PROFILE_DATA]
    )

    res = client.put(
        "/profile",
        json={"city": "Hacked", "id": victim_id},  # id field ignored by schema
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    # Verify the .eq() was called with the authenticated user's ID, not the victim's
    eq_call_args = mock_supabase.table.return_value.update.return_value.eq.call_args
    assert eq_call_args[0][1] == TEST_USER_ID


def test_update_profile_unconfirmed_email(client, mock_supabase):
    _setup_auth(mock_supabase, confirmed=False)

    res = client.put("/profile", json={"city": "Miami"}, headers=AUTH_HEADERS)

    assert res.status_code == 403
