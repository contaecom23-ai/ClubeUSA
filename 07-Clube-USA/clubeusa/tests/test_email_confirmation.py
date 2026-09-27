# tests/test_email_confirmation.py — Fase 0.1: email confirmation
import hashlib
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ============================================================
#  request_email_confirmation
# ============================================================

def _mock_sb_for_request(email_enc="enc_email", confirmed_at=None):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":          email_enc,
        "email_confirmed_at": confirmed_at,
    }]
    mock_sb.table().delete().eq().execute.return_value = None
    mock_sb.table().insert().execute.return_value.data = [{"id": "tok-1"}]
    return mock_sb


def test_request_email_confirmation_success(mocker):
    from services.member_service import request_email_confirmation

    mock_sb = _mock_sb_for_request()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")
    mocker.patch("services.member_service._audit")

    raw_token, email = request_email_confirmation("member-123")
    assert len(raw_token) > 20
    assert email == "user@example.com"


def test_request_email_confirmation_no_email(mocker):
    from services.member_service import request_email_confirmation

    mock_sb = _mock_sb_for_request(email_enc=None)
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    with pytest.raises(ValueError, match="email cadastrado"):
        request_email_confirmation("member-123")


def test_request_email_confirmation_already_confirmed(mocker):
    from services.member_service import request_email_confirmation

    mock_sb = _mock_sb_for_request(confirmed_at="2026-01-01T00:00:00")
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    with pytest.raises(ValueError, match="já confirmado"):
        request_email_confirmation("member-123")


def test_request_email_confirmation_member_not_found(mocker):
    from services.member_service import request_email_confirmation

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="Membro não encontrado"):
        request_email_confirmation("ghost-id")


# ============================================================
#  verify_email_token
# ============================================================

def _future(hours=24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()

def _past(hours=1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _make_token():
    import secrets
    raw = secrets.token_urlsafe(32)
    hsh = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hsh


def test_verify_email_token_success(mocker):
    from services.member_service import verify_email_token

    raw, hsh = _make_token()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-1", "member_id": "m-1",
        "expires_at": _future(), "used_at": None,
    }]
    mock_sb.table().update().eq().execute.return_value = None
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    member_id = verify_email_token(raw)
    assert member_id == "m-1"


def test_verify_email_token_invalid(mocker):
    from services.member_service import verify_email_token

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="inválido"):
        verify_email_token("bad-token")


def test_verify_email_token_expired(mocker):
    from services.member_service import verify_email_token

    raw, _ = _make_token()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-1", "member_id": "m-1",
        "expires_at": _past(1), "used_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    with pytest.raises(ValueError, match="expirado"):
        verify_email_token(raw)


def test_verify_email_token_already_used(mocker):
    from services.member_service import verify_email_token

    raw, _ = _make_token()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok-1", "member_id": "m-1",
        "expires_at": _future(), "used_at": _past(1),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="já utilizado"):
        verify_email_token(raw)


# ============================================================
#  get_member_profile — inclui email_confirmed
# ============================================================

def test_profile_includes_email_confirmed_true(mocker):
    from services.member_service import get_member_profile

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m-1", "name_enc": "enc_name", "phone_enc": "enc_phone",
        "email_enc": "enc_email", "email_confirmed_at": "2026-01-01T10:00:00",
        "language": "pt", "state": "FL", "plan": "free", "points": 100,
        "level": "bronze", "categories": ["all"], "referral_code": "ABC12345",
        "referral_count": 0, "total_clicks": 0, "created_at": "2026-01-01T00:00:00",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="test")

    profile = get_member_profile("m-1")
    assert profile["email_confirmed"] is True


def test_profile_includes_email_confirmed_false(mocker):
    from services.member_service import get_member_profile

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m-1", "name_enc": None, "phone_enc": "enc_phone",
        "email_enc": "enc_email", "email_confirmed_at": None,
        "language": "pt", "state": None, "plan": "free", "points": 100,
        "level": "bronze", "categories": ["all"], "referral_code": "XYZ67890",
        "referral_count": 0, "total_clicks": 0, "created_at": "2026-01-01T00:00:00",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="test")

    profile = get_member_profile("m-1")
    assert profile["email_confirmed"] is False


# ============================================================
#  email_service — send_confirmation_email (dev mode)
# ============================================================

def test_send_confirmation_email_dev_returns_true(mocker):
    from services.email_service import send_confirmation_email

    mocker.patch.dict("os.environ", {"ENVIRONMENT": "development"})
    result = send_confirmation_email("test@example.com", "https://example.com/confirm/tok")
    assert result is True


def test_send_confirmation_email_no_provider_returns_false(mocker):
    from services.email_service import send_confirmation_email

    mocker.patch.dict("os.environ", {
        "ENVIRONMENT": "production",
    }, clear=False)
    # Remove provider keys if set
    mocker.patch("os.environ.get", side_effect=lambda k, d=None: {
        "ENVIRONMENT": "production",
    }.get(k, d))

    result = send_confirmation_email("test@example.com", "https://example.com/confirm/tok")
    assert result is False
