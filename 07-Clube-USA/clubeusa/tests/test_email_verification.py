# tests/test_email_verification.py — Fase 0.1
import os, sys, hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api'))

# Stub heavy deps that may not be in the CI venv
from unittest.mock import MagicMock as _MM
for _mod in [
    "cryptography", "cryptography.fernet",
    "supabase", "jose", "jose.jwt",
    "stripe", "feedparser", "requests",
    "httpx", "fastapi", "uvicorn",
    "dotenv", "python_dotenv",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = _MM()
# Fernet precisa ser 'chamavel' para Fernet(key) funcionar
sys.modules["cryptography.fernet"].Fernet = lambda k: _MM()

# Env vars minimos para importar os modulos
os.environ.setdefault("SUPABASE_URL",         "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY",  "test_key")
os.environ.setdefault("ENCRYPTION_KEY",        "test_encryption_key_32bytes!!!!!")
os.environ.setdefault("JWT_SECRET",            "test_jwt_secret")
os.environ.setdefault("APP_BASE_URL",          "https://clubeusa.com")

from services.email_service import (
    generate_email_verification_token,
    hash_token,
    send_verification_email,
)


# ============================================================
#  Testes de geracao de token
# ============================================================

def test_token_generation_returns_three_values():
    plain, h, expires = generate_email_verification_token()
    assert isinstance(plain, str) and len(plain) > 20
    assert isinstance(h, str) and len(h) == 64   # SHA-256 hex
    assert isinstance(expires, datetime)


def test_token_hash_is_deterministic():
    plain, h, _ = generate_email_verification_token()
    assert hash_token(plain) == h


def test_token_expiry_is_future():
    _, _, expires = generate_email_verification_token()
    assert expires > datetime.utcnow()


def test_two_tokens_are_different():
    t1, _, _ = generate_email_verification_token()
    t2, _, _ = generate_email_verification_token()
    assert t1 != t2


# ============================================================
#  Testes de envio de email (sem credenciais reais)
# ============================================================

def test_send_email_dev_mode_returns_true():
    """Sem RESEND_API_KEY e SMTP_HOST, deve retornar True (modo dev)."""
    env = {"RESEND_API_KEY": None, "SMTP_HOST": None}
    with patch.dict(os.environ, {k: "" for k in env}, clear=False):
        # Remove as chaves para simular modo dev
        for k in env:
            os.environ.pop(k, None)
        result = send_verification_email("test@example.com", "tok", "Joao", "pt")
        assert result is True


def test_send_email_resend_success():
    """Com RESEND_API_KEY, deve chamar a API Resend."""
    os.environ["RESEND_API_KEY"] = "re_test_key"
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_verification_email("test@example.com", "tok123", "Maria", "pt")
    assert result is True
    del os.environ["RESEND_API_KEY"]


def test_send_email_resend_failure_returns_false():
    """Erro na chamada Resend retorna False sem lancar excecao."""
    os.environ["RESEND_API_KEY"] = "re_test_key"
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        result = send_verification_email("test@example.com", "tok123", "Maria", "es")
    assert result is False
    del os.environ["RESEND_API_KEY"]


def test_send_email_spanish_subject():
    """Email em espanhol usa subject correto."""
    # Testa template sem enviar de verdade
    from services.email_service import _build_verification_email
    subject, text, html = _build_verification_email("Ana Lopez", "https://test.com/verify?token=abc", "es")
    assert "Confirma tu correo" in subject
    assert "Ana" in text
    assert "https://test.com/verify?token=abc" in html


def test_send_email_portuguese_subject():
    from services.email_service import _build_verification_email
    subject, text, html = _build_verification_email("Carlos Silva", "https://test.com/verify?token=abc", "pt")
    assert "Confirme seu email" in subject
    assert "Carlos" in text
    assert "https://test.com/verify?token=abc" in html


# ============================================================
#  Testes da logica de verificacao (member_service, com mock Supabase)
# ============================================================

def _make_sb_mock(token_row: dict = None, member_row: dict = None):
    """Helper: retorna mock do Supabase com dados configuaveis."""
    sb = MagicMock()

    # email_verification_tokens
    evt_select = MagicMock()
    evt_select.data = [token_row] if token_row else []
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = evt_select
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = evt_select

    return sb


def test_verify_email_token_invalid_hash():
    """Token com hash desconhecido levanta ValueError."""
    from services import member_service

    with patch.object(member_service, "_supabase") as mock_sb:
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.return_value = sb

        try:
            member_service.verify_email_token("token_invalido_xpto")
            assert False, "Deveria ter lancado ValueError"
        except ValueError as e:
            assert "invalido" in str(e).lower()


def test_verify_email_token_already_used():
    """Token ja utilizado levanta ValueError."""
    from services import member_service

    token_plain, token_hash, expires = generate_email_verification_token()
    expires_future = (datetime.utcnow() + timedelta(hours=23)).isoformat() + "+00:00"

    row = {
        "id": "uuid-token-1",
        "member_id": "uuid-member-1",
        "expires_at": expires_future,
        "used_at": datetime.utcnow().isoformat(),  # ja usado
    }

    with patch.object(member_service, "_supabase") as mock_sb:
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[row])
        mock_sb.return_value = sb

        try:
            member_service.verify_email_token(token_plain)
            assert False, "Deveria ter lancado ValueError"
        except ValueError as e:
            assert "utilizado" in str(e).lower()


def test_verify_email_token_expired():
    """Token expirado levanta ValueError."""
    from services import member_service

    token_plain, token_hash, _ = generate_email_verification_token()
    expires_past = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "+00:00"

    row = {
        "id": "uuid-token-2",
        "member_id": "uuid-member-2",
        "expires_at": expires_past,
        "used_at": None,
    }

    with patch.object(member_service, "_supabase") as mock_sb:
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[row])
        mock_sb.return_value = sb

        try:
            member_service.verify_email_token(token_plain)
            assert False, "Deveria ter lancado ValueError"
        except ValueError as e:
            assert "expirado" in str(e).lower()


def test_verify_email_token_success():
    """Token valido marca email como verificado e retorna ok=True."""
    from services import member_service

    token_plain, token_hash, _ = generate_email_verification_token()
    expires_future = (datetime.utcnow() + timedelta(hours=23)).isoformat() + "+00:00"

    row = {
        "id": "uuid-token-3",
        "member_id": "uuid-member-3",
        "expires_at": expires_future,
        "used_at": None,
    }

    with patch.object(member_service, "_supabase") as mock_sb:
        sb = MagicMock()

        # select retorna o row
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[row])
        # update e delete nao falham
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

        mock_sb.return_value = sb

        result = member_service.verify_email_token(token_plain)

    assert result["ok"] is True
    assert result["member_id"] == "uuid-member-3"
