import base64
import hashlib
import hmac
import json
import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

TEST_JWT_SECRET = "test-jwt-secret-for-unit-tests-only"
USER_A_ID = "aaaaaaaa-0000-0000-0000-000000000001"
USER_B_ID = "bbbbbbbb-0000-0000-0000-000000000002"

PROFILE_A = {
    "id": USER_A_ID,
    "full_name": "Ana Souza",
    "city": "Orlando",
    "state_us": "FL",
    "phone": None,
    "referral_code": "abc12345",
    "referred_by_code": None,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

PROFILE_B = {
    "id": USER_B_ID,
    "full_name": "Bruno Lima",
    "city": "Miami",
    "state_us": "FL",
    "phone": None,
    "referral_code": "def67890",
    "referred_by_code": None,
    "created_at": "2026-01-02T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign_jwt(payload: dict, secret: str) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header}.{body}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def make_jwt(user_id: str, email: str = "test@example.com") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return _sign_jwt(payload, TEST_JWT_SECRET)


def make_expired_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "aud": "authenticated",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
    }
    return _sign_jwt(payload, TEST_JWT_SECRET)


@pytest.fixture(autouse=True)
def patch_jwt_secret(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")


@pytest.fixture
def mock_supabase():
    """Mock do cliente Supabase para testes sem conexão real.

    Patch no namespace de routers.profile onde get_supabase_client foi importado,
    evitando importar o pacote supabase (que tem deps quebradas no ambiente de CI).
    """
    mock_client = MagicMock()
    with patch("routers.profile.get_supabase_client", return_value=mock_client):
        yield mock_client


@pytest.fixture
def client(mock_supabase):
    from main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def token_a():
    return make_jwt(USER_A_ID, "ana@test.com")


@pytest.fixture
def token_b():
    return make_jwt(USER_B_ID, "bruno@test.com")
