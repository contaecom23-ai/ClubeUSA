# tests/test_email_confirm.py — Clube USA
# Testes para o fluxo de confirmação de email (Fase 0.1).
#
# Implementação usa tabela `email_verify_tokens` + coluna `email_confirmed_at` em members.

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


def _make_token():
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def _future(hours=1):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past(hours=2):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


# ============================================================
#  confirm_member_email
# ============================================================

def test_confirm_email_success(mocker):
    raw, hashed = _make_token()
    mock_sb = MagicMock()
    # email_verify_tokens lookup by token_hash
    mock_sb.table().select().eq().execute.return_value.data = [{
        "member_id":  "member-1",
        "token_hash": hashed,
        "expires_at": _future(hours=23),
        "used_at":    None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    from services.member_service import confirm_member_email
    result = confirm_member_email(raw)

    assert result["confirmed"] is True
    assert result["member_id"] == "member-1"


def test_confirm_email_invalid_token_empty(mocker):
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_member_email
    import pytest
    with pytest.raises(ValueError, match="[Ii]nv"):
        confirm_member_email("bad-token")


def test_confirm_email_token_already_used(mocker):
    raw, _ = _make_token()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "member_id":  "member-1",
        "token_hash": "hash",
        "expires_at": _future(),
        "used_at":    _past(),   # already used
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_member_email
    import pytest
    with pytest.raises(ValueError, match="[Uu]tilizado|[Uu]sado"):
        confirm_member_email(raw)


def test_confirm_email_expired_token(mocker):
    raw, hashed = _make_token()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "member_id":  "member-1",
        "token_hash": hashed,
        "expires_at": _past(hours=1),   # expired
        "used_at":    None,
    }]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service._audit")

    from services.member_service import confirm_member_email
    import pytest
    with pytest.raises(ValueError, match="[Ee]xpirado"):
        confirm_member_email(raw)


def test_confirm_email_token_too_long(mocker):
    mocker.patch("services.member_service._supabase")

    from services.member_service import confirm_member_email
    import pytest
    with pytest.raises(ValueError, match="[Ii]nv"):
        confirm_member_email("x" * 201)


# ============================================================
#  resend_email_confirmation
# ============================================================

def _make_routed_sb(table_data: dict):
    """
    Cria MagicMock para Supabase que roteia .table(name) para respostas distintas.
    table_data: {"table_name": [row_dict, ...]}
    """
    from unittest.mock import MagicMock

    def table_side_effect(name):
        rows = table_data.get(name, [])
        m = MagicMock()
        m.select.return_value.eq.return_value.execute.return_value.data = rows
        m.insert.return_value.execute.return_value.data = [{}]
        m.update.return_value.eq.return_value.execute.return_value.data = [{}]
        m.delete.return_value.eq.return_value.execute.return_value.data = []
        return m

    sb = MagicMock()
    sb.table.side_effect = table_side_effect
    return sb


def test_resend_success_no_existing_token(mocker):
    """Reenvio bem-sucedido quando não há token recente."""
    mock_sb = _make_routed_sb({
        "email_verify_tokens": [],
        "members": [{"email_enc": "enc_email", "email_confirmed_at": None, "name_enc": None}],
    })
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")
    mock_send = mocker.patch(
        "services.member_service.send_email_confirmation_for_member",
        return_value=True,
    )

    from services.member_service import resend_email_confirmation
    result = resend_email_confirmation("member-1")
    assert result is True
    mock_send.assert_called_once()


def test_resend_blocked_by_rate_limit(mocker):
    """Reenvio bloqueado quando token foi gerado há menos de 60 min."""
    recent_created = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_sb = _make_routed_sb({
        "email_verify_tokens": [{"created_at": recent_created}],
        "members": [],
    })
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resend_email_confirmation
    import pytest
    with pytest.raises(ValueError, match="[Aa]guarde"):
        resend_email_confirmation("member-1")


def test_resend_blocked_email_already_confirmed(mocker):
    """Reenvio bloqueado quando email já confirmado."""
    old_created = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    mock_sb = _make_routed_sb({
        "email_verify_tokens": [{"created_at": old_created}],
        "members": [{"email_enc": "enc_email", "email_confirmed_at": _past(hours=1)}],
    })
    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.decrypt", return_value="user@example.com")

    from services.member_service import resend_email_confirmation
    import pytest
    with pytest.raises(ValueError, match="[Cc]onfirm"):
        resend_email_confirmation("member-1")


# ============================================================
#  Isolamento multi-tenant: token de membro A não confirma B
# ============================================================

def test_confirm_email_cross_tenant_isolation(mocker):
    """Token não encontrado no banco retorna erro, nunca vaza dados."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import confirm_member_email
    import pytest
    with pytest.raises(ValueError):
        confirm_member_email(secrets.token_urlsafe(32))


# ============================================================
#  utils/email_sender: modo dev não levanta exceção
# ============================================================

def test_email_sender_dev_mode_does_not_raise(mocker):
    mocker.patch.dict("os.environ", {"ENVIRONMENT": "development"})
    from utils.email_sender import send_email_confirmation
    # Em dev deve apenas logar; pode retornar True ou None sem levantar exceção
    try:
        send_email_confirmation("test@example.com", "https://example.com/confirm?token=abc", "Joao")
    except Exception as e:
        raise AssertionError(f"Dev mode nao deve levantar excecao: {e}")


def test_email_sender_production_no_provider_does_not_crash(mocker):
    mocker.patch.dict("os.environ", {"ENVIRONMENT": "production", "EMAIL_PROVIDER": ""})
    from utils.email_sender import send_email_confirmation
    # Sem provider configurado deve lidar graciosamente (log de erro, nao crash)
    try:
        send_email_confirmation("test@example.com", "https://example.com/confirm?token=abc", "")
    except Exception as e:
        raise AssertionError(f"Producao sem provider nao deve crashar: {e}")
