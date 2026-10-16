import pytest
from unittest.mock import MagicMock, patch
import os


@pytest.fixture
def client(mocker):
    """FastAPI TestClient com Supabase mockado."""
    os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-real")
    os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzLXBhZGRpbmc=")
    os.environ.setdefault("ENVIRONMENT", "test")

    from fastapi.testclient import TestClient
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

    with patch("supabase.create_client"):
        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)
        return TestClient(main_mod.app, raise_server_exceptions=False)


def test_referral_redirect_valid_code(mocker):
    """Código válido deve redirecionar para /?ref=CODE e setar cookie."""
    os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-real")
    os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzLXBhZGRpbmc=")
    os.environ.setdefault("ENVIRONMENT", "test")

    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = [{"id": "uuid-member-1"}]

    with patch("supabase.create_client", return_value=mock_sb):
        from fastapi.testclient import TestClient
        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)
        tc = TestClient(main_mod.app, raise_server_exceptions=False, follow_redirects=False)

        resp = tc.get("/i/ABCD1234")
        assert resp.status_code == 302
        assert resp.headers["location"] == "/?ref=ABCD1234"
        assert "clubeusa_ref" in resp.cookies


def test_referral_redirect_invalid_code(mocker):
    """Código com formato inválido redireciona para / sem cookie."""
    os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-real")
    os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzLXBhZGRpbmc=")
    os.environ.setdefault("ENVIRONMENT", "test")

    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

    mock_sb = MagicMock()

    with patch("supabase.create_client", return_value=mock_sb):
        from fastapi.testclient import TestClient
        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)
        tc = TestClient(main_mod.app, raise_server_exceptions=False, follow_redirects=False)

        resp = tc.get("/i/!!invalid!!")
        assert resp.status_code == 302
        assert "ref=" not in resp.headers.get("location", "")


def test_referral_redirect_nonexistent_code(mocker):
    """Código com formato válido mas não encontrado no DB redireciona para /."""
    os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-service-key")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-real")
    os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzLXBhZGRpbmc=")
    os.environ.setdefault("ENVIRONMENT", "test")

    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []

    with patch("supabase.create_client", return_value=mock_sb):
        from fastapi.testclient import TestClient
        import importlib
        import api.main as main_mod
        importlib.reload(main_mod)
        tc = TestClient(main_mod.app, raise_server_exceptions=False, follow_redirects=False)

        resp = tc.get("/i/ZZZZ9999")
        assert resp.status_code == 302
        assert "ref=" not in resp.headers.get("location", "")
        assert "clubeusa_ref" not in resp.cookies
