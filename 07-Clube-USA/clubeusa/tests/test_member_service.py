"""
Tests for services/member_service.py

Focus: registration flow correctness, especially the re-login path
where an already-registered member calls /auth/register again.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sb(existing_data=None, insert_data=None):
    """Return a MagicMock Supabase client with configurable table responses."""
    sb = MagicMock()
    # SELECT (existing member check)
    sb.table().select().eq().execute.return_value.data = existing_data or []
    # INSERT (new member)
    if insert_data is not None:
        sb.table().insert().execute.return_value.data = insert_data
    return sb


# ---------------------------------------------------------------------------
# Re-login path: VIP plan preserved in token
# ---------------------------------------------------------------------------

def test_relogin_vip_member_token_contains_vip_plan(mocker):
    """
    Regression: when a VIP member calls /auth/register with their phone,
    the returned token must carry plan='vip', not plan='free'.
    Before the fix the SELECT only fetched id+status, so plan defaulted to free.
    """
    from services.member_service import register_member

    existing = [{"id": "uuid-vip", "status": "active", "plan": "vip"}]
    mock_sb = _make_sb(existing_data=existing)
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    captured_tokens = []

    def fake_create_token(member_id, plan="free"):
        captured_tokens.append({"member_id": member_id, "plan": plan})
        return f"token.{plan}"

    mocker.patch("services.member_service.create_token", side_effect=fake_create_token)
    mocker.patch("services.member_service.hash_pii", return_value="hash-abc")
    mocker.patch("services.member_service.validate_phone", return_value="+15551234567")
    mocker.patch("services.member_service._audit")

    result = register_member(phone="+15551234567")

    assert result["action"] == "login"
    assert result["plan"] == "vip"
    assert len(captured_tokens) == 1
    assert captured_tokens[0]["plan"] == "vip", (
        "create_token deve receber plan='vip' para membro VIP no re-login"
    )


def test_relogin_free_member_token_contains_free_plan(mocker):
    """Free members re-logging stay free."""
    from services.member_service import register_member

    existing = [{"id": "uuid-free", "status": "active", "plan": "free"}]
    mock_sb = _make_sb(existing_data=existing)
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    captured_tokens = []

    def fake_create_token(member_id, plan="free"):
        captured_tokens.append({"plan": plan})
        return f"token.{plan}"

    mocker.patch("services.member_service.create_token", side_effect=fake_create_token)
    mocker.patch("services.member_service.hash_pii", return_value="hash-xyz")
    mocker.patch("services.member_service.validate_phone", return_value="+15559876543")
    mocker.patch("services.member_service._audit")

    result = register_member(phone="+15559876543")

    assert result["action"] == "login"
    assert result["plan"] == "free"
    assert captured_tokens[0]["plan"] == "free"


def test_relogin_banned_member_raises_permission_error(mocker):
    """Banned members cannot re-login."""
    from services.member_service import register_member

    existing = [{"id": "uuid-banned", "status": "banned", "plan": "free"}]
    mock_sb = _make_sb(existing_data=existing)
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.hash_pii", return_value="hash-banned")
    mocker.patch("services.member_service.validate_phone", return_value="+15550000000")

    with pytest.raises(PermissionError):
        register_member(phone="+15550000000")
