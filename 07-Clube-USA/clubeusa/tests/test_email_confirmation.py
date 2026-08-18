# ============================================================
#  tests/test_email_confirmation.py — Clube USA
#  Testes: confirmacao de email (Fase 0.1)
# ============================================================

import logging
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone


# ============================================================
#  generate_email_token
# ============================================================

def test_generate_email_token_length():
    from services.email_service import generate_email_token
    assert len(generate_email_token()) >= 32


def test_generate_email_token_uniqueness():
    from services.email_service import generate_email_token
    tokens = {generate_email_token() for _ in range(50)}
    assert len(tokens) == 50, "Tokens devem ser unicos"


def test_generate_email_token_url_safe():
    import re
    from services.email_service import generate_email_token
    token = generate_email_token()
    assert re.match(r'^[A-Za-z0-9_-]+$', token), "Token deve ser URL-safe"


# ============================================================
#  request_email_confirmation
# ============================================================

def test_request_confirmation_member_not_found(mocker):
    from services.email_service import request_email_confirmation
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="nao encontrado"):
        request_email_confirmation("nonexistent-id")


def test_request_confirmation_no_email(mocker):
    from services.email_service import request_email_confirmation
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": None, "email_confirmed": False, "email_token_expires_at": None}
    ]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="Nenhum email"):
        request_email_confirmation("member-id")


def test_request_confirmation_already_confirmed(mocker):
    from services.email_service import request_email_confirmation
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc", "email_confirmed": True, "email_token_expires_at": None}
    ]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="ja confirmado"):
        request_email_confirmation("member-id")


def test_request_confirmation_rate_limit_active_token(mocker):
    from services.email_service import request_email_confirmation
    future = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc", "email_confirmed": False, "email_token_expires_at": future}
    ]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="Aguarde"):
        request_email_confirmation("member-id")


def test_request_confirmation_expired_token_resends(mocker):
    from services.email_service import request_email_confirmation
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc_email", "email_confirmed": False, "email_token_expires_at": past}
    ]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    mocker.patch("services.email_service._decrypt", return_value="user@example.com")
    mock_send = mocker.patch("services.email_service.send_confirmation_email")

    result = request_email_confirmation("member-id")

    assert result["expires_in_hours"] == 24
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0]
    assert call_args[0] == "user@example.com"
    assert call_args[1] == "member-id"


def test_request_confirmation_no_previous_token_sends(mocker):
    from services.email_service import request_email_confirmation
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc_email", "email_confirmed": False, "email_token_expires_at": None}
    ]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    mocker.patch("services.email_service._decrypt", return_value="user@example.com")
    mock_send = mocker.patch("services.email_service.send_confirmation_email")

    result = request_email_confirmation("member-id")
    assert result["message"] == "Email de confirmacao enviado."
    mock_send.assert_called_once()


# ============================================================
#  confirm_email_token
# ============================================================

def test_confirm_token_empty_raises(mocker):
    from services.email_service import confirm_email_token
    with pytest.raises(ValueError, match="invalido"):
        confirm_email_token("")


def test_confirm_token_too_long_raises(mocker):
    from services.email_service import confirm_email_token
    with pytest.raises(ValueError, match="invalido"):
        confirm_email_token("x" * 200)


def test_confirm_token_not_found(mocker):
    from services.email_service import confirm_email_token
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="invalido ou expirado"):
        confirm_email_token("bad-token")


def test_confirm_token_expired(mocker):
    from services.email_service import confirm_email_token
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "m-1", "email_token": "tok", "email_token_expires_at": past, "email_confirmed": False}
    ]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="expirado"):
        confirm_email_token("tok")


def test_confirm_token_already_confirmed_returns_no_points(mocker):
    from services.email_service import confirm_email_token
    future = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "m-1", "email_token": "tok", "email_token_expires_at": future, "email_confirmed": True}
    ]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    result = confirm_email_token("tok")
    assert result["points_awarded"] == 0


