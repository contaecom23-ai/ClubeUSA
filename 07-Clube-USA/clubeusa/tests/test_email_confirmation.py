# tests/test_email_confirmation.py
"""
Testes para o fluxo de confirmação de email (Fase 0.1).

Cobertos:
- Geração e hash de token
- Envio em dev mode (sem RESEND_API_KEY)
- Endpoint resend-confirmation: membro sem email retorna 400
- Endpoint resend-confirmation: email já confirmado retorna 200 com confirmed=True
- Endpoint confirm: token válido confirma email
- Endpoint confirm: token inválido retorna 400
- Endpoint confirm: token expirado retorna 400
- Perfil expõe email_confirmed
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ---- utils/email_sender ----

def test_generate_email_token_produces_distinct_tokens():
    from utils.email_sender import generate_email_token
    r1, h1 = generate_email_token()
    r2, h2 = generate_email_token()
    assert r1 != r2
    assert h1 != h2
    assert r1 not in (h1, h2)  # raw nunca igual ao hash


def test_hash_token_deterministic():
    from utils.email_sender import hash_token, generate_email_token
    raw, _ = generate_email_token()
    assert hash_token(raw) == hash_token(raw)


def test_send_confirmation_email_dev_mode_returns_true(caplog):
    import logging
    from utils.email_sender import send_confirmation_email
    with patch.dict("os.environ", {}, clear=False):
        # garante que RESEND_API_KEY nao esta definida
        import os; os.environ.pop("RESEND_API_KEY", None)
        with caplog.at_level(logging.INFO, logger="email_sender"):
            result = send_confirmation_email("test@example.com", "rawtoken123", name="João")
    assert result is True
    assert "rawtoken123" in caplog.text


# ---- endpoint: resend-confirmation ----

def _make_member_payload(member_id="m1", plan="free"):
    return {"sub": member_id, "plan": plan}


def _app_with_auth_override(member_payload):
    """Retorna TestClient com get_current_member mockado via dependency_overrides."""
    from fastapi.testclient import TestClient
    import api.main as app_module
    from deps import get_current_member as real_dep

    app_module.app.dependency_overrides[real_dep] = lambda: member_payload
    client = TestClient(app_module.app, raise_server_exceptions=False)
    return client, app_module.app


_TEST_ENV = {"SUPABASE_URL": "http://test", "SUPABASE_SERVICE_KEY": "test-key",
             "ENCRYPTION_KEY": "test-encryption-key-32chars-padding",
             "JWT_SECRET": "test-jwt-secret"}


def test_resend_confirmation_no_email(mocker):
    """Membro sem email cadastrado → 400."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m1", "email_enc": None, "email_confirmed": False,
        "name_enc": None, "language": "pt",
    }]

    with patch.dict("os.environ", _TEST_ENV), \
         patch("supabase.create_client", return_value=mock_sb):
        client, app = _app_with_auth_override(_make_member_payload())
        try:
            resp = client.post("/auth/email/resend-confirmation")
        finally:
            from deps import get_current_member as real_dep
            app.dependency_overrides.pop(real_dep, None)

    assert resp.status_code == 400


def test_resend_confirmation_already_confirmed(mocker):
    """Email já confirmado → 200 com confirmed=True."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m1", "email_enc": "enc", "email_confirmed": True,
        "name_enc": None, "language": "pt",
    }]

    with patch.dict("os.environ", _TEST_ENV), \
         patch("supabase.create_client", return_value=mock_sb):
        client, app = _app_with_auth_override(_make_member_payload())
        try:
            resp = client.post("/auth/email/resend-confirmation")
        finally:
            from deps import get_current_member as real_dep
            app.dependency_overrides.pop(real_dep, None)

    assert resp.status_code == 200
    assert resp.json()["confirmed"] is True


# ---- endpoint: confirm/{token} ----

def test_confirm_email_valid_token(mocker):
    """Token válido → email confirmado, token deletado."""
    from utils.email_sender import generate_email_token
    from fastapi.testclient import TestClient
    import api.main as app_module

    raw, token_hash = generate_email_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok1", "member_id": "m1",
        "expires_at": expires_at,
    }]

    with patch.dict("os.environ", _TEST_ENV), \
         patch("supabase.create_client", return_value=mock_sb):
        client = TestClient(app_module.app, raise_server_exceptions=False)
        resp = client.get(f"/auth/email/confirm/{raw}")

    assert resp.status_code == 200
    assert "confirmado" in resp.text.lower()


def test_confirm_email_invalid_token(mocker):
    """Token não encontrado → 400."""
    from fastapi.testclient import TestClient
    import api.main as app_module

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []

    with patch.dict("os.environ", _TEST_ENV), \
         patch("supabase.create_client", return_value=mock_sb):
        client = TestClient(app_module.app, raise_server_exceptions=False)
        resp = client.get("/auth/email/confirm/tokeninvalido123")

    assert resp.status_code == 400


def test_confirm_email_expired_token(mocker):
    """Token expirado → 400."""
    from fastapi.testclient import TestClient
    import api.main as app_module
    from utils.email_sender import generate_email_token

    raw, _ = generate_email_token()
    expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "tok1", "member_id": "m1",
        "expires_at": expires_at,
    }]

    with patch.dict("os.environ", _TEST_ENV), \
         patch("supabase.create_client", return_value=mock_sb):
        client = TestClient(app_module.app, raise_server_exceptions=False)
        resp = client.get(f"/auth/email/confirm/{raw}")

    assert resp.status_code == 400
    assert "expirado" in resp.json()["detail"].lower()


# ---- member profile: email_confirmed ----

def test_get_member_profile_exposes_email_confirmed(mocker):
    from services.member_service import get_member_profile

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id": "m1",
        "phone_enc": "enc_phone",
        "email_enc": "enc_email",
        "email_confirmed": True,
        "name_enc": "enc_name",
        "language": "pt",
        "state": "FL",
        "plan": "free",
        "points": 100,
        "level": "bronze",
        "categories": ["all"],
        "referral_code": "ABC123",
        "referral_count": 2,
        "total_clicks": 5,
        "created_at": "2026-01-01T00:00:00",
        "vip_expires_at": None,
    }]

    with patch("services.member_service._supabase", return_value=mock_sb):
        with patch("services.member_service.decrypt", return_value="fake_value"):
            profile = get_member_profile("m1")

    assert profile is not None
    assert profile["email_confirmed"] is True
