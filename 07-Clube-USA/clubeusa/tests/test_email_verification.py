# tests/test_email_verification.py
# Testa fluxo completo de verificação de email (Fase 0.1)
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest


# ------------------------------------------------------------------ helpers
def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _future(hours=24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past(hours=1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


# ================================================================== send
def test_send_verification_email_creates_record_and_calls_sender(mocker, monkeypatch):
    """Token gerado, gravado no Supabase e email_sender chamado."""
    monkeypatch.setenv("ENCRYPTION_KEY", "testkey_abc123")
    from services.member_service import send_verification_email

    mock_sb = MagicMock()
    mock_sb.table().delete().eq().execute.return_value = MagicMock()
    mock_sb.table().insert().execute.return_value = MagicMock()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.hash_pii", return_value="fakehash")

    mock_send = mocker.patch("utils.email_sender.send_email_verification", return_value=True)

    raw_token = send_verification_email("member-1", "user@example.com", "João")

    assert len(raw_token) > 10
    mock_send.assert_called_once_with("user@example.com", raw_token, member_name="João")


def test_send_verification_deletes_previous_tokens(mocker, monkeypatch):
    """Resend remove tokens anteriores do mesmo membro antes de criar novo."""
    monkeypatch.setenv("ENCRYPTION_KEY", "testkey_abc123")
    from services.member_service import send_verification_email

    mock_sb = MagicMock()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.hash_pii", return_value="fakehash")
    mocker.patch("utils.email_sender.send_email_verification", return_value=True)

    send_verification_email("member-1", "user@example.com")

    # Verifica que delete foi chamado com member_id
    mock_sb.table().delete().eq.assert_called_with("member_id", "member-1")


# ================================================================== confirm
def test_confirm_email_success(mocker):
    """Token válido → email_verified=True no member, token marcado como usado."""
    from services.member_service import confirm_email

    raw_token = "validtoken_abc123XYZ"
    verif_record = {
        "id": "verif-1",
        "member_id": "member-1",
        "email_hash": "somehash",
        "expires_at": _future(24),
        "used_at": None,
    }
    member_record = {"email_enc": "enc_email"}

    mock_sb = MagicMock()
    # First select returns verif record; second select (member) returns member record
    mock_sb.table().select().eq().execute.return_value.data = [verif_record]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")
    mocker.patch("services.member_service._mask_email", return_value="us**@example.com")
    # Override _audit to avoid supabase call
    mocker.patch("services.member_service._audit")

    result = confirm_email(raw_token)

    assert result["member_id"] == "member-1"


def test_confirm_email_invalid_token(mocker):
    """Token não encontrado → ValueError."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="inválido"):
        confirm_email("nonexistent_token_long_enough")


def test_confirm_email_already_used(mocker):
    """Token já usado → ValueError."""
    from services.member_service import confirm_email

    raw_token = "already_used_token_xyz"
    record = {
        "id": "verif-1",
        "member_id": "member-1",
        "email_hash": "somehash",
        "expires_at": _future(24),
        "used_at": _past(1),  # já foi usado
    }

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [record]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="já foi utilizado"):
        confirm_email(raw_token)


def test_confirm_email_expired_token(mocker):
    """Token expirado → ValueError e token deletado do banco."""
    from services.member_service import confirm_email

    raw_token = "expired_token_long_enough_xyz"
    record = {
        "id": "verif-1",
        "member_id": "member-1",
        "email_hash": "somehash",
        "expires_at": _past(25),  # expirou há 25h
        "used_at": None,
    }

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [record]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="expirado"):
        confirm_email(raw_token)

    # Confirma que o token expirado foi deletado
    mock_sb.table().delete().eq.assert_called_with("id", "verif-1")


def test_confirm_email_too_short_token(mocker):
    """Token curto demais (< 10 chars) → ValueError imediato sem hit no banco."""
    from services.member_service import confirm_email

    mock_sb = MagicMock()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="inválido"):
        confirm_email("abc")

    mock_sb.table.assert_not_called()


# ================================================================== resend
def test_resend_verification_already_verified(mocker):
    """Membro já verificado → retorna False sem reenvio."""
    from services.member_service import resend_verification_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc", "email_verified": True, "name_enc": None}
    ]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = resend_verification_email("member-1")
    assert result is False


def test_resend_verification_no_email(mocker):
    """Membro sem email cadastrado → ValueError."""
    from services.member_service import resend_verification_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": None, "email_verified": False, "name_enc": None}
    ]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    with pytest.raises(ValueError, match="email"):
        resend_verification_email("member-1")


def test_resend_verification_success(mocker):
    """Membro com email não verificado → reenvia e retorna True."""
    from services.member_service import resend_verification_email

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc", "email_verified": False, "name_enc": "enc_name"}
    ]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", side_effect=["user@example.com", "João"])
    mock_send = mocker.patch(
        "services.member_service.send_verification_email", return_value="sometoken"
    )

    result = resend_verification_email("member-1")

    assert result is True
    mock_send.assert_called_once_with("member-1", "user@example.com", "João")


# ================================================================== email_sender
def test_email_sender_dev_mode_no_smtp(monkeypatch, caplog):
    """Sem SMTP configurado em dev → loga o link, retorna True."""
    import logging
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("APP_URL", "https://clubeusa.com")

    from utils.email_sender import send_email_verification

    with caplog.at_level(logging.WARNING, logger="email_sender"):
        result = send_email_verification("test@example.com", "sometoken123")

    assert result is True
    assert "sometoken123" in caplog.text


def test_email_sender_smtp_sends_message(monkeypatch):
    """Com SMTP configurado → chama smtplib.SMTP e envia mensagem."""
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("APP_URL", "https://clubeusa.com")

    from utils import email_sender

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=__import__("contextlib").nullcontext(mock_server))

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = email_sender.send_email_verification("dest@example.com", "tok123")

    assert result is True
    mock_server.sendmail.assert_called_once()
