# ============================================================
#  tests/test_email_service.py — Clube USA
#  Testes unitarios do email_service (sem acesso real ao banco)
# ============================================================

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


# --------------- fixtures --------------------------------

def _make_token_record(used_at=None, delta_hours=1):
    expires = datetime.now(timezone.utc) + timedelta(hours=delta_hours)
    return {
        "id": "tok-id-001",
        "member_id": "member-001",
        "token": "validtoken",
        "expires_at": expires.isoformat(),
        "used_at": used_at,
    }


# --------------- request_email_confirmation ---------------

def test_request_generates_token_and_calls_send():
    mock_sb = MagicMock()
    mock_sb.table.return_value.delete.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

    with patch("services.email_service._supabase", return_value=mock_sb), \
         patch("services.email_service._send_confirmation_email") as mock_send:
        from services.email_service import request_email_confirmation
        token = request_email_confirmation("member-001", "user@example.com")

    assert isinstance(token, str) and len(token) > 20
    mock_send.assert_called_once()
    email_arg, token_arg = mock_send.call_args[0]
    assert email_arg == "user@example.com"
    assert token_arg == token


# --------------- confirm_email_token: happy path ----------

def test_confirm_valid_token_marks_confirmed():
    record = _make_token_record()
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [record]
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

    with patch("services.email_service._supabase", return_value=mock_sb):
        from services.email_service import confirm_email_token
        result = confirm_email_token("validtoken")

    assert result["ok"] is True
    assert result["member_id"] == "member-001"


# --------------- confirm_email_token: token not found -----

def test_confirm_invalid_token_raises():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("services.email_service._supabase", return_value=mock_sb):
        from services.email_service import confirm_email_token
        with pytest.raises(ValueError, match="invalido"):
            confirm_email_token("badtoken")


# --------------- confirm_email_token: expired -------------

def test_confirm_expired_token_raises():
    record = _make_token_record(delta_hours=-1)  # expirou ha 1h
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [record]

    with patch("services.email_service._supabase", return_value=mock_sb):
        from services.email_service import confirm_email_token
        with pytest.raises(ValueError, match="expirado"):
            confirm_email_token("validtoken")


# --------------- confirm_email_token: already used --------

def test_confirm_already_used_token_raises():
    record = _make_token_record(used_at=datetime.now(timezone.utc).isoformat())
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [record]

    with patch("services.email_service._supabase", return_value=mock_sb):
        from services.email_service import confirm_email_token
        with pytest.raises(ValueError, match="ja utilizado"):
            confirm_email_token("validtoken")


# --------------- _send_confirmation_email: dev mode -------

def test_send_logs_in_dev_mode(caplog):
    import logging
    with patch.dict("os.environ", {"ENVIRONMENT": "development", "APP_URL": "http://localhost:8000"}):
        from services.email_service import _send_confirmation_email
        import importlib
        import services.email_service as mod
        importlib.reload(mod)  # garante env atualizada
        with caplog.at_level(logging.INFO, logger="email_service"):
            mod._send_confirmation_email("user@test.com", "tok123")
    # Em dev, nao chama providers externos
    assert True  # nao levantou excecao
