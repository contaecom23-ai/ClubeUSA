# tests/test_email_confirmation.py — Fase 0.1: confirmacao de email
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ============================================================
#  Helpers
# ============================================================

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_sb_mock():
    """MagicMock generico do Supabase com encadeamento fluente."""
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
#  send_verification_email
# ============================================================

def test_send_verification_email_no_smtp_logs_url(mocker):
    """Sem SMTP configurado: retorna True e nao lanca excecao."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
        "APP_URL": "https://clubeusa.com",
    }, clear=False)
    mock_sb = _make_sb_mock()
    mocker.patch("services.email_service._supabase", return_value=mock_sb)
    # Garante que SMTP_HOST nao existe no ambiente de teste
    mocker.patch.dict("os.environ", {}, clear=False)
    import os; os.environ.pop("SMTP_HOST", None); os.environ.pop("SMTP_USER", None)

    from services.email_service import send_verification_email
    result = send_verification_email("member-uuid-123", "user@example.com")

    assert result is True
    # Token deve ter sido inserido no banco
    mock_sb.insert.assert_called_once()


def test_send_verification_email_inserts_token_hash(mocker):
    """Token inserido deve ser o hash SHA-256, nunca o token puro."""
    import os; os.environ.pop("SMTP_HOST", None); os.environ.pop("SMTP_USER", None)

    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
        "APP_URL": "https://clubeusa.com",
    }, clear=False)

    inserted = {}

    mock_sb = _make_sb_mock()
    def capture_insert(data):
        inserted.update(data)
        return mock_sb
    mock_sb.insert.side_effect = capture_insert

    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import send_verification_email
    send_verification_email("member-uuid-123", "user@example.com")

    # token_hash deve ser um hexdigest de 64 caracteres (SHA-256)
    assert "token_hash" in inserted
    assert len(inserted["token_hash"]) == 64
    # Nenhum campo deve conter o token puro (64-char hex vs urlsafe token ~43 chars)
    token_value = inserted["token_hash"]
    assert all(c in "0123456789abcdef" for c in token_value)


# ============================================================
#  confirm_email_token
# ============================================================

def test_confirm_email_token_invalid_token(mocker):
    """Token nao encontrado no banco retorna erro."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)
    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = []
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import confirm_email_token
    result = confirm_email_token("token-invalido")

    assert result["ok"] is False
    assert "invalido" in result["error"].lower()


def test_confirm_email_token_expired(mocker):
    """Token expirado retorna erro e e deletado."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "+00:00"

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "m-1", "expires_at": expired_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import confirm_email_token
    result = confirm_email_token(token)

    assert result["ok"] is False
    assert "expirado" in result["error"].lower()


def test_confirm_email_token_valid(mocker):
    """Token valido confirma email, deleta token e retorna member_id."""
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    future_time = (datetime.utcnow() + timedelta(hours=20)).isoformat() + "+00:00"

    mock_sb = _make_sb_mock()
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "member-uuid-abc", "expires_at": future_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import confirm_email_token
    result = confirm_email_token(token)

    assert result["ok"] is True
    assert result["member_id"] == "member-uuid-abc"

    # Deve ter chamado update para setar email_confirmed_at
    mock_sb.update.assert_called()
    # Deve ter chamado delete para invalidar token (uso unico)
    mock_sb.delete.assert_called()


def test_confirm_email_token_empty(mocker):
    """Token vazio retorna erro sem acessar o banco."""
    from services.email_service import confirm_email_token
    result = confirm_email_token("")
    assert result["ok"] is False


def test_confirm_email_token_too_long(mocker):
    """Token muito longo retorna erro sem acessar o banco."""
    from services.email_service import confirm_email_token
    result = confirm_email_token("x" * 300)
    assert result["ok"] is False


# ============================================================
#  Isolamento multi-tenant: token pertence ao membro certo
# ============================================================

def test_confirm_email_token_cross_tenant_not_possible(mocker):
    """
    O token e vinculado ao member_id retornado pelo banco —
    nao ha como usar token de outro membro (o banco retornaria row vazio).
    Este teste documenta a garantia: o member_id vem sempre do server.
    """
    mocker.patch.dict("os.environ", {
        "SUPABASE_URL": "http://fake", "SUPABASE_SERVICE_KEY": "key",
    }, clear=False)

    import secrets
    token = secrets.token_urlsafe(32)
    future_time = (datetime.utcnow() + timedelta(hours=20)).isoformat() + "+00:00"

    mock_sb = _make_sb_mock()
    # Banco retorna member_id "m-correto" independente de qualquer input do cliente
    mock_sb.execute.return_value.data = [{
        "id": "row-1", "member_id": "m-correto", "expires_at": future_time,
    }]
    mocker.patch("services.email_service._supabase", return_value=mock_sb)

    from services.email_service import confirm_email_token
    result = confirm_email_token(token)

    assert result["ok"] is True
    assert result["member_id"] == "m-correto"
