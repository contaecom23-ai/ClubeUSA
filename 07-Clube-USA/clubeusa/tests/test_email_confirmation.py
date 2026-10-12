# tests/test_email_confirmation.py — Clube USA
# Testa o fluxo de verificacao de email (FASE 0.1)

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ============================================================
#  email_service — testes unitarios
# ============================================================

def test_send_verification_email_dev_mode(caplog):
    """Em dev (sem SMTP_HOST), nao envia email mas loga o link."""
    from services.email_service import send_verification_email
    import logging
    with patch.dict("os.environ", {}, clear=False):
        # garante que SMTP_HOST nao esta definido
        import os
        os.environ.pop("SMTP_HOST", None)
        with caplog.at_level(logging.INFO, logger="email_service"):
            result = send_verification_email("test@example.com", "token-abc", "pt")
    assert result is True
    assert "token-abc" in caplog.text


def test_send_verification_email_pt_content():
    """Conteudo do email em portugues contem campos corretos."""
    from services.email_service import _build_verification_content
    url = "https://clubeusa.com/auth/email/verify/xyz"
    subject, html, text = _build_verification_content("pt", url)
    assert "Clube USA" in subject
    assert url in html
    assert url in text
    assert "24 horas" in text


def test_send_verification_email_es_content():
    """Conteudo do email em espanhol contem campos corretos."""
    from services.email_service import _build_verification_content
    url = "https://clubeusa.com/auth/email/verify/xyz"
    subject, html, text = _build_verification_content("es", url)
    assert "Club USA" in subject
    assert url in html
    assert "24 horas" in text


# ============================================================
#  auth_email router — testes de integracao com mocks
# ============================================================

def _make_sb_mock(member_data=None, update_data=None):
    """Helper para criar mock do Supabase."""
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        member_data if member_data is not None else []
    )
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = (
        update_data or [{}]
    )
    sb.table.return_value.insert.return_value.execute.return_value.data = [{}]
    return sb


def test_request_verification_no_email(mocker):
    """Erro 400 se membro nao tem email cadastrado."""
    from routers.auth_email import request_email_verification
    import asyncio
    from fastapi import HTTPException

    sb = _make_sb_mock(member_data=[{"id": "m1", "email_enc": None, "email_confirmed": False, "language": "pt"}])
    mocker.patch("routers.auth_email._supabase", return_value=sb)

    member = {"sub": "m1"}
    with pytest.raises(HTTPException) as exc_info:
        asyncio.get_event_loop().run_until_complete(request_email_verification(member))
    assert exc_info.value.status_code == 400


def test_request_verification_already_confirmed(mocker):
    """Retorna already_confirmed=True se email ja esta verificado."""
    from routers.auth_email import request_email_verification
    import asyncio

    sb = _make_sb_mock(member_data=[{"id": "m1", "email_enc": "enc_data", "email_confirmed": True, "language": "pt"}])
    mocker.patch("routers.auth_email._supabase", return_value=sb)

    member = {"sub": "m1"}
    result = asyncio.get_event_loop().run_until_complete(request_email_verification(member))
    assert result["already_confirmed"] is True


def test_request_verification_sends_email(mocker):
    """Fluxo normal: gera token e envia email."""
    from routers.auth_email import request_email_verification
    import asyncio

    sb = _make_sb_mock(member_data=[{"id": "m1", "email_enc": "enc_data", "email_confirmed": False, "language": "pt"}])
    mocker.patch("routers.auth_email._supabase", return_value=sb)
    mocker.patch("utils.security.decrypt", return_value="user@example.com")
    mock_send = mocker.patch("services.email_service.send_verification_email", return_value=True)

    member = {"sub": "m1"}
    result = asyncio.get_event_loop().run_until_complete(request_email_verification(member))
    assert result["expires_in_hours"] == 24
    mock_send.assert_called_once()


def test_confirm_email_invalid_token(mocker):
    """Link com token desconhecido retorna pagina de erro."""
    from routers.auth_email import confirm_email
    import asyncio

    sb = _make_sb_mock(member_data=[])  # token nao encontrado
    mocker.patch("routers.auth_email._supabase", return_value=sb)

    response = asyncio.get_event_loop().run_until_complete(confirm_email("token-invalido"))
    # confirm_email retorna string HTML diretamente
    body = response if isinstance(response, str) else response.body.decode()
    assert "invalido" in body.lower() or "invalid" in body.lower()


def test_confirm_email_expired_token(mocker):
    """Link expirado retorna pagina de link expirado."""
    from routers.auth_email import confirm_email
    import asyncio

    expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    sb = _make_sb_mock(member_data=[{
        "id": "m1",
        "email_token_expires_at": expired_time,
        "email_confirmed": False,
        "language": "pt",
    }])
    mocker.patch("routers.auth_email._supabase", return_value=sb)

    response = asyncio.get_event_loop().run_until_complete(confirm_email("token-expirado"))
    body = response if isinstance(response, str) else response.body.decode()
    assert "expirado" in body.lower() or "expired" in body.lower()


def test_confirm_email_success(mocker):
    """Link valido confirma email e retorna pagina de sucesso."""
    from routers.auth_email import confirm_email
    import asyncio

    valid_time = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
    sb = _make_sb_mock(member_data=[{
        "id": "m1",
        "email_token_expires_at": valid_time,
        "email_confirmed": False,
        "language": "pt",
    }])
    mocker.patch("routers.auth_email._supabase", return_value=sb)

    response = asyncio.get_event_loop().run_until_complete(confirm_email("token-valido"))
    body = response if isinstance(response, str) else response.body.decode()
    assert "confirmado" in body.lower()


# ============================================================
#  member_service — email_confirmed no perfil
# ============================================================

def test_profile_includes_email_confirmed(mocker):
    """get_member_profile retorna campo email_confirmed."""
    from services.member_service import get_member_profile

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "m1",
        "name_enc": None,
        "phone_enc": "enc",
        "email_enc": "enc_email",
        "email_confirmed": False,
        "language": "pt",
        "state": "FL",
        "plan": "free",
        "points": 100,
        "level": "bronze",
        "categories": ["all"],
        "referral_code": "ABC123",
        "referral_count": 0,
        "total_clicks": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=sb)
    mocker.patch("services.member_service.decrypt", return_value="+15551234567")

    profile = get_member_profile("m1")
    assert "email_confirmed" in profile
    assert profile["email_confirmed"] is False


def test_profile_email_confirmed_none_when_no_email(mocker):
    """email_confirmed deve ser None quando membro nao tem email."""
    from services.member_service import get_member_profile

    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": "m1",
        "name_enc": None,
        "phone_enc": "enc",
        "email_enc": None,  # sem email
        "email_confirmed": False,
        "language": "pt",
        "state": None,
        "plan": "free",
        "points": 100,
        "level": "bronze",
        "categories": ["all"],
        "referral_code": "XYZ789",
        "referral_count": 0,
        "total_clicks": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "vip_expires_at": None,
    }]
    mocker.patch("services.member_service._supabase", return_value=sb)
    mocker.patch("services.member_service.decrypt", return_value="+15551234567")

    profile = get_member_profile("m1")
    assert profile["email_confirmed"] is None  # sem email = nao aplicavel