def test_confirm_token_success_marks_confirmed_and_awards_points(mocker):
    from services.email_service import confirm_email_token
    future = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "m-1", "email_token": "tok", "email_token_expires_at": future, "email_confirmed": False}
    ]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mock_sb.rpc().execute.return_value = MagicMock()
    mock_sb.table().insert().execute.return_value = MagicMock()
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    result = confirm_email_token("tok")

    assert result["points_awarded"] == 50
    assert "confirmado" in result["message"].lower()


def test_confirm_token_success_clears_token(mocker):
    from services.email_service import confirm_email_token
    future = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "m-1", "email_token": "tok", "email_token_expires_at": future, "email_confirmed": False}
    ]
    update_mock = MagicMock()
    update_mock.eq().execute.return_value.data = [{}]
    mock_sb.table().update.return_value = update_mock
    mock_sb.rpc().execute.return_value = MagicMock()
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    confirm_email_token("tok")

    update_call_kwargs = mock_sb.table().update.call_args[0][0]
    assert update_call_kwargs.get("email_confirmed") is True
    assert update_call_kwargs.get("email_token") is None
    assert update_call_kwargs.get("email_token_expires_at") is None


# ============================================================
#  update_member_email
# ============================================================

def test_update_email_in_use_raises(mocker):
    from services.email_service import update_member_email
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{"id": "outro-membro"}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    mocker.patch("services.email_service._hash_pii", return_value="hash123")
    mocker.patch("services.email_service._encrypt", return_value="enc")
    mocker.patch("services.email_service._validate_email", return_value="test@example.com")
    with pytest.raises(ValueError, match="em uso"):
        update_member_email("member-id", "test@example.com")


def test_update_email_same_member_is_allowed(mocker):
    """Membro pode re-salvar seu proprio email sem conflito."""
    from services.email_service import update_member_email
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{"id": "member-id"}]
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    mocker.patch("services.email_service._hash_pii", return_value="hash123")
    mocker.patch("services.email_service._encrypt", return_value="enc")
    mocker.patch("services.email_service._validate_email", return_value="test@example.com")
    result = update_member_email("member-id", "test@example.com")
    assert result["email_confirmed"] is False


def test_update_email_no_conflict_succeeds(mocker):
    from services.email_service import update_member_email
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mock_sb.table().update().eq().execute.return_value.data = [{}]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    mocker.patch("services.email_service._hash_pii", return_value="hash123")
    mocker.patch("services.email_service._encrypt", return_value="enc")
    mocker.patch("services.email_service._validate_email", return_value="novo@example.com")
    result = update_member_email("member-id", "novo@example.com")
    assert result["email_confirmed"] is False
    assert "atualizado" in result["message"].lower()


# ============================================================
#  send_confirmation_email — modo dev
# ============================================================

def test_send_confirmation_email_dev_does_not_raise(monkeypatch, caplog):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    import services.email_service as svc
    with caplog.at_level(logging.INFO, logger="email_service"):
        svc.send_confirmation_email("user@test.com", "member-id", "safe_token_abc123")
    # Nao deve lancar excecao; deve apenas logar


def test_send_via_resend_missing_key_logs_error(monkeypatch, caplog):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("RESEND_API_KEY", "")
    import services.email_service as svc
    with caplog.at_level(logging.ERROR, logger="email_service"):
        svc._send_via_resend("user@test.com", "https://clubeusa.com/confirm?token=x")
    assert "RESEND_API_KEY" in caplog.text


def test_send_via_sendgrid_missing_key_logs_error(monkeypatch, caplog):
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    monkeypatch.setenv("SENDGRID_API_KEY", "")
    import services.email_service as svc
    with caplog.at_level(logging.ERROR, logger="email_service"):
        svc._send_via_sendgrid("user@test.com", "https://clubeusa.com/confirm?token=x")
    assert "SENDGRID_API_KEY" in caplog.text


# ============================================================
#  Isolamento multi-tenant: token so acessa o proprio membro
# ============================================================

def test_confirm_token_cross_tenant_impossible(mocker):
    """
    Garantia: o token e unico por membro (UNIQUE na coluna email_token).
    Um token forjado que nao existe retorna 'invalido', nunca dados de outro membro.
    """
    from services.email_service import confirm_email_token
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    with pytest.raises(ValueError, match="invalido"):
        confirm_email_token("token-de-outro-membro")
