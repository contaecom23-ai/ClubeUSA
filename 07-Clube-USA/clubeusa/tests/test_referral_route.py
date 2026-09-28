# tests/test_referral_route.py — testes para o link de referral rastreavel /i/{code}
import sys, os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api'))

# Env mínimo para o app inicializar (antes de qualquer import do app)
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum-x!")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-chars-min!")
os.environ.setdefault("HASH_SALT", "test-salt")
os.environ.setdefault("STRIPE_SECRET_KEY", "")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "")
os.environ.setdefault("STRIPE_VIP_PRICE_ID", "")
os.environ.setdefault("APP_URL", "https://clubeusa.com")


def _make_client():
    from api.main import app
    return TestClient(app, follow_redirects=False)


# ============================================================
#  /i/{referral_code} — redirect + log
# ============================================================

def test_valid_referral_code_redirects_to_home_with_ref(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "member-uuid-123"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)

    client = _make_client()
    resp = client.get("/i/ABC12345")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12345"


def test_referral_code_is_uppercased(mocker):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = [{"id": "member-uuid-456"}]
    mock_sb.table().insert().execute.return_value.data = [{}]
    mocker.patch("supabase.create_client", return_value=mock_sb)

    client = _make_client()
    resp = client.get("/i/abc12345")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12345"


def test_invalid_code_format_redirects_to_home(mocker):
    mocker.patch("supabase.create_client", return_value=MagicMock())
    client = _make_client()

    resp = client.get("/i/!!bad!!")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_too_short_code_redirects_to_home(mocker):
    mocker.patch("supabase.create_client", return_value=MagicMock())
    client = _make_client()

    resp = client.get("/i/AB")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_nonexistent_code_still_redirects_with_ref(mocker):
    """Código inválido (não encontrado no DB) ainda redireciona — o backend de cadastro rejeitará se não existe."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []  # código não encontrado
    mocker.patch("supabase.create_client", return_value=mock_sb)

    client = _make_client()
    resp = client.get("/i/NOTEXIST")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=NOTEXIST"


def test_audit_log_inserted_for_valid_member(mocker):
    """Verifica que audit_log.insert() é chamado quando o membro existe."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "member-uuid-789"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)

    client = _make_client()
    client.get("/i/VALID123")

    # Verifica que insert foi chamado (audit log)
    assert mock_sb.table.return_value.insert.called


def test_supabase_error_does_not_break_redirect(mocker):
    """Falha no Supabase não deve impedir o redirect — best-effort logging."""
    mock_sb = MagicMock()
    mock_sb.table.side_effect = Exception("DB offline")
    mocker.patch("supabase.create_client", return_value=mock_sb)

    client = _make_client()
    resp = client.get("/i/SAFE1234")
    assert resp.status_code == 302
    assert "?ref=SAFE1234" in resp.headers["location"]
