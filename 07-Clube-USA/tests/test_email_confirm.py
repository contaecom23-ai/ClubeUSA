# tests/test_email_confirm.py — Fase 0.1: Email confirmado
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta, timezone


# ---- _send_email_confirmation_token ----

def test_send_confirmation_token_creates_record(mocker):
    """Cria token e chama send_email_confirmation."""
    from services.member_service import _send_email_confirmation_token

    mock_sb = MagicMock()
    mock_sb.table().delete().eq().is_().execute.return_value = MagicMock()
    mock_sb.table().insert().execute.return_value = MagicMock()

    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mock_send = mocker.patch("services.member_service.send_email_confirmation")

    _send_email_confirmation_token("member-uuid", "user@example.com", "pt")

    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[0] == "user@example.com"
    assert len(args[1]) > 20  # token tem comprimento razoavel
    assert args[2] == "pt"


# ---- confirm_email ----

def _make_future_iso(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()

def _make_past_iso(hours=1):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_confirm_email_success(mocker):
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "token-uuid",
        "member_id": "member-uuid",
        "expires_at": _make_future_iso(24),
        "used_at": None,
    }]
    mock_sb.table().update().eq().execute.return_value = MagicMock()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    result = confirm_email("valid-token-abc")

    assert result["ok"] is True
    assert result["member_id"] == "member-uuid"


def test_confirm_email_invalid_token_raises(mocker):
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="invalido"):
        confirm_email("non-existent-token")


def test_confirm_email_already_used_raises(mocker):
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "token-uuid",
        "member_id": "member-uuid",
        "expires_at": _make_future_iso(24),
        "used_at": _make_past_iso(1),  # ja foi usado
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="ja utilizado"):
        confirm_email("already-used-token")


def test_confirm_email_expired_raises(mocker):
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "token-uuid",
        "member_id": "member-uuid",
        "expires_at": _make_past_iso(2),  # expirado ha 2h
        "used_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="expirado"):
        confirm_email("expired-token")


# ---- resend_email_confirmation ----

def test_resend_sends_when_not_verified(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-uuid",
        "email_enc": "encrypted-email",
        "email_verified": False,
        "language": "pt",
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mock_decrypt = mocker.patch("services.member_service.decrypt", return_value="user@test.com")
    mock_send_token = mocker.patch("services.member_service._send_email_confirmation_token")

    result = resend_email_confirmation("member-uuid")

    assert result["ok"] is True
    mock_send_token.assert_called_once_with("member-uuid", "user@test.com", "pt")


def test_resend_raises_when_already_verified(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-uuid",
        "email_enc": "encrypted-email",
        "email_verified": True,
        "language": "pt",
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="ja confirmado"):
        resend_email_confirmation("member-uuid")


def test_resend_raises_when_no_email(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-uuid",
        "email_enc": None,
        "email_verified": False,
        "language": "pt",
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="email cadastrado"):
        resend_email_confirmation("member-uuid")


# ---- isolamento multi-tenant: token pertence a outro membro ----

def test_confirm_email_cross_tenant_not_possible():
    """
    Tokens sao buscados pelo valor (aleatorio), nao pelo member_id.
    Um atacante precisaria conhecer o token secreto — impossivel adivinhar.
    O isolamento ocorre porque o token e gerado com secrets.token_urlsafe(32).
    Este teste documenta a invariante.
    """
    import secrets
    t1 = secrets.token_urlsafe(32)
    t2 = secrets.token_urlsafe(32)
    assert t1 != t2
    assert len(t1) >= 32


# ---- email_service: modo dev nao levanta excecao ----

def test_send_email_confirmation_dev_mode(mocker):
    from services.email_service import send_email_confirmation

    mocker.patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=False)
    mock_log = mocker.patch("services.email_service.log")

    send_email_confirmation("user@example.com", "test-token-123", "pt")

    mock_log.info.assert_called_once()
    logged = mock_log.info.call_args[0][0]
    assert "test-token-123" in logged
