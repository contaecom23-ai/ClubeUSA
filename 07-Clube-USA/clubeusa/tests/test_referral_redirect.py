# tests/test_referral_redirect.py — Phase 0.2 referral redirect
import os
import sys
import pytest

# Env mínima para importar main sem crash
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-chars-long!")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-at-least-32c!")
os.environ.setdefault("ADMIN_SECRET", "test-admin")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app, follow_redirects=False)


class TestReferralRedirect:
    def test_valid_code_redirects_to_home_with_ref(self, client):
        response = client.get("/i/ABCD1234")
        assert response.status_code == 302
        assert response.headers["location"] == "/?ref=ABCD1234"

    def test_code_is_uppercased(self, client):
        response = client.get("/i/abcd1234")
        assert response.status_code == 302
        assert "ABCD1234" in response.headers["location"]

    def test_cookie_is_set(self, client):
        response = client.get("/i/ABCD1234")
        assert "clubeusa_ref" in response.headers.get("set-cookie", "")
        assert "ABCD1234" in response.headers.get("set-cookie", "")

    def test_invalid_code_format_redirects_to_root(self, client):
        # Código com caracteres inválidos → redireciona para /
        response = client.get("/i/INVALID!!")
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_too_short_code_redirects_to_root(self, client):
        response = client.get("/i/AB")
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_too_long_code_redirects_to_root(self, client):
        response = client.get("/i/ABCDEFGHIJKLM")  # 13 chars, limite é 12
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_min_length_code_accepted(self, client):
        response = client.get("/i/ABCD")  # 4 chars — mínimo
        assert response.status_code == 302
        assert "/?ref=ABCD" in response.headers["location"]
