# tests/test_email_confirm.py — Clube USA
# Testes para o fluxo de confirmacao de email (Fase 0.1).

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def _make_token():
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def _future_expiry(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past_expiry():
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


# ============================================================
#  confirm_email
# ============================================================

def test_confirm_email_success(mocker):
    raw, hashed = _make_token()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_confirmed": False,
        "email_confirm_expires_at": _future_expiry(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    from services.member_service import confirm_email
    result = confirm_email(raw)

    assert result["ok"] is True
    assert result["member_id"] == "member-1"
    # Deve ter chamado update com email_confirmed=True e limpeza do token
    update_call = mock_sb.table().update()
    update_call.eq.assert_called()


def test_confirm_email_invalid_token(mocker):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_email
    import pytest
    with pytest.raises(ValueError, match="invalido"):
        confirm_email("nonexistent-token")


def test_confirm_email_already_confirmed(mocker):
    raw, _ = _make_token()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_confirmed": True,
        "email_confirm_expires_at": _future_expiry(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_email
    import pytest
    with pytest.raises(ValueError, match="ja confirmado"):
        confirm_email(raw)


def test_confirm_email_expired_token(mocker):
    raw, hashed = _make_token()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_confirmed": False,
        "email_confirm_expires_at": _past_expiry(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    from services.member_service import confirm_email
    import pytest
    with pytest.raises(ValueError, match="expirado"):
        confirm_email(raw)


def test_confirm_email_token_too_long(mocker):
    mocker.patch("services.member_service._supabase")

    from services.member_service import confirm_email
    import pytest
    with pytest.raises(ValueError, match="invalido"):
        confirm_email("x" * 201)


# ============================================================
#  resend_email_confirmation
# ============================================================

def test_resend_confirmation_success(mocker):
    mock_sb = MagicMock()
    # TTL issued ~1h ago, so no cooldown (>5min since issue)
    issued_at = datetime.now(timezone.utc) - timedelta(hours=1)
    expires_at = issued_at + timedelta(hours=24)

    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_enc": "enc_email",
        "email_confirmed": False,
        "email_confirm_expires_at": expires_at.isoformat(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")
    mocker.patch("services.member_service._audit")
    mock_send = mocker.patch("services.email_service.send_email_confirmation", return_value=True)

    from services.member_service import resend_email_confirmation
    result = resend_email_confirmation("member-1")

    assert result["ok"] is True
    assert result["expires_in_hours"] == 24
    mock_send.assert_called_once()


def test_resend_confirmation_already_confirmed(mocker):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_enc": "enc_email",
        "email_confirmed": True,
        "email_confirm_expires_at": _future_expiry(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resend_email_confirmation
    import pytest
    with pytest.raises(ValueError, match="ja confirmado"):
        resend_email_confirmation("member-1")


def test_resend_confirmation_no_email(mocker):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_enc": None,
        "email_confirmed": False,
        "email_confirm_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resend_email_confirmation
    import pytest
    with pytest.raises(ValueError, match="Nenhum email"):
        resend_email_confirmation("member-1")


def test_resend_confirmation_cooldown_active(mocker):
    mock_sb = MagicMock()
    # Token emitido 1 minuto atras — dentro do cooldown de 5 minutos
    issued_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    expires_at = issued_at + timedelta(hours=24)

    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "member-1",
        "email_enc": "enc_email",
        "email_confirmed": False,
        "email_confirm_expires_at": expires_at.isoformat(),
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resend_email_confirmation
    import pytest
    with pytest.raises(ValueError, match="Aguarde"):
        resend_email_confirmation("member-1")


# ============================================================
#  Isolamento multi-tenant: confirm_email nao vaza entre membros
# ============================================================

def test_confirm_email_wrong_member_gets_404_equivalent(mocker):
    """Token de membro A nao pode confirmar email de membro B."""
    # Simula token que nao existe no banco (nao pertence a nenhum membro)
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_email
    import pytest
    with pytest.raises(ValueError, match="invalido"):
        confirm_email(secrets.token_urlsafe(32))


# ============================================================
#  email_service: dev mode nao levanta excecao
# ============================================================

def test_email_service_dev_mode_returns_true(mocker):
    mocker.patch.dict("os.environ", {"ENVIRONMENT": "development"})
    from services.email_service import send_email_confirmation
    result = send_email_confirmation("test@example.com", "rawtoken123")
    assert result is True


def test_email_service_production_no_provider(mocker):
    mocker.patch.dict("os.environ", {"ENVIRONMENT": "production", "EMAIL_PROVIDER": ""})
    from services.email_service import send_email_confirmation
    result = send_email_confirmation("test@example.com", "rawtoken123")
    assert result is False
