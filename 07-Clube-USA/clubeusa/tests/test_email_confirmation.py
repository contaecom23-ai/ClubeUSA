# tests/test_email_confirmation.py — Fase 0.1: confirmacao de email
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

_UTC = timezone.utc


# ============================================================
#  Helpers
# ============================================================

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_sb_mock():
    """MagicMock do Supabase com encadeamento fluente."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.execute.return_value.data = []
    return mock


# ============================================================
#  create_confirmation_token
# ============================================================

def test_create_confirmation_token_inserts_hash_not_raw_token(mocker):
    """O banco deve receber apenas o hash SHA-256, nunca o token puro."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    inserted = {}
    mock_sb = _make_sb_mock()

    def capture_insert(data):
        inserted.update(data)
        return mock_sb
    mock_sb.insert.side_effect = capture_insert

    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import create_confirmation_token
    raw_token = create_confirmation_token("member-uuid-123")

    # raw_token é urlsafe (~43 chars); hash é hexdigest (64 chars)
    assert len(raw_token) > 0
    assert "token_hash" in inserted
    assert len(inserted["token_hash"]) == 64
    assert inserted["token_hash"] != raw_token
    assert inserted["token_hash"] == _hash_token(raw_token)


def test_create_confirmation_token_invalidates_previous(mocker):
    """Tokens anteriores do mesmo membro devem ser deletados antes de criar novo."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    mock_sb = _make_sb_mock()
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import create_confirmation_token
    create_confirmation_token("member-uuid-123")

    mock_sb.delete.assert_called()


# ============================================================
#  verify_confirmation_token
# ============================================================

def test_verify_confirmation_token_invalid_token(mocker):
    """Token nao encontrado no banco retorna None."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token("token-invalido")
    assert result is None


def test_verify_confirmation_token_expired(mocker):
    """Token expirado retorna None e e deletado."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    expired_time = (datetime.now(_UTC) - timedelta(hours=1)).isoformat()

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "m-1", "expires_at": expired_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token(token)

    assert result is None
    mock_sb.delete.assert_called()


def test_verify_confirmation_token_valid(mocker):
    """Token valido retorna member_id e deleta token (uso unico)."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    future_time = (datetime.now(_UTC) + timedelta(hours=20)).isoformat()

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "member-uuid-abc", "expires_at": future_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token(token)

    assert result == "member-uuid-abc"
    mock_sb.delete.assert_called()


def test_verify_confirmation_token_empty(mocker):
    """Token vazio retorna None sem acessar o banco."""
    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token("")
    assert result is None


def test_verify_confirmation_token_too_long(mocker):
    """Token muito longo retorna None sem acessar o banco."""
    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token("x" * 300)
    assert result is None


# ============================================================
#  Isolamento multi-tenant
# ============================================================

def test_verify_confirmation_token_member_id_from_server(mocker):
    """
    O member_id retornado vem SEMPRE do banco (servidor), nunca do token em si.
    Nao ha como usar token de outro membro: o banco retorna o membro certo.
    """
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    future_time = (datetime.now(_UTC) + timedelta(hours=20)).isoformat()

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "m-correto", "expires_at": future_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import verify_confirmation_token
    result = verify_confirmation_token(token)

    assert result == "m-correto"


# ============================================================
#  send_confirmation_email (dev mode)
# ============================================================

def test_send_confirmation_email_dev_mode_returns_true(mocker):
    """Em dev (ENVIRONMENT != production), retorna True sem enviar email."""
    mocker.patch.dict("os.environ", {
        "ENVIRONMENT": "development",
    }, clear=False)

    from services.email_service import send_confirmation_email
    result = send_confirmation_email("user@example.com", "https://clubeusa.com/auth/email/confirm/abc")
    assert result is True
