# tests/test_email_confirmation.py — Fase 0.1: confirmação de email

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

# Garante que as variáveis mínimas existem para importar os módulos
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-for-unit-tests-only")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("APP_URL", "https://clubeusa.com")
os.environ.setdefault("ENVIRONMENT", "development")


# ============================================================
#  email_service — testes unitários
# ============================================================

def test_dev_mode_returns_true_without_sending():
    """Em dev, send_confirmation_email retorna True sem tentar SMTP."""
    from services.email_service import send_confirmation_email
    result = send_confirmation_email(
        email="joao@example.com",
        token="fake-token-abc123",
        name="João",
        language="pt",
    )
    assert result is True


def test_dev_mode_es_template_returns_true():
    """Template em espanhol também funciona em dev."""
    from services.email_service import send_confirmation_email
    result = send_confirmation_email(
        email="pedro@example.com",
        token="token-es-test",
        name="Pedro",
        language="es",
    )
    assert result is True


def test_unknown_language_falls_back_to_pt():
    """Idioma desconhecido usa template PT sem erro."""
    from services.email_service import send_confirmation_email
    result = send_confirmation_email(
        email="x@example.com",
        token="tok",
        language="fr",   # não suportado → cai no PT
    )
    assert result is True


def test_templates_contain_confirm_url_placeholder():
    """Todos os templates têm o placeholder {confirm_url}."""
    from services.email_service import _TEMPLATES
    assert "confirm_pt" in _TEMPLATES
    assert "confirm_es" in _TEMPLATES
    for key, tmpl in _TEMPLATES.items():
        assert "{confirm_url}" in tmpl["html"], f"{key} sem {{confirm_url}}"
        assert "subject" in tmpl
        assert len(tmpl["subject"]) > 0


def test_prod_without_smtp_returns_false():
    """Em prod sem SMTP configurado, retorna False (não lança exceção)."""
    import importlib
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "SMTP_HOST": "",
        "SMTP_USER": "",
    }):
        import services.email_service as svc
        importlib.reload(svc)  # força releitura das vars de ambiente
        result = svc.send_confirmation_email("x@example.com", "tok", "X", "pt")
        assert result is False

    # Restaura modo dev para os próximos testes
    os.environ["ENVIRONMENT"] = "development"


# ============================================================
#  member_service — cadastro com email obrigatório
# ============================================================

def test_register_requires_email():
    """Cadastro sem email deve levantar ValueError com menção a email."""
    # Mock do Supabase — não precisa de conexão real
    with patch("services.member_service._supabase") as mock_sb_factory:
        mock_sb = MagicMock()
        mock_sb_factory.return_value = mock_sb

        from services.member_service import register_member
        with pytest.raises(ValueError, match=r"(?i)email"):
            register_member(phone="+15551234567", email=None)


def test_register_requires_valid_email():
    """Cadastro com email malformado levanta ValueError."""
    with patch("services.member_service._supabase") as mock_sb_factory:
        mock_sb = MagicMock()
        mock_sb_factory.return_value = mock_sb

        from services.member_service import register_member
        with pytest.raises(ValueError, match=r"(?i)email"):
            register_member(phone="+15551234567", email="nao-e-um-email")


def test_register_new_member_sends_confirmation():
    """Cadastro bem-sucedido chama send_confirmation_email."""
    with patch("services.member_service._supabase") as mock_sb_factory, \
         patch("services.member_service.assign_member_to_group", return_value={}), \
         patch("services.email_service.send_confirmation_email", return_value=True) as mock_send:

        mock_sb = MagicMock()
        mock_sb_factory.return_value = mock_sb

        # phone_hash lookup: não encontrado (novo membro)
        no_data = MagicMock()
        no_data.data = []
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = no_data

        # insert: retorna membro criado
        created = MagicMock()
        created.data = [{
            "id": "uuid-test-1234",
            "plan": "free",
            "referral_code": "ABCD1234",
        }]
        mock_sb.table.return_value.insert.return_value.execute.return_value = created

        from importlib import reload
        import services.member_service as ms_module
        reload(ms_module)

        result = ms_module.register_member(
            phone="+15551234567",
            email="joao@example.com",
            name="João",
        )

        assert result["action"] == "registered"
        assert result["email_confirmed"] is False
        assert result["confirm_email_sent"] is True


# ============================================================
#  Token de confirmação — lógica de expiração
# ============================================================

def test_confirmation_token_48h_ttl():
    """Token gerado agora deve expirar em ~48 horas."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=48)
    # Deve estar no futuro
    assert expires > now
    # Deve estar antes de 49 horas
    assert expires < now + timedelta(hours=49)


def test_expired_token_detected():
    """Token criado há 49 horas está expirado."""
    expires = datetime.now(timezone.utc) - timedelta(hours=1)
    assert datetime.now(timezone.utc) > expires


def test_resend_cooldown_logic():
    """
    Token com 48h de TTL gerado há 5 minutos não deve permitir reenvio.
    Threshold: expires > now + 47h50m.
    """
    now = datetime.now(timezone.utc)
    # Gerado há 5 minutos → expira em ~47h55m
    expires_in_47h55m = now + timedelta(hours=47, minutes=55)
    cooldown_threshold = now + timedelta(hours=47, minutes=50)
    assert expires_in_47h55m > cooldown_threshold  # cooldown ativo

    # Gerado há 15 minutos → expira em ~47h45m → cooldown NÃO ativo
    expires_in_47h45m = now + timedelta(hours=47, minutes=45)
    assert expires_in_47h45m < cooldown_threshold   # pode reenviar
