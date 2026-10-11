# tests/test_email_confirmation.py — Fase 0.1: confirmação de email
#
# Nota: utils.security usa cryptography (Fernet) que tem conflito de versão no
# ambiente de CI desta sandbox. Resolvido pré-mockando o módulo no nível do sys.
import hashlib
import secrets
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────
#  Pré-mock de utils.security para isolar do cryptography bug
# ─────────────────────────────────────────────────────────────

def _make_security_mock():
    m = MagicMock()
    m.encrypt = lambda x: f"ENC:{x}" if x else ""
    m.decrypt = lambda x: x.replace("ENC:", "") if x else ""
    m.hash_pii = lambda x: hashlib.sha256(x.encode()).hexdigest()
    m.hash_ip  = lambda x: "hashed_ip"
    m.validate_phone = lambda x: x
    m.validate_email = lambda x: x.strip().lower()
    m.sanitize = lambda x, *a: x[:80] if x else ""
    m.generate_referral_code = lambda: "TESTCODE"
    m.generate_utm = lambda a, b: "utm_test"
    m.create_token = lambda *a, **kw: "fake.jwt.token"
    m.verify_token = lambda t: {"sub": "mem-test", "plan": "free"} if t else None
    return m

# Injeta antes de qualquer import do módulo
sys.modules.setdefault("utils.security", _make_security_mock())
# Também garante que supabase não seja necessário no ambiente de CI
sys.modules.setdefault("supabase", MagicMock())
sys.modules.setdefault("services.group_manager", MagicMock())


# ─────────────────────────────────────────────────────────────
#  email_sender.py
# ─────────────────────────────────────────────────────────────

def test_send_email_dev_mode_logs_and_returns_true(caplog):
    """Sem chaves de email configuradas deve logar o link e retornar True."""
    import logging
    from utils.email_sender import send_email_confirmation

    os.environ.pop("RESEND_API_KEY", None)
    os.environ.pop("SENDGRID_API_KEY", None)

    with caplog.at_level(logging.INFO, logger="email_sender"):
        result = send_email_confirmation(
            "test@example.com",
            "https://clubeusa.com/confirm?token=abc",
            "João",
        )

    assert result is True
    assert "https://clubeusa.com/confirm?token=abc" in caplog.text


def test_send_email_resend_success(mocker):
    """Chama Resend quando RESEND_API_KEY está definida."""
    mock_send = mocker.patch("utils.email_sender._send_resend", return_value=True)
    os.environ.pop("SENDGRID_API_KEY", None)

    with patch.dict(os.environ, {"RESEND_API_KEY": "re_fake_key"}):
        from utils.email_sender import send_email_confirmation
        result = send_email_confirmation("user@example.com", "https://x.com/confirm?token=xyz")

    assert result is True
    mock_send.assert_called_once()


def test_send_email_sendgrid_fallback(mocker):
    """Usa SendGrid quando só SENDGRID_API_KEY está definida."""
    mock_send = mocker.patch("utils.email_sender._send_sendgrid", return_value=True)
    os.environ.pop("RESEND_API_KEY", None)

    with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}):
        from utils.email_sender import send_email_confirmation
        result = send_email_confirmation("user@example.com", "https://x.com/confirm?token=xyz")

    assert result is True
    mock_send.assert_called_once()


# ─────────────────────────────────────────────────────────────
#  member_service.send_email_confirmation_for_member
# ─────────────────────────────────────────────────────────────

def _make_sb():
    sb = MagicMock()
    sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{}]
    return sb


def test_send_confirmation_generates_token_and_calls_sender(mocker):
    sb = _make_sb()
    mocker.patch("services.member_service._supabase", return_value=sb)
    mock_send = mocker.patch("utils.email_sender.send_email_confirmation", return_value=True)

    with patch.dict(os.environ, {"APP_URL": "https://clubeusa.com"}):
        from services.member_service import send_email_confirmation_for_member
        result = send_email_confirmation_for_member("member-uuid", "test@example.com")

    assert result is True
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0]
    assert call_args[0] == "test@example.com"
    confirm_url = call_args[1]
    assert "clubeusa.com/auth/email/confirm?token=" in confirm_url
    raw_token = confirm_url.split("token=")[1]
    assert len(raw_token) > 20  # token URL-safe 32 bytes → ~43 chars


