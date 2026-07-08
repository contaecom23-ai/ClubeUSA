"""Tests for /api/v1/profile endpoints."""

import uuid
from unittest.mock import MagicMock


def _profile_row(user_id: str, full_name: str = "Test User", zip_code: str = "10001"):
    return {
        "id": user_id,
        "full_name": full_name,
        "zip_code": zip_code,
        "state_us": "NY",
        "city": "New York",
        "whatsapp": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


# -------------------------------------------------------------- GET /profile --


def test_get_profile_success(client, mock_supabase, confirmed_user, auth_headers, user_id):
    row = _profile_row(user_id)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=row)
    mock_supabase.auth.admin.get_user_by_id.return_value = MagicMock(user=confirmed_user)

    resp = client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Test User"
    assert body["email_confirmed"] is True
    assert body["id"] == user_id


def test_get_profile_requires_auth(client):
    resp = client.get("/api/v1/profile")
    assert resp.status_code == 403


def test_get_profile_not_found(client, mock_supabase, auth_headers):
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=None)

    resp = client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 404


# -------------------------------------------------------------- PATCH /profile --


def test_update_profile_success(client, mock_supabase, confirmed_user, auth_headers, user_id):
    updated_row = _profile_row(user_id, full_name="Maria Updated")
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[updated_row])
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=updated_row)
    mock_supabase.auth.admin.get_user_by_id.return_value = MagicMock(user=confirmed_user)

    resp = client.patch(
        "/api/v1/profile",
        headers=auth_headers,
        json={"full_name": "Maria Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Maria Updated"


def test_update_profile_empty_body(client, mock_supabase, auth_headers):
    resp = client.patch("/api/v1/profile", headers=auth_headers, json={})
    assert resp.status_code == 400


def test_update_profile_invalid_state(client, mock_supabase, auth_headers):
    resp = client.patch(
        "/api/v1/profile",
        headers=auth_headers,
        json={"state_us": "XX"},
    )
    assert resp.status_code == 422


def test_update_profile_requires_auth(client):
    resp = client.patch("/api/v1/profile", json={"full_name": "Hacker"})
    assert resp.status_code == 403


# --------------------------------------------------------- cross-tenant check --


def test_profile_isolated_by_token(client, mock_supabase, confirmed_user, auth_headers, user_id):
    """IDOR check: token for user_id must ONLY read that user's profile row."""
    attacker_id = str(uuid.uuid4())
    attacker_row = _profile_row(attacker_id, full_name="Victim's Data")

    # The query is always filtered by the user_id from the token (not from request)
    # So even if attacker sends their own token, they only see their own row.
    # This test confirms the router always passes user_id from the token to .eq()
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=_profile_row(user_id))
    mock_supabase.auth.admin.get_user_by_id.return_value = MagicMock(user=confirmed_user)

    resp = client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 200
    # Confirm the eq() call used the token's user_id
    call_args = mock_supabase.table.return_value.select.return_value.eq.call_args
    assert call_args[0][1] == user_id, "Profile query must use user_id from token, not from request"
