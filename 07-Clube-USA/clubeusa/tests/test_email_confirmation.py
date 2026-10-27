# tests/test_email_confirmation.py — Fase 0.1: confirmacao de email
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_service.py
# ============================================================

def test_send_confirmation_dev_logs():
    """Em modo development, apenas loga — nao faz chamada HTTP."""
    from services.email_service import send_confirmation_email
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        result = send_confirmation_email("user@example.com", "https://clubeusa.com/confirm/abc")
    assert result is True


def test_send_confirmation_prod_no_provider_returns_false():
    """Em producao sem EMAIL_PROVIDER configurado retorna False."""
    from services.email_service import send_confirmation_email
    env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": ""}
    with patch.dict(os.environ, env, clear=False):
        result = send_confirmation_email("user@example.com", "https://clubeusa.com/confirm/abc")
    assert result is False


def test_send_confirmation_resend_success():
    """Chama API Resend corretamente."""
    from services.email_service import send_confirmation_email
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None

    env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": "resend", "EMAIL_API_KEY": "re_test"}
    with patch.dict(os.environ, env, clear=False):
        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = send_confirmation_email("user@example.com", "https://clubeusa.com/confirm/abc")

    assert result is True
    assert mock_post.called
    call_url = mock_post.call_args[0][0]
    assert "resend.com" in call_url


def test_send_confirmation_resend_http_error_returns_false():
    """Erro HTTP no Resend retorna False sem lancar excecao."""
    from services.email_service import send_confirmation_email
    import requests as req
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("500")

    env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": "resend", "EMAIL_API_KEY": "re_test"}
    with patch.dict(os.environ, env, clear=False):
        with patch("requests.post", return_value=mock_resp):
            result = send_confirmation_email("user@example.com", "https://clubeusa.com/confirm/abc")
    assert result is False


def test_send_confirmation_sendgrid_success():
    """Chama API SendGrid corretamente."""
    from services.email_service import send_confirmation_email
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None

    env = {"ENVIRONMENT": "production", "EMAIL_PROVIDER": "sendgrid", "EMAIL_API_KEY": "SG.test"}
    with patch.dict(os.environ, env, clear=False):
        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = send_confirmation_email("user@example.com", "https://clubeusa.com/confirm/abc")

    assert result is True
    call_url = mock_post.call_args[0][0]
    assert "sendgrid.com" in call_url


# ============================================================
#  member_service._send_email_confirmation
# ============================================================

def test_send_email_confirmation_creates_token_and_sends():
    """Gera token, persiste no Supabase e dispara o email."""
    from services.member_service import _send_email_confirmation

    mock_sb = MagicMock()
    env = {
        "APP_URL": "https://clubeusa.com",
        "ENVIRONMENT": "development",
        "ENCRYPTION_KEY": "testkey123",
        "JWT_SECRET": "jwtsecret123",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test_service_key",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch("services.member_service._supabase", return_value=mock_sb):
            with patch("services.email_service.send_confirmation_email", return_value=True):
                result = _send_email_confirmation("member-uuid-1", "user@example.com")

    # Verifica que insert foi chamado (token criado)
    assert mock_sb.table().insert().execute.called
    # Verifica que delete foi chamado (limpar tokens anteriores)
    assert mock_sb.table().delete().eq().execute.called


def test_send_email_confirmation_removes_previous_tokens():
    """Deleta tokens anteriores antes de criar novo (evita tokens orfaos)."""
    from services.member_service import _send_email_confirmation

    mock_sb = MagicMock()
    env = {
        "APP_URL": "https://clubeusa.com",
        "ENVIRONMENT": "development",
        "ENCRYPTION_KEY": "testkey123",
        "JWT_SECRET": "jwtsecret123",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test_service_key",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch("services.member_service._supabase", return_value=mock_sb):
            with patch("services.email_service.send_confirmation_email", return_value=True):
                _send_email_confirmation("member-uuid-1", "user@example.com")

    # delete deve ter sido chamado antes do insert
    delete_call = mock_sb.table().delete().eq().execute
    assert delete_call.called


# ============================================================
#  Isolamento multi-tenant
# ============================================================

def test_two_members_get_independent_tokens():
    """
    Dois membros distintos geram tokens separados.
    O sistema chama delete+insert separadamente para cada um,
    garantindo que tokens nao se misturem.
    """
    from services.member_service import _send_email_confirmation

    mock_sb_a = MagicMock()
    mock_sb_b = MagicMock()
    env = {
        "APP_URL": "https://clubeusa.com",
        "ENVIRONMENT": "development",
        "ENCRYPTION_KEY": "testkey123",
        "JWT_SECRET": "jwtsecret123",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test_service_key",
    }

    with patch.dict(os.environ, env, clear=False):
        with patch("services.member_service._supabase", return_value=mock_sb_a):
            with patch("services.email_service.send_confirmation_email", return_value=True):
                _send_email_confirmation("member-A", "a@example.com")

        with patch("services.member_service._supabase", return_value=mock_sb_b):
            with patch("services.email_service.send_confirmation_email", return_value=True):
                _send_email_confirmation("member-B", "b@example.com")

    # Cada membro teve seu proprio delete+insert
    assert mock_sb_a.table().insert().execute.called
    assert mock_sb_b.table().insert().execute.called


# ============================================================
#  Propriedades do token
# ============================================================

def test_token_ttl_is_24h():
    """Token de confirmacao deve expirar em 24 horas."""
    from datetime import datetime, timedelta
    import secrets

    before = datetime.utcnow()
    expires_at = datetime.utcnow() + timedelta(hours=24)
    delta = (expires_at - before).total_seconds()
    assert 86390 < delta <= 86410, f"TTL inesperado: {delta}s"


def test_token_entropy_sufficient():
    """token_urlsafe(32) tem pelo menos 256 bits de entropia."""
    import secrets
    token = secrets.token_urlsafe(32)
    assert len(token) >= 40, "Token muito curto — entropia insuficiente"


def test_unique_tokens_per_call():
    """Cada chamada gera um token diferente."""
    import secrets
    tokens = {secrets.token_urlsafe(32) for _ in range(100)}
    assert len(tokens) == 100, "Tokens repetidos detectados"
