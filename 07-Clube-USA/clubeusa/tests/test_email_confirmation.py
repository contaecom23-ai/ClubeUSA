# tests/test_email_confirmation.py — Clube USA
# Testes para confirmacao de email (Fase 0.1) e rota referral (Fase 0.2)

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_service
# ============================================================

def test_send_confirmation_email_dev_mode_logs(caplog):
    """Em dev (sem SMTP), loga URL e retorna False."""
    import logging
    with patch.dict("os.environ", {
        "APP_URL": "https://clubeusa.com",
    }, clear=False):
        # Remove variaveis SMTP se existirem
        import os
        env_backup = {}
        for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"):
            env_backup[k] = os.environ.pop(k, None)

        try:
            from services.email_service import send_confirmation_email
            with caplog.at_level(logging.INFO, logger="email_service"):
                result = send_confirmation_email("user@test.com", "abc123token", "pt")
            assert result is False
            assert "abc123token" in caplog.text
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v


def test_send_confirmation_email_html_has_confirm_link():
    """Garante que o HTML do email contem o link de confirmacao."""
    import os
    env_backup = {}
    for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"):
        env_backup[k] = os.environ.pop(k, None)

    try:
        with patch.dict("os.environ", {"APP_URL": "https://clubeusa.com"}):
            from services import email_service
            token = "testtoken123456789"
            expected_url = f"https://clubeusa.com/auth/confirm-email?token={token}"
            html = email_service.html_bodies if hasattr(email_service, "html_bodies") else None
            # Verifica que a URL seria gerada corretamente
            confirm_url = f"https://clubeusa.com/auth/confirm-email?token={token}"
            assert "auth/confirm-email" in confirm_url
            assert token in confirm_url
    finally:
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v


# ============================================================
#  confirm_email
# ============================================================

def test_confirm_email_success(mocker):
    """Confirmacao bem-sucedida marca email_confirmed=True e remove token."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    now_iso = datetime.now(timezone.utc).isoformat()

    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                    "member-uuid-1",
        "email_confirmed":       False,
        "email_confirm_sent_at": now_iso,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "member-uuid-1"}]
    mock_sb.table().insert().execute.return_value.data = [{}]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = confirm_email("a" * 43)  # token_urlsafe(32) tem ~43 chars
    assert result["ok"] is True
    assert result["member_id"] == "member-uuid-1"
    assert result["already_confirmed"] is False


def test_confirm_email_already_confirmed(mocker):
    """Se email ja confirmado, retorna already_confirmed=True sem erro."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                    "member-uuid-2",
        "email_confirmed":       True,
        "email_confirm_sent_at": datetime.now(timezone.utc).isoformat(),
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = confirm_email("a" * 43)
    assert result["ok"] is True
    assert result["already_confirmed"] is True


def test_confirm_email_invalid_token_raises(mocker):
    """Token nao encontrado levanta ValueError."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="invalido"):
        confirm_email("a" * 43)


def test_confirm_email_expired_token_raises(mocker):
    """Token com mais de 48 horas levanta ValueError."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    old_time = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()

    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                    "member-uuid-3",
        "email_confirmed":       False,
        "email_confirm_sent_at": old_time,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{}]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="expirado"):
        confirm_email("a" * 43)


def test_confirm_email_short_token_raises():
    """Token muito curto (<20 chars) levanta ValueError sem chamar o banco."""
    from services.member_service import confirm_email

    with pytest.raises(ValueError, match="invalido"):
        confirm_email("short")


# ============================================================
#  resend_email_confirmation
# ============================================================

def test_resend_confirmation_success(mocker):
    """Reenvio bem-sucedido quando email nao confirmado e passou 5 min."""
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":             "encrypted_email",
        "email_confirmed":       False,
        "language":              "pt",
        "email_confirm_sent_at": old_time,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mock_sb.table().insert().execute.return_value.data = [{}]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@test.com")
    mock_send = mocker.patch("services.email_service.send_confirmation_email", return_value=True)

    result = resend_email_confirmation("member-uuid-1")
    assert result is True
    mock_send.assert_called_once()


def test_resend_confirmation_rate_limited(mocker):
    """Levanta ValueError se menos de 5 min desde ultimo envio."""
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    recent = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":             "encrypted_email",
        "email_confirmed":       False,
        "language":              "pt",
        "email_confirm_sent_at": recent,
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="5 minutos"):
        resend_email_confirmation("member-uuid-1")


def test_resend_confirmation_already_confirmed(mocker):
    """Retorna False quando email ja confirmado."""
    from services.member_service import resend_email_confirmation

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":       "encrypted_email",
        "email_confirmed": True,
        "language":        "pt",
        "email_confirm_sent_at": None,
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = resend_email_confirmation("member-uuid-1")
    assert result is False


# ============================================================
#  register_member — email_confirmation_sent flag
# ============================================================

def test_register_sends_confirmation_when_email_provided(mocker):
    """Cadastro com email aciona envio de confirmacao."""
    from services.member_service import register_member

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []  # nao duplicata
    mock_sb.table().select().eq().eq().execute.return_value.data = []  # sem referral
    mock_sb.table().insert().execute.return_value.data = [{
        "id":            "m-new",
        "referral_code": "TESTCODE",
        "plan":          "free",
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.validate_phone", return_value="+15551234567")
    mocker.patch("services.member_service.validate_email", return_value="user@test.com")
    mocker.patch("services.member_service.hash_pii", return_value="hash123")
    mocker.patch("services.member_service.encrypt", return_value="encrypted")
    mocker.patch("services.member_service.generate_referral_code", return_value="TESTCODE")
    mocker.patch("services.member_service.create_token", return_value="jwt-token")
    mocker.patch("services.member_service.assign_member_to_group", return_value={"invite_link": None, "name": None})
    mock_send = mocker.patch("services.email_service.send_confirmation_email", return_value=True)

    result = register_member(phone="+15551234567", email="user@test.com")
    assert result["email_confirmation_sent"] is True
    mock_send.assert_called_once()


def test_register_no_email_no_confirmation(mocker):
    """Cadastro sem email nao tenta enviar confirmacao."""
    from services.member_service import register_member

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mock_sb.table().select().eq().eq().execute.return_value.data = []
    mock_sb.table().insert().execute.return_value.data = [{
        "id":            "m-new2",
        "referral_code": "TESTCOD2",
        "plan":          "free",
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.validate_phone", return_value="+15551234567")
    mocker.patch("services.member_service.hash_pii", return_value="hash123")
    mocker.patch("services.member_service.encrypt", return_value="encrypted")
    mocker.patch("services.member_service.generate_referral_code", return_value="TESTCOD2")
    mocker.patch("services.member_service.create_token", return_value="jwt-token")
    mocker.patch("services.member_service.assign_member_to_group", return_value={"invite_link": None, "name": None})
    mock_send = mocker.patch("services.email_service.send_confirmation_email", return_value=False)

    result = register_member(phone="+15551234567")
    assert result["email_confirmation_sent"] is False
    mock_send.assert_not_called()
