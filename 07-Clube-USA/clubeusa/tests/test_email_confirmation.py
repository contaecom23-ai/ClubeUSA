# tests/test_email_confirmation.py
# FASE 0.1 — testes de confirmação de email

from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sb_mock(member_rows=None, update_ok=True):
    """Cria mock de Supabase com comportamento configurável."""
    sb = MagicMock()
    sb.table().select().eq().execute.return_value.data = member_rows or []
    if update_ok:
        sb.table().update().eq().execute.return_value.data = [{"id": "m-1"}]
    return sb


# ---------------------------------------------------------------------------
# confirm_email
# ---------------------------------------------------------------------------

def test_confirm_email_valid_token(mocker):
    from services.member_service import confirm_email

    future = (datetime.utcnow() + timedelta(hours=23)).isoformat()
    member = {"id": "m-1", "email_confirmed": False, "email_confirm_expires_at": future}
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)
    mocker.patch("services.member_service._audit")

    result = confirm_email("valid-token-abc")
    assert result["confirmed"] is True
    assert "already" not in result


def test_confirm_email_already_confirmed(mocker):
    from services.member_service import confirm_email

    member = {"id": "m-1", "email_confirmed": True, "email_confirm_expires_at": None}
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = confirm_email("already-used-token")
    assert result["confirmed"] is True
    assert result.get("already") is True


def test_confirm_email_expired_token(mocker):
    from services.member_service import confirm_email

    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    member = {"id": "m-1", "email_confirmed": False, "email_confirm_expires_at": past}
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = confirm_email("expired-token")
    assert result["confirmed"] is False
    assert result.get("expired") is True


def test_confirm_email_not_found(mocker):
    from services.member_service import confirm_email

    sb = _make_sb_mock(member_rows=[])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = confirm_email("nonexistent-token")
    assert result["confirmed"] is False


def test_confirm_email_empty_token(mocker):
    from services.member_service import confirm_email

    result = confirm_email("")
    assert result["confirmed"] is False


def test_confirm_email_oversized_token(mocker):
    from services.member_service import confirm_email

    result = confirm_email("x" * 500)
    assert result["confirmed"] is False


# ---------------------------------------------------------------------------
# resend_confirmation
# ---------------------------------------------------------------------------

def test_resend_confirmation_success(mocker):
    from services.member_service import resend_confirmation

    # Expirado há 10 minutos (além do cooldown de 5 min)
    past_expires = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    member = {
        "id": "m-1",
        "email_enc": "encrypted_email",
        "email_confirmed": False,
        "email_confirm_expires_at": past_expires,
        "name_enc": "encrypted_name",
    }
    sb = MagicMock()
    # Primeiro select retorna o membro
    sb.table().select().eq().execute.return_value.data = [member]
    sb.table().update().eq().execute.return_value.data = [{"id": "m-1"}]
    mocker.patch("services.member_service._supabase", return_value=sb)
    mocker.patch("services.member_service.decrypt", side_effect=lambda x: x)
    mocker.patch("services.member_service._audit")
    mocker.patch("utils.email.send_confirmation_email")

    result = resend_confirmation("m-1")
    assert result["sent"] is True


def test_resend_confirmation_already_confirmed(mocker):
    from services.member_service import resend_confirmation

    member = {"id": "m-1", "email_enc": "enc", "email_confirmed": True, "email_confirm_expires_at": None}
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = resend_confirmation("m-1")
    assert result["sent"] is False
    assert result["reason"] == "already_confirmed"


def test_resend_confirmation_no_email(mocker):
    from services.member_service import resend_confirmation

    member = {"id": "m-1", "email_enc": None, "email_confirmed": False, "email_confirm_expires_at": None}
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = resend_confirmation("m-1")
    assert result["sent"] is False
    assert result["reason"] == "no_email"


def test_resend_confirmation_cooldown(mocker):
    from services.member_service import resend_confirmation
    from services.member_service import EMAIL_TOKEN_TTL_HOURS, RESEND_COOLDOWN_MINUTES

    # Token criado 2 minutos atrás (dentro do cooldown de 5 min)
    recent_expires = (datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_TTL_HOURS) - timedelta(minutes=2)).isoformat()
    member = {
        "id": "m-1",
        "email_enc": "enc",
        "email_confirmed": False,
        "email_confirm_expires_at": recent_expires,
    }
    sb = _make_sb_mock(member_rows=[member])
    mocker.patch("services.member_service._supabase", return_value=sb)

    result = resend_confirmation("m-1")
    assert result["sent"] is False
    assert result["reason"] == "cooldown"
    assert result["retry_in_seconds"] > 0


# ---------------------------------------------------------------------------
# register_member — verifica que email_confirmed=False é salvo ao cadastrar
# ---------------------------------------------------------------------------

def test_register_member_stores_email_confirmed_false(mocker):
    from services.member_service import register_member

    sb = MagicMock()
    # Sem membro existente
    sb.table().select().eq().execute.return_value.data = []
    # Insert retorna membro criado
    sb.table().insert().execute.return_value.data = [{
        "id": "m-new",
        "plan": "free",
        "referral_code": "ABCD1234",
        "email_confirmed": False,
    }]
    mocker.patch("services.member_service._supabase", return_value=sb)
    mocker.patch("services.member_service.validate_phone", return_value="+15551234567")
    mocker.patch("services.member_service.validate_email", return_value="test@example.com")
    mocker.patch("services.member_service.encrypt", side_effect=lambda x: f"enc({x})")
    mocker.patch("services.member_service.hash_pii", return_value="hashed")
    mocker.patch("services.member_service.generate_referral_code", return_value="ABCD1234")
    mocker.patch("services.member_service.create_token", return_value="jwt-token")
    mocker.patch("services.member_service.sanitize", side_effect=lambda x, _: x)
    mocker.patch("services.group_manager.assign_member_to_group", return_value={})
    mocker.patch("services.member_service._audit")
    mocker.patch("utils.email.send_confirmation_email")

    result = register_member("+15551234567", email="test@example.com")

    # Verifica que a chamada insert incluiu email_confirmed: False
    insert_call_args = sb.table().insert.call_args
    if insert_call_args:
        inserted_data = insert_call_args[0][0] if insert_call_args[0] else insert_call_args[1].get("json", {})
        assert inserted_data.get("email_confirmed") is False
        assert "email_confirm_token" in inserted_data

    assert result["email_confirmed"] is False
    assert result["email_pending"] is True
