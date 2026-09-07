# tests/test_email_confirmation.py — Fase 0.1
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest


# ============================================================
#  generate_confirmation_token
# ============================================================

def test_generate_token_returns_raw_and_hash():
    from services.email_service import generate_confirmation_token
    raw, hashed = generate_confirmation_token()
    assert len(raw) >= 32
    assert hashed == hashlib.sha256(raw.encode()).hexdigest()
    assert raw != hashed


def test_generate_token_unique_each_call():
    from services.email_service import generate_confirmation_token
    raw1, _ = generate_confirmation_token()
    raw2, _ = generate_confirmation_token()
    assert raw1 != raw2


# ============================================================
#  store_confirmation_token
# ============================================================

def test_store_token_deletes_previous_and_inserts(mocker):
    from services.email_service import store_confirmation_token
    mock_sb = MagicMock()
    # delete chain
    mock_sb.table().delete().eq().is_().execute.return_value.data = []
    # insert chain
    mock_sb.table().insert().execute.return_value.data = [{"id": "tok-1"}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    store_confirmation_token("member-uuid", "hash-abc")

    # Verifica que delete foi chamado (invalida tokens anteriores)
    assert mock_sb.table().delete.called


# ============================================================
#  consume_confirmation_token — token valido
# ============================================================

def _make_future(hours=23):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def test_consume_valid_token_returns_member_id(mocker):
    from services.email_service import consume_confirmation_token
    raw = "validrawtoken"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-uuid",
        "member_id": "m-uuid",
        "expires_at": _make_future(23),
        "used_at": None,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    result = consume_confirmation_token(raw)
    assert result == "m-uuid"


def test_consume_returns_none_if_not_found(mocker):
    from services.email_service import consume_confirmation_token
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    assert consume_confirmation_token("nonexistent") is None


def test_consume_returns_none_if_already_used(mocker):
    from services.email_service import consume_confirmation_token
    raw = "usedtoken"
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-uuid",
        "member_id": "m-uuid",
        "expires_at": _make_future(23),
        "used_at": "2026-09-01T10:00:00+00:00",  # ja usado
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    assert consume_confirmation_token(raw) is None


def test_consume_returns_none_if_expired(mocker):
    from services.email_service import consume_confirmation_token
    raw = "expiredtoken"
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-uuid",
        "member_id": "m-uuid",
        "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "used_at": None,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    assert consume_confirmation_token(raw) is None


# ============================================================
#  send_confirmation_email — dev mode
# ============================================================

def test_send_email_dev_mode_returns_true(mocker, monkeypatch):
    from services.email_service import send_confirmation_email
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    mocker.patch("services.email_service.log")  # silencia log

    result = send_confirmation_email("m-id", "user@example.com", "rawtoken123")
    assert result is True


# ============================================================
#  member_service — profile inclui email_confirmed
# ============================================================

def test_profile_includes_email_confirmed_true(mocker):
    from services.member_service import get_member_profile
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m-1",
        "name_enc": "",
        "phone_enc": "enc_phone",
        "email_enc": "enc_email",
        "email_confirmed_at": "2026-09-07T10:00:00+00:00",
        "language": "pt",
        "state": "FL",
        "plan": "free",
        "points": 100,
        "level": "bronze",
        "categories": ["all"],
        "referral_code": "ABC12345",
        "referral_count": 0,
        "total_clicks": 0,
        "created_at": "2026-09-01T00:00:00+00:00",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", side_effect=lambda x: x or "")

    profile = get_member_profile("m-1")
    assert profile["email_confirmed"] is True


def test_profile_includes_email_confirmed_false(mocker):
    from services.member_service import get_member_profile
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m-1",
        "name_enc": "",
        "phone_enc": "enc_phone",
        "email_enc": "enc_email",
        "email_confirmed_at": None,
        "language": "pt",
        "state": "FL",
        "plan": "free",
        "points": 100,
        "level": "bronze",
        "categories": ["all"],
        "referral_code": "ABC12345",
        "referral_count": 0,
        "total_clicks": 0,
        "created_at": "2026-09-01T00:00:00+00:00",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", side_effect=lambda x: x or "")

    profile = get_member_profile("m-1")
    assert profile["email_confirmed"] is False