# ─────────────────────────────────────────────────────────────
#  member_service.confirm_member_email
# ─────────────────────────────────────────────────────────────

def test_confirm_email_valid_token():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "token_hash": token_hash,
        "member_id":  "mem-1",
        "expires_at": future,
        "used_at":    None,
    }]
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("services.member_service._supabase", return_value=sb), \
         patch("services.member_service._audit"):
        from services.member_service import confirm_member_email
        result = confirm_member_email(raw_token)

    assert result["confirmed"] is True
    assert result["member_id"] == "mem-1"


def test_confirm_email_invalid_token_raises():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import confirm_member_email
        with pytest.raises(ValueError, match="inválido"):
            confirm_member_email("token-nao-existe")


def test_confirm_email_expired_token_raises():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "token_hash": token_hash,
        "member_id":  "mem-2",
        "expires_at": past,
        "used_at":    None,
    }]
    sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import confirm_member_email
        with pytest.raises(ValueError, match="expirado"):
            confirm_member_email(raw_token)


def test_confirm_email_already_used_raises():
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    future = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "token_hash": token_hash,
        "member_id":  "mem-3",
        "expires_at": future,
        "used_at":    "2026-09-20T10:00:00",
    }]

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import confirm_member_email
        with pytest.raises(ValueError, match="já utilizado"):
            confirm_member_email(raw_token)


def test_confirm_email_empty_token_raises():
    with patch("services.member_service._supabase", return_value=MagicMock()):
        from services.member_service import confirm_member_email
        with pytest.raises(ValueError):
            confirm_member_email("")


# ─────────────────────────────────────────────────────────────
#  member_service.resend_email_confirmation
# ─────────────────────────────────────────────────────────────

def test_resend_blocks_if_token_recent():
    """Token criado há 30 min → deve bloquear reenvio."""
    recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"created_at": recent}
    ]

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import resend_email_confirmation
        with pytest.raises(ValueError, match="Aguarde"):
            resend_email_confirmation("mem-4")


def test_resend_raises_if_email_already_confirmed():
    """Email já confirmado → deve rejeitar reenvio."""
    sb = MagicMock()
    # Nenhum token recente
    no_tokens = MagicMock()
    no_tokens.data = []
    # Perfil com email_confirmed_at preenchido
    confirmed_profile = MagicMock()
    confirmed_profile.data = [{"email_enc": "ENC:test@example.com", "email_confirmed_at": "2026-09-20"}]

    sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        no_tokens,
        confirmed_profile,
    ]

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import resend_email_confirmation
        with pytest.raises(ValueError, match="já confirmado"):
            resend_email_confirmation("mem-5")


# ─────────────────────────────────────────────────────────────
#  get_member_profile retorna email_confirmed
# ─────────────────────────────────────────────────────────────

def test_profile_includes_email_confirmed_false():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "m-1", "name_enc": None, "phone_enc": "ENC:+15551234567",
        "email_enc": None, "email_confirmed_at": None,
        "language": "pt", "state": "FL", "plan": "free",
        "points": 100, "level": "bronze", "categories": ["all"],
        "referral_code": "ABC12345", "referral_count": 0,
        "total_clicks": 0, "created_at": "2026-09-20T00:00:00",
        "vip_expires_at": None,
    }]

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import get_member_profile
        profile = get_member_profile("m-1")

    assert profile["email_confirmed"] is False


def test_profile_includes_email_confirmed_true():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "m-1", "name_enc": None, "phone_enc": "ENC:+15551234567",
        "email_enc": None, "email_confirmed_at": "2026-09-20T12:00:00",
        "language": "pt", "state": "FL", "plan": "free",
        "points": 100, "level": "bronze", "categories": ["all"],
        "referral_code": "ABC12345", "referral_count": 0,
        "total_clicks": 0, "created_at": "2026-09-20T00:00:00",
        "vip_expires_at": None,
    }]

    with patch("services.member_service._supabase", return_value=sb):
        from services.member_service import get_member_profile
        profile = get_member_profile("m-1")

    assert profile["email_confirmed"] is True
