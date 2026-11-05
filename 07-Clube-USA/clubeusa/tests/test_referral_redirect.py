"""
Testes para a rota GET /r/{referral_code} (Fase 0.2).

Cobre:
- Redirect para /?ref={code} com código válido
- Cookie cu_ref setado no redirect
- Redirect para / (sem parâmetro) com código inválido
- Formato do código (case-insensitive, normalizado para upper)
- Log do clique no audit_log quando código existe no banco
"""
import os, sys, pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Garante que api/ e raiz do projeto estão no path
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api'))

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-key")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-chars-pad")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("STRIPE_SECRET_KEY", "")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "")
os.environ.setdefault("STRIPE_VIP_PRICE_ID", "")


@pytest.fixture
def client(mocker):
    """Cliente de teste com Supabase mockado."""
    # Evita importar supabase real durante os testes
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{}]

    mocker.patch("supabase.create_client", return_value=mock_sb)

    from fastapi.testclient import TestClient
    import main as app_module
    return TestClient(app_module.app, follow_redirects=False)


def test_valid_code_redirects_to_landing(client):
    resp = client.get("/r/ABC12345")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12345"


def test_valid_code_lowercase_normalized(client):
    resp = client.get("/r/abc12345")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12345"


def test_valid_code_sets_cookie(client):
    resp = client.get("/r/XYZXYZ12")
    assert resp.status_code == 302
    cookie = resp.cookies.get("cu_ref")
    assert cookie == "XYZXYZ12"


def test_invalid_code_too_short_redirects_home(client):
    resp = client.get("/r/AB")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_invalid_code_special_chars_redirects_home(client):
    resp = client.get("/r/ABC_12345!")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_valid_code_logs_click_when_member_exists(mocker):
    """Clique é registrado no audit_log quando o código pertence a um membro ativo."""
    mock_sb = MagicMock()
    # Simula membro encontrado
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "member-uuid-123"}
    ]
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{}]
    mocker.patch("supabase.create_client", return_value=mock_sb)

    from fastapi.testclient import TestClient
    import main as app_module
    client_local = TestClient(app_module.app, follow_redirects=False)

    resp = client_local.get("/r/VALIDCODE1")
    assert resp.status_code == 302

    # Verifica que insert foi chamado (log do clique)
    insert_call_args = mock_sb.table.return_value.insert.call_args
    assert insert_call_args is not None
    payload = insert_call_args[0][0]
    assert payload["action"] == "referral.link_clicked"
    assert payload["metadata"]["referral_code"] == "VALIDCODE1"


def test_supabase_failure_does_not_break_redirect(mocker):
    """Falha no Supabase não bloqueia o redirect."""
    mocker.patch("supabase.create_client", side_effect=Exception("DB offline"))

    from fastapi.testclient import TestClient
    import main as app_module
    client_local = TestClient(app_module.app, follow_redirects=False)

    resp = client_local.get("/r/ANYCODE12")
    assert resp.status_code == 302
    assert "ref=ANYCODE12" in resp.headers["location"]
