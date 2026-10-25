# tests/test_email_confirm.py — FASE 0.1: confirmação de email
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def _mock_sb():
    return MagicMock()


def _token_pair():
    """Gera um par (raw_token, token_hash) para uso nos testes."""
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


# ================================================================
#  confirm_email
# ================================================================

def test_confirm_email_success(mocker):
    from services.member_service import confirm_email
    raw, tok_hash = _token_pair()
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                   "m1",
        "email_confirmed":      False,
        "email_verify_expires": expires,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    result = confirm_email(raw)
    assert result["confirmed"] is True
    assert result["member_id"] == "m1"
    assert result["already_confirmed"] is False


def test_confirm_email_already_confirmed(mocker):
    from services.member_service import confirm_email
    raw, tok_hash = _token_pair()
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                   "m1",
        "email_confirmed":      True,
        "email_verify_expires": expires,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    result = confirm_email(raw)
    assert result["confirmed"] is True
    assert result["already_confirmed"] is True


def test_confirm_email_token_not_found(mocker):
    import pytest
    from services.member_service import confirm_email
    raw, _ = _token_pair()

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="inválido ou expirado"):
        confirm_email(raw)


def test_confirm_email_expired(mocker):
    import pytest
    from services.member_service import confirm_email
    raw, _ = _token_pair()
    expired = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                   "m1",
        "email_confirmed":      False,
        "email_verify_expires": expired,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="expirado"):
        confirm_email(raw)


def test_confirm_email_empty_token_raises(mocker):
    import pytest
    from services.member_service import confirm_email
    mocker.patch("services.member_service._supabase", return_value=_mock_sb())

    with pytest.raises(ValueError, match="inválido"):
        confirm_email("")


def test_confirm_email_too_long_raises(mocker):
    import pytest
    from services.member_service import confirm_email
    mocker.patch("services.member_service._supabase", return_value=_mock_sb())

    with pytest.raises(ValueError, match="inválido"):
        confirm_email("x" * 200)


# ================================================================
#  resend_email_confirmation
# ================================================================

def test_resend_success(mocker):
    from services.member_service import resend_email_confirmation
    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":              "m1",
        "email_enc":       "encrypted",
        "email_confirmed": False,
        "name_enc":        "encrypted_name",
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("utils.security.check_rate_limit", return_value=True)
    mocker.patch("services.member_service.decrypt", return_value="valor")
    mocker.patch("services.email_service.send_confirmation_email")
    mocker.patch("services.member_service._audit")

    # Não deve levantar exceção
    resend_email_confirmation("m1")


def test_resend_already_confirmed_raises(mocker):
    import pytest
    from services.member_service import resend_email_confirmation
    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":              "m1",
        "email_enc":       "encrypted",
        "email_confirmed": True,
        "name_enc":        None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("utils.security.check_rate_limit", return_value=True)

    with pytest.raises(ValueError, match="já confirmado"):
        resend_email_confirmation("m1")


def test_resend_no_email_raises(mocker):
    import pytest
    from services.member_service import resend_email_confirmation
    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":              "m1",
        "email_enc":       None,
        "email_confirmed": False,
        "name_enc":        None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("utils.security.check_rate_limit", return_value=True)

    with pytest.raises(ValueError, match="Nenhum email"):
        resend_email_confirmation("m1")


def test_resend_rate_limited_raises(mocker):
    import pytest
    from services.member_service import resend_email_confirmation
    mocker.patch("services.member_service._supabase", return_value=_mock_sb())
    mocker.patch("utils.security.check_rate_limit", return_value=False)

    with pytest.raises(ValueError, match="Muitas tentativas"):
        resend_email_confirmation("m1")


# ================================================================
#  email_service — envio em dev mode (sem chave)
# ================================================================

def test_email_service_dev_mode_logs(caplog, monkeypatch):
    """Em dev (sem RESEND_API_KEY), deve logar em vez de enviar."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("APP_URL", "https://clubeusa.com")

    from services.email_service import send_confirmation_email
    import logging

    with caplog.at_level(logging.INFO, logger="email_service"):
        send_confirmation_email("user@example.com", "João", "abc123token")

    assert any("DEV" in r.message or "abc123token" in r.message for r in caplog.records)


def test_email_service_confirm_url_contains_token(monkeypatch):
    """A URL de confirmação deve conter o token raw."""
    monkeypatch.setenv("APP_URL", "https://clubeusa.com")

    from services import email_service
    html = email_service._html_confirm_email("João", "https://clubeusa.com/verify-email?token=TOKEN123")
    assert "TOKEN123" in html
    assert "verify-email" in html


# ================================================================
#  register_member — campo email_confirmed setado ao criar
# ================================================================

def test_register_sets_email_confirmed_false(mocker):
    """Membro criado com email tem email_confirmed=False."""
    import os
    os.environ.setdefault("ENCRYPTION_KEY", "testkey1234567890")
    os.environ.setdefault("JWT_SECRET", "testsecret")

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = []  # nao existe
    mock_sb.table().insert().execute.return_value.data = [{
        "id": "new1", "plan": "free", "referral_code": "ABC12345",
        "email_confirmed": False,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.assign_member_to_group", return_value=None)
    mocker.patch("services.member_service._audit")
    mocker.patch("services.email_service.send_confirmation_email")

    from services.member_service import register_member
    result = register_member(phone="+15551234567", email="test@example.com", name="Test")

    assert result["action"] == "registered"
    assert result["email_confirmation_sent"] is True

    # Verifica que o insert incluiu email_confirmed=False e token
    call_args = mock_sb.table().insert.call_args
    inserted = call_args[0][0]
    assert inserted.get("email_confirmed") is False
    assert inserted.get("email_verify_token") is not None
