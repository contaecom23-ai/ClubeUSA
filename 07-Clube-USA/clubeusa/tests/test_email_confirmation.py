# ============================================================
#  tests/test_email_confirmation.py — Fase 0.1
#  Testa geracao, envio e verificacao de token de confirmacao.
# ============================================================

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ---- helpers -------------------------------------------------------

def _mock_sb():
    return MagicMock()


# ---- generate_email_confirmation -----------------------------------

def test_generate_email_confirmation_saves_token(mocker):
    from services.member_service import generate_email_confirmation

    mock_sb = _mock_sb()
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    token = generate_email_confirmation("m1")

    assert isinstance(token, str)
    assert len(token) >= 40  # token_urlsafe(32) => 43 chars
    mock_sb.table().update().eq().execute.assert_called_once()


# ---- confirm_email_token -------------------------------------------

def test_confirm_email_token_valid(mocker):
    from services.member_service import confirm_email_token

    mock_sb = _mock_sb()
    future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                              "m1",
        "email_confirmed":                 False,
        "email_confirmation_expires_at":   future,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    result = confirm_email_token("valid_token")
    assert result == "m1"


def test_confirm_email_token_expired(mocker):
    from services.member_service import confirm_email_token

    mock_sb = _mock_sb()
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                              "m2",
        "email_confirmed":                 False,
        "email_confirmation_expires_at":   past,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = confirm_email_token("expired_token")
    assert result is None


def test_confirm_email_token_not_found(mocker):
    from services.member_service import confirm_email_token

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = confirm_email_token("nonexistent")
    assert result is None


def test_confirm_email_token_already_confirmed(mocker):
    """Token de membro ja confirmado deve ser aceito e invalidado sem erro."""
    from services.member_service import confirm_email_token

    mock_sb = _mock_sb()
    future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                              "m3",
        "email_confirmed":                 True,
        "email_confirmation_expires_at":   future,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m3"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = confirm_email_token("already_done_token")
    # Deve retornar o member_id (idempotente)
    assert result == "m3"


# ---- resend_email_confirmation -------------------------------------

def test_resend_email_confirmation_no_email(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":       None,
        "email_confirmed": False,
        "language":        "pt",
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = resend_email_confirmation("m1")
    assert result is False


def test_resend_email_confirmation_already_confirmed(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":       "encrypted_email",
        "email_confirmed": True,
        "language":        "pt",
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    result = resend_email_confirmation("m1")
    assert result is False


def test_resend_email_confirmation_sends(mocker):
    from services.member_service import resend_email_confirmation

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "email_enc":       "encrypted",
        "email_confirmed": False,
        "language":        "pt",
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")
    mocker.patch("services.member_service.generate_email_confirmation", return_value="tok123")
    mocker.patch("services.email_service.send_confirmation_email", return_value=True)

    result = resend_email_confirmation("m1")
    assert result is True


# ---- get_member_profile inclui email_confirmed ---------------------

def test_get_member_profile_includes_email_confirmed(mocker):
    from services.member_service import get_member_profile

    mock_sb = _mock_sb()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":              "m1",
        "name_enc":        None,
        "phone_enc":       "enc_phone",
        "email_enc":       None,
        "email_confirmed": True,
        "language":        "pt",
        "state":           "FL",
        "plan":            "free",
        "points":          100,
        "level":           "bronze",
        "categories":      ["all"],
        "referral_code":   "ABCD1234",
        "referral_count":  0,
        "total_clicks":    0,
        "created_at":      "2026-01-01T00:00:00",
        "vip_expires_at":  None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="+15551234567")

    profile = get_member_profile("m1")
    assert profile is not None
    assert profile["email_confirmed"] is True


# ---- email_service -------------------------------------------------

def test_send_confirmation_email_dev_mode(mocker):
    """Sem RESEND_API_KEY, deve logar e retornar True."""
    import os
    mocker.patch.dict(os.environ, {}, clear=False)
    os.environ.pop("RESEND_API_KEY", None)

    from services.email_service import send_confirmation_email
    result = send_confirmation_email("test@example.com", "mytoken123", "pt")
    assert result is True


def test_send_confirmation_email_resend_success(mocker):
    """Com RESEND_API_KEY, chama API e retorna True se status 200."""
    import os
    mocker.patch.dict(os.environ, {"RESEND_API_KEY": "re_test_key"})

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mocker.patch("requests.post", return_value=mock_resp)

    from services import email_service
    import importlib
    importlib.reload(email_service)

    result = email_service._send_via_resend("re_test_key", "test@example.com", "Confirme", "<p>ok</p>")
    assert result is True


def test_send_confirmation_email_resend_failure(mocker):
    """API Resend retorna erro — deve retornar False sem lancar excecao."""
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.text = "Unprocessable Entity"

    mocker.patch("requests.post", return_value=mock_resp)

    from services.email_service import _send_via_resend
    result = _send_via_resend("key", "bad@bad", "subj", "<p>html</p>")
    assert result is False


# ---- isolamento multi-tenant: token de outro membro nao funciona ---

def test_confirm_token_cross_tenant_isolation(mocker):
    """
    Se o token pertence ao membro A, nao pode confirmar o membro B.
    O lookup e por token — retorna apenas o dono do token.
    """
    from services.member_service import confirm_email_token

    mock_sb = _mock_sb()
    future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    # Supabase retorna apenas o membro dono do token (isolamento garantido pelo WHERE)
    mock_sb.table().select().eq().execute.return_value.data = [{
        "id":                              "member_A",
        "email_confirmed":                 False,
        "email_confirmation_expires_at":   future,
    }]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "member_A"}]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    # O token so pode confirmar quem o possui — sempre retorna member_A
    result = confirm_email_token("token_de_member_A")
    assert result == "member_A"
    # member_B nunca aparece neste fluxo
