# tests/test_email_confirmation.py — Fase 0.1 confirmação de email
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_sender — unit tests (sem envio real)
# ============================================================

def test_email_sender_dev_mode_logs(caplog):
    """Em modo dev (não production) deve logar e NÃO enviar."""
    import logging
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        import importlib
        import utils.email_sender as mod
        importlib.reload(mod)
        with caplog.at_level(logging.INFO, logger="email_sender"):
            mod.send_email_otp("test@example.com", "123456", "Ana")
        assert "123456" in caplog.text
        assert "test@example.com" in caplog.text


def test_email_sender_production_no_credentials_raises():
    """Em production sem credenciais deve levantar EnvironmentError."""
    env_override = {
        "ENVIRONMENT":      "production",
        "SENDGRID_API_KEY": "",
        "SMTP_HOST":        "",
    }
    import importlib
    import utils.email_sender as mod
    with patch.dict(os.environ, env_override, clear=False):
        importlib.reload(mod)
        with pytest.raises(EnvironmentError):
            mod.send_email_otp("test@example.com", "123456")


def test_email_html_contains_otp():
    import importlib
    import utils.email_sender as mod
    importlib.reload(mod)
    html = mod._html_otp("654321", "João")
    assert "654321" in html
    assert "João" in html


def test_email_text_contains_otp():
    import importlib
    import utils.email_sender as mod
    importlib.reload(mod)
    text = mod._text_otp("987654")
    assert "987654" in text


# ============================================================
#  email_confirmation_service — unit tests
# ============================================================

def _mock_sb_with_record(record):
    """Helper: Supabase mock que retorna um record em email_tokens."""
    mock = MagicMock()
    mock.table().select().eq().execute.return_value.data = [record]
    mock.table().delete().eq().execute.return_value = MagicMock()
    mock.table().update().eq().execute.return_value = MagicMock()
    mock.table().insert().execute.return_value = MagicMock()
    return mock


def test_verify_email_token_valid(mocker):
    from services.email_confirmation_service import verify_email_token
    record = {
        "email_hash": "abc", "token": "111111", "attempts": 0,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    mocker.patch("services.email_confirmation_service._supabase",
                 return_value=_mock_sb_with_record(record))
    ok, msg = verify_email_token("abc", "111111")
    assert ok is True
    assert msg == ""


def test_verify_email_token_wrong_code(mocker):
    from services.email_confirmation_service import verify_email_token
    record = {
        "email_hash": "abc", "token": "111111", "attempts": 0,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    mocker.patch("services.email_confirmation_service._supabase",
                 return_value=_mock_sb_with_record(record))
    ok, msg = verify_email_token("abc", "000000")
    assert ok is False
    assert "incorreto" in msg.lower()


def test_verify_email_token_expired(mocker):
    from services.email_confirmation_service import verify_email_token
    record = {
        "email_hash": "abc", "token": "111111", "attempts": 0,
        "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    }
    mocker.patch("services.email_confirmation_service._supabase",
                 return_value=_mock_sb_with_record(record))
    ok, msg = verify_email_token("abc", "111111")
    assert ok is False
    assert "expirado" in msg.lower()


def test_verify_email_token_too_many_attempts(mocker):
    from services.email_confirmation_service import verify_email_token
    record = {
        "email_hash": "abc", "token": "111111", "attempts": 5,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    mocker.patch("services.email_confirmation_service._supabase",
                 return_value=_mock_sb_with_record(record))
    ok, msg = verify_email_token("abc", "111111")
    assert ok is False
    assert "tentativas" in msg.lower()


def test_verify_email_token_not_found(mocker):
    from services.email_confirmation_service import verify_email_token
    mock = MagicMock()
    mock.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_confirmation_service._supabase", return_value=mock)
    ok, msg = verify_email_token("nonexistent", "111111")
    assert ok is False
    assert "invalido" in msg.lower()


def test_verify_email_token_single_use(mocker):
    """Token deve ser deletado após verificação bem-sucedida."""
    from services.email_confirmation_service import verify_email_token
    record = {
        "email_hash": "abc", "token": "222222", "attempts": 0,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    mock = _mock_sb_with_record(record)
    mocker.patch("services.email_confirmation_service._supabase", return_value=mock)
    ok, _ = verify_email_token("abc", "222222")
    assert ok is True
    # Verifica que delete foi chamado após sucesso
    mock.table().delete().eq().execute.assert_called()


# ============================================================
#  Multi-tenant: token de outro membro não confirma membro errado
# ============================================================

def test_email_confirmation_isolation(mocker):
    """
    O endpoint usa member_id do JWT para buscar email_hash (servidor),
    nunca aceita email_hash de outro membro via body.
    Este teste verifica que verify_email_token com hash inexistente retorna False.
    """
    from services.email_confirmation_service import verify_email_token
    mock = MagicMock()
    mock.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_confirmation_service._supabase", return_value=mock)
    ok, msg = verify_email_token("hash_membro_b", "999999")
    assert ok is False


def test_set_email_confirmed_calls_update_and_audit(mocker):
    """set_email_confirmed deve atualizar members e inserir audit_log."""
    from services.email_confirmation_service import set_email_confirmed
    mock = MagicMock()
    mocker.patch("services.email_confirmation_service._supabase", return_value=mock)
    set_email_confirmed("member-uuid-123")
    mock.table().update().eq().execute.assert_called()
    mock.table().insert().execute.assert_called()
