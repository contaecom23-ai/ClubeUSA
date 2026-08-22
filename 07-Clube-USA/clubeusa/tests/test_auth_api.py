"""Testes dos endpoints de autenticacao: register, OTP request/verify."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-dummy-value-32b")
os.environ.setdefault("SECRET_KEY", "test-secret-key-dummy-value-for-jwt-32b")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("APP_URL", "https://clubeusa.com")

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pytest


def _client():
    from main import app
    app.dependency_overrides.clear()
    return TestClient(app)


# --- /health (publico, sem auth) ---

def test_health_returns_ok():
    client = _client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# --- /public/groups (publico, sem auth) ---

def test_public_groups_accessible_without_auth():
    client = _client()
    resp = client.get("/public/groups")
    assert resp.status_code == 200
    assert "groups" in resp.json()


# --- POST /auth/register — validacao de entrada ---

def test_register_invalid_language_returns_422():
    """Idioma invalido (nao 'pt' ou 'es') deve retornar 422."""
    client = _client()
    resp = client.post("/auth/register", json={"phone": "+15559990000", "language": "fr"})
    assert resp.status_code == 422


def test_register_categories_invalid_falls_to_all(mocker):
    """Categorias invalidas devem ser filtradas para ['all'] sem erro 500."""
    mocker.patch(
        "services.member_service.register_member",
        return_value={"id": "m-1", "referral_code": "ABC123"},
    )
    client = _client()
    resp = client.post("/auth/register", json={
        "phone": "+15559990001",
        "language": "pt",
        "categories": ["invalida_xxx", "outra_invalida"],
    })
    assert resp.status_code == 201


def test_register_valid_payload_returns_201(mocker):
    mocker.patch(
        "services.member_service.register_member",
        return_value={"id": "m-2", "referral_code": "DEF456"},
    )
    client = _client()
    resp = client.post("/auth/register", json={
        "phone": "+15559990002",
        "name": "Joao Silva",
        "language": "pt",
        "state": "FL",
        "categories": ["electronics", "kitchen"],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "m-2"


def test_register_with_referral_code_passes_to_service(mocker):
    mock_reg = mocker.patch(
        "services.member_service.register_member",
        return_value={"id": "m-3", "referral_code": "GHI789"},
    )
    client = _client()
    resp = client.post("/auth/register", json={
        "phone": "+15559990003",
        "language": "pt",
        "referral_code": "REF001",
    })
    assert resp.status_code == 201
    call_kwargs = mock_reg.call_args[1]
    assert call_kwargs["referral_code"] == "REF001"


def test_register_value_error_returns_422(mocker):
    """Se o servico levanta ValueError (ex: telefone ja cadastrado), retorna 422."""
    mocker.patch(
        "services.member_service.register_member",
        side_effect=ValueError("Telefone ja cadastrado."),
    )
    client = _client()
    resp = client.post("/auth/register", json={"phone": "+15559990004", "language": "pt"})
    assert resp.status_code == 422
    assert "Telefone ja cadastrado" in resp.json()["detail"]


def test_register_permission_error_returns_403(mocker):
    """PermissionError (ex: IP banido) retorna 403."""
    mocker.patch(
        "services.member_service.register_member",
        side_effect=PermissionError(),
    )
    client = _client()
    resp = client.post("/auth/register", json={"phone": "+15559990005", "language": "pt"})
    assert resp.status_code == 403


# --- POST /auth/otp/request ---

def test_otp_request_invalid_phone_returns_422(mocker):
    mocker.patch("utils.security.validate_phone", side_effect=ValueError("invalido"))
    client = _client()
    resp = client.post("/auth/otp/request", json={"phone": "nao-e-telefone"})
    assert resp.status_code == 422


def test_otp_request_valid_phone_returns_200(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990006")
    mocker.patch("utils.security.generate_otp", return_value="123456")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_x")
    mocker.patch("main._otp_save")
    client = _client()
    resp = client.post("/auth/otp/request", json={"phone": "+15559990006"})
    assert resp.status_code == 200
    data = resp.json()
    assert "expires_in" in data
    assert data["expires_in"] == 600


# --- POST /auth/otp/verify ---

def test_otp_verify_wrong_code_returns_400(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990007")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_y")
    mocker.patch("main._otp_verify", return_value=(False, "Codigo incorreto."))
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990007", "otp": "000000"})
    assert resp.status_code == 400
    assert "incorreto" in resp.json()["detail"]


def test_otp_verify_too_many_attempts_returns_429(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990008")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_z")
    mocker.patch("main._otp_verify", return_value=(False, "Muitas tentativas. Solicite novo codigo."))
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990008", "otp": "111111"})
    assert resp.status_code == 429


def test_otp_verify_expired_code_returns_400(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990009")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_a")
    mocker.patch("main._otp_verify", return_value=(False, "Codigo expirado. Solicite um novo."))
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990009", "otp": "222222"})
    assert resp.status_code == 400
    assert "expirado" in resp.json()["detail"]


def test_otp_verify_member_not_found_returns_404(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990010")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_b")
    mocker.patch("main._otp_verify", return_value=(True, ""))
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990010", "otp": "333333"})
    assert resp.status_code == 404


def test_otp_verify_banned_member_returns_403(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990011")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_c")
    mocker.patch("main._otp_verify", return_value=(True, ""))
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "m-banned", "plan": "free", "status": "banned"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990011", "otp": "444444"})
    assert resp.status_code == 403


def test_otp_verify_valid_returns_token(mocker):
    mocker.patch("utils.security.validate_phone", return_value="+15559990012")
    mocker.patch("utils.security.hash_pii", return_value="hash_phone_d")
    mocker.patch("main._otp_verify", return_value=(True, ""))
    mocker.patch("utils.security.create_token", return_value="jwt-token-ok")
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "m-active", "plan": "free", "status": "active"}
    ]
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)
    client = _client()
    resp = client.post("/auth/otp/verify", json={"phone": "+15559990012", "otp": "555555"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["token"] == "jwt-token-ok"
    assert data["member_id"] == "m-active"
    assert data["plan"] == "free"
