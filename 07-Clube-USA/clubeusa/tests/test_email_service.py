"""
tests/test_email_service.py — Fase 0.1
Testa o servico de verificacao de email.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ------------------------------------------------------------------ helpers

def _mock_sb(mocker, service_path="services.email_service._supabase"):
    """Cria mock do Supabase e injeta via mocker."""
    mock = MagicMock()
    mocker.patch(service_path, return_value=mock)
    return mock


def _make_token_record(member_id="m-1", hours_until_expiry=20, used_at=None):
    expires = (datetime.now(timezone.utc) + timedelta(hours=hours_until_expiry)).isoformat()
    return {
        "id":         "tok-1",
        "member_id":  member_id,
        "token_hash": "abc123",
        "expires_at": expires,
        "used_at":    used_at,
    }


# ------------------------------------------------------------------ request_verification

def test_request_verification_happy_path(mocker):
    from services.email_service import request_verification

    mock_sb = _mock_sb(mocker)
    # 0 tokens recentes
    mock_sb.table().select().eq().gt().is_().execute.return_value.count = 0
    mock_sb.table().delete().eq().is_().execute.return_value = None
    mock_sb.table().insert().execute.return_value.data = [{"id": "tok-new"}]

    mocker.patch("services.email_service.decrypt", return_value="user@example.com")
    mocker.patch("services.email_service._send_verification_email")

    result = request_verification("m-1", "enc_email")
    assert result["ok"] is True
    assert result["expires_in"] == 86400


def test_request_verification_rate_limit(mocker):
    from services.email_service import request_verification

    mock_sb = _mock_sb(mocker)
    mock_sb.table().select().eq().gt().is_().execute.return_value.count = 3

    with pytest.raises(ValueError, match="Muitas solicitacoes"):
        request_verification("m-1", "enc_email")


def test_request_verification_already_verified_returns_flag(mocker):
    """Se email_verified=True no router, nao chega ao service. Teste defensivo."""
    # Service nao tem acesso direto ao campo; o router bloqueia antes.
    # Aqui testamos que o service nao emite erro se chamado sem token anterior.
    from services.email_service import request_verification

    mock_sb = _mock_sb(mocker)
    mock_sb.table().select().eq().gt().is_().execute.return_value.count = 0
    mock_sb.table().delete().eq().is_().execute.return_value = None
    mock_sb.table().insert().execute.return_value.data = [{"id": "tok-2"}]

    mocker.patch("services.email_service.decrypt", return_value="verified@example.com")
    mocker.patch("services.email_service._send_verification_email")

    result = request_verification("m-verified", "enc")
    assert result["ok"] is True


# ------------------------------------------------------------------ verify_email_token

def test_verify_email_token_valid(mocker):
    from services.email_service import verify_email_token

    mock_sb = _mock_sb(mocker)
    record = _make_token_record()
    mock_sb.table().select().eq().is_().execute.return_value.data = [record]
    mock_sb.table().update().eq().execute.return_value = None

    mocker.patch("services.email_service._hash_token", return_value="abc123")

    result = verify_email_token("rawtoken123")
    assert result["ok"] is True
    assert result["member_id"] == "m-1"


def test_verify_email_token_invalid_returns_error(mocker):
    from services.email_service import verify_email_token

    mock_sb = _mock_sb(mocker)
    mock_sb.table().select().eq().is_().execute.return_value.data = []

    mocker.patch("services.email_service._hash_token", return_value="wronghash")

    with pytest.raises(ValueError, match="inválido"):
        verify_email_token("badtoken")


def test_verify_email_token_expired(mocker):
    from services.email_service import verify_email_token

    mock_sb = _mock_sb(mocker)
    expired_record = _make_token_record(hours_until_expiry=-1)  # 1 hora no passado
    mock_sb.table().select().eq().is_().execute.return_value.data = [expired_record]
    mock_sb.table().delete().eq().execute.return_value = None

    mocker.patch("services.email_service._hash_token", return_value="abc123")

    with pytest.raises(ValueError, match="expirado"):
        verify_email_token("expiredtoken")


def test_verify_email_token_too_long_raises(mocker):
    from services.email_service import verify_email_token

    with pytest.raises(ValueError, match="inválido"):
        verify_email_token("x" * 65)


def test_verify_email_token_empty_raises(mocker):
    from services.email_service import verify_email_token

    with pytest.raises(ValueError, match="inválido"):
        verify_email_token("")


# ------------------------------------------------------------------ isolamento multi-tenant

def test_verify_cannot_use_other_members_token(mocker):
    """Token valido de membro A nao pode ser reutilizado por membro B."""
    from services.email_service import verify_email_token

    mock_sb = _mock_sb(mocker)
    record_a = _make_token_record(member_id="member-A")
    mock_sb.table().select().eq().is_().execute.return_value.data = [record_a]
    mock_sb.table().update().eq().execute.return_value = None

    mocker.patch("services.email_service._hash_token", return_value="abc123")

    # Token valido de A: retorna member_id de A, nao B
    result = verify_email_token("rawtoken")
    assert result["member_id"] == "member-A"
    # Nao ha como usar o mesmo token novamente (is_("used_at", None) falharia)
