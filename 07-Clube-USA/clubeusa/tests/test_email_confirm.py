# tests/test_email_confirm.py
"""
Testa o fluxo de confirmacao de email:
- generate_confirm_token retorna token valido
- confirm_email_token marca email como confirmado
- token invalido retorna ValueError
- token ja usado (idempotente) retorna already_confirmed=True
- token expirado retorna ValueError
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


# ============================================================
#  Testes de geracao de token
# ============================================================

def test_generate_confirm_token_format():
    from utils.email import generate_confirm_token
    token = generate_confirm_token()
    # URL-safe base64: apenas letras, digitos, - e _
    assert len(token) >= 40
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=" for c in token)


def test_generate_confirm_token_unique():
    from utils.email import generate_confirm_token
    tokens = {generate_confirm_token() for _ in range(10)}
    assert len(tokens) == 10, "Tokens devem ser unicos"


# ============================================================
#  Testes de send_confirmation_email (sem envio real)
# ============================================================

def test_send_confirmation_email_dev_mode(caplog):
    """Em dev (sem EMAIL_PROVIDER), apenas loga — retorna True."""
    from utils.email import send_confirmation_email
    import logging
    with patch.dict("os.environ", {}, clear=False):
        # Garante que EMAIL_PROVIDER nao esta setado
        import os
        os.environ.pop("EMAIL_PROVIDER", None)
        with caplog.at_level(logging.INFO, logger="email_util"):
            result = send_confirmation_email("test@example.com", "Joao", "TOKEN123")
    assert result is True


def test_send_confirmation_email_sendgrid_missing_key(caplog):
    """SendGrid sem API key loga warning e retorna False."""
    from utils.email import send_confirmation_email
    import logging
    with patch.dict("os.environ", {"EMAIL_PROVIDER": "sendgrid"}, clear=False):
        import os
        os.environ.pop("SENDGRID_API_KEY", None)
        with caplog.at_level(logging.WARNING, logger="email_util"):
            result = send_confirmation_email("test@example.com", "Joao", "TOKEN123")
    assert result is False


# ============================================================
#  Testes de confirm_email_token
# ============================================================

def _make_sb_mock(member_data=None, update_ok=True):
    """Cria mock do Supabase para os testes."""
    sb = MagicMock()
    select_chain = MagicMock()
    select_chain.eq.return_value.execute.return_value.data = member_data or []
    sb.table.return_value.select.return_value = select_chain
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = (
        [{"id": "uuid-123"}] if update_ok else []
    )
    return sb


def test_confirm_email_token_invalid_token():
    """Token vazio ou muito longo levanta ValueError."""
    from services.member_service import confirm_email_token
    with pytest.raises(ValueError, match="invalido"):
        confirm_email_token("")
    with pytest.raises(ValueError, match="invalido"):
        confirm_email_token("x" * 200)


def test_confirm_email_token_not_found():
    """Token nao encontrado no banco levanta ValueError."""
    from services.member_service import confirm_email_token
    with patch("services.member_service._supabase") as mock_sb:
        sb = _make_sb_mock(member_data=[])
        mock_sb.return_value = sb
        with pytest.raises(ValueError, match="invalido"):
            confirm_email_token("VALIDTOKEN")


def test_confirm_email_token_already_confirmed():
    """Token de membro ja confirmado retorna already_confirmed=True (idempotente)."""
    from services.member_service import confirm_email_token
    member = {
        "id": "uuid-123",
        "email_confirmed": True,
        "email_confirm_sent_at": datetime.now(timezone.utc).isoformat(),
    }
    with patch("services.member_service._supabase") as mock_sb:
        sb = _make_sb_mock(member_data=[member])
        mock_sb.return_value = sb
        result = confirm_email_token("VALIDTOKEN")
    assert result["already_confirmed"] is True
    assert result["member_id"] == "uuid-123"


def test_confirm_email_token_expired():
    """Token com mais de 72h levanta ValueError."""
    from services.member_service import confirm_email_token
    old_time = (datetime.now(timezone.utc) - timedelta(hours=73)).isoformat()
    member = {
        "id": "uuid-123",
        "email_confirmed": False,
        "email_confirm_sent_at": old_time,
    }
    with patch("services.member_service._supabase") as mock_sb:
        sb = _make_sb_mock(member_data=[member])
        mock_sb.return_value = sb
        with pytest.raises(ValueError, match="expirado"):
            confirm_email_token("VALIDTOKEN")


def test_confirm_email_token_success():
    """Token valido e nao expirado confirma email e apaga token."""
    from services.member_service import confirm_email_token

    sent_at = datetime.now(timezone.utc).isoformat()
    member = {
        "id": "uuid-123",
        "email_confirmed": False,
        "email_confirm_sent_at": sent_at,
    }

    with patch("services.member_service._supabase") as mock_sb, \
         patch("services.member_service._audit"):
        sb = MagicMock()
        # select chain
        select_mock = MagicMock()
        select_mock.eq.return_value.execute.return_value.data = [member]
        sb.table.return_value.select.return_value = select_mock
        # update chain
        update_mock = MagicMock()
        update_mock.eq.return_value.execute.return_value.data = [{"id": "uuid-123"}]
        sb.table.return_value.update.return_value = update_mock
        mock_sb.return_value = sb

        result = confirm_email_token("VALIDTOKEN")

    assert result["ok"] is True
    assert result["member_id"] == "uuid-123"
    assert result.get("already_confirmed") is False

    # Verifica que o update foi chamado com email_confirmed=True e token=None
    sb.table.return_value.update.assert_called_once_with({
        "email_confirmed":     True,
        "email_confirm_token": None,
    })


# ============================================================
#  Teste de isolamento multi-tenant: token pertence a outro membro
#  (o banco garante uniqueness, mas o service usa o token como chave — sem IDOR)
# ============================================================

def test_confirm_email_token_cross_tenant_safe():
    """
    Token pertencente a membro A nao pode ser usado por membro B.
    O service busca pelo token — quem tem o token, confirma. Sem IDOR.
    """
    from services.member_service import confirm_email_token
    # Se o token nao existir para B, o banco retorna vazio.
    # Aqui simulamos que o token nao existe (banco retorna []).
    with patch("services.member_service._supabase") as mock_sb:
        sb = _make_sb_mock(member_data=[])
        mock_sb.return_value = sb
        with pytest.raises(ValueError):
            confirm_email_token("TOKEN_DE_OUTRO_MEMBRO")
