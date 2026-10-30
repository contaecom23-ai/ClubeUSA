# ============================================================
#  tests/test_email_confirm.py — Fase 0.1: confirmação de email
# ============================================================
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ---- utils/email.py ----

def test_generate_confirm_token_returns_tuple():
    from utils.email import generate_confirm_token
    token, token_hash = generate_confirm_token()
    assert isinstance(token, str) and len(token) > 20
    assert isinstance(token_hash, str) and len(token_hash) == 64  # SHA-256 hex


def test_verify_token_hash_correct():
    from utils.email import generate_confirm_token, verify_token_hash
    token, token_hash = generate_confirm_token()
    assert verify_token_hash(token, token_hash) is True


def test_verify_token_hash_wrong():
    from utils.email import generate_confirm_token, verify_token_hash
    token, _ = generate_confirm_token()
    _, wrong_hash = generate_confirm_token()
    assert verify_token_hash(token, wrong_hash) is False


def test_send_email_confirmation_dev_mode_logs(caplog):
    """Em dev (sem EMAIL_PROVIDER), deve apenas logar."""
    import logging
    from utils.email import send_email_confirmation
    with patch.dict("os.environ", {"EMAIL_PROVIDER": "", "APP_URL": "https://test.com"}):
        with caplog.at_level(logging.INFO, logger="email"):
            send_email_confirmation("test@example.com", "mem-123", "tok-abc", "pt")
    assert "DEV" in caplog.text or "test@example.com" in caplog.text


# ---- services/email_confirm_service.py ----

def _make_sb_mock(email_enc="enc_email", email_verified=False, language="pt"):
    """Monta mock do Supabase para os testes do email confirm service."""
    from unittest.mock import MagicMock
    sb = MagicMock()

    # members select
    sb.table("members").select().eq().execute.return_value.data = [{
        "email_enc":      email_enc,
        "email_verified": email_verified,
        "language":       language,
    }]

    # email_confirm_tokens delete (limpar anterior)
    sb.table("email_confirm_tokens").delete().eq().execute.return_value.data = []

    # email_confirm_tokens insert
    sb.table("email_confirm_tokens").insert().execute.return_value.data = [{"id": "tok-1"}]

    return sb


def test_request_confirmation_returns_false_when_no_email(mocker):
    from services.email_confirm_service import request_email_confirmation
    sb = _make_sb_mock(email_enc=None)
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    result = request_email_confirmation("mem-1")
    assert result is False


def test_request_confirmation_returns_true_when_already_verified(mocker):
    from services.email_confirm_service import request_email_confirmation
    sb = _make_sb_mock(email_verified=True)
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    result = request_email_confirmation("mem-1")
    assert result is True


def test_request_confirmation_sends_email(mocker):
    from services.email_confirm_service import request_email_confirmation
    sb = _make_sb_mock()
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    mocker.patch("services.email_confirm_service.decrypt", return_value="user@example.com")
    mock_send = mocker.patch("services.email_confirm_service.send_email_confirmation")
    mocker.patch("services.email_confirm_service.generate_confirm_token",
                 return_value=("tok", "tok_hash"))

    result = request_email_confirmation("mem-1")
    assert result is True
    mock_send.assert_called_once()


def test_verify_confirmation_invalid_token(mocker):
    from services.email_confirm_service import verify_email_confirmation
    sb = MagicMock()
    sb.table("email_confirm_tokens").select().eq().execute.return_value.data = []
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)

    with pytest.raises(ValueError, match="Token inválido"):
        verify_email_confirmation("invalid_token")


def test_verify_confirmation_expired_token(mocker):
    from services.email_confirm_service import verify_email_confirmation
    sb = MagicMock()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    sb.table("email_confirm_tokens").select().eq().execute.return_value.data = [{
        "id":         "tok-1",
        "member_id":  "mem-1",
        "token_hash": "anything",
        "expires_at": past,
        "used_at":    None,
    }]
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    mocker.patch("utils.email._hash_token", return_value="anything")

    with pytest.raises(ValueError, match="expirado"):
        verify_email_confirmation("sometoken")


def test_verify_confirmation_already_used(mocker):
    from services.email_confirm_service import verify_email_confirmation
    sb = MagicMock()
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
    sb.table("email_confirm_tokens").select().eq().execute.return_value.data = [{
        "id":         "tok-1",
        "member_id":  "mem-1",
        "token_hash": "anything",
        "expires_at": future,
        "used_at":    "2026-01-01T00:00:00+00:00",
    }]
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    mocker.patch("utils.email._hash_token", return_value="anything")

    with pytest.raises(ValueError, match="já utilizado"):
        verify_email_confirmation("sometoken")


def test_verify_confirmation_success(mocker):
    from services.email_confirm_service import verify_email_confirmation
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()

    sb = MagicMock()
    sb.table("email_confirm_tokens").select().eq().execute.return_value.data = [{
        "id":         "tok-1",
        "member_id":  "mem-1",
        "token_hash": "correct_hash",
        "expires_at": future,
        "used_at":    None,
    }]
    # update calls return data
    sb.table("email_confirm_tokens").update().eq().execute.return_value.data = [{}]
    sb.table("members").update().eq().execute.return_value.data = [{"id": "mem-1"}]
    sb.table("audit_logs").insert().execute.return_value.data = [{}]

    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    mocker.patch("utils.email._hash_token", return_value="correct_hash")

    result = verify_email_confirmation("sometoken")
    assert result["ok"] is True
    assert result["member_id"] == "mem-1"


# ---- isolamento multi-tenant ----

def test_verify_token_only_matches_exact_hash(mocker):
    """Token de membro A não pode confirmar email do membro B."""
    from services.email_confirm_service import verify_email_confirmation
    future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()

    sb = MagicMock()
    # Banco retorna vazio para o hash do token de A buscado
    sb.table("email_confirm_tokens").select().eq().execute.return_value.data = []
    mocker.patch("services.email_confirm_service._supabase", return_value=sb)
    mocker.patch("utils.email._hash_token", return_value="hash_of_token_A")

    with pytest.raises(ValueError):
        verify_email_confirmation("token_de_A_tentando_confirmar_B")
