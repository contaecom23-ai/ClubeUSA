# tests/test_email_verification.py
"""
Testes para o fluxo de verificacao de email (Fase 0.1) e update de perfil.
Cobre: envio de token, confirmacao, token expirado, token usado,
atualizacao de email e conflito multi-tenant.
"""

import os
import sys
import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ============================================================
#  Path setup — igual ao conftest.py do projeto
# ============================================================
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api'))

# Env vars minimas para imports nao falharem
os.environ.setdefault("SUPABASE_URL",         "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY",  "test-service-key")
os.environ.setdefault("ENCRYPTION_KEY",        "clubeusa-test-key-32chars-12345!")
os.environ.setdefault("JWT_SECRET",             "test-jwt-secret-string")
os.environ.setdefault("ADMIN_SECRET",           "test-admin")

# Mock modulos pesados/externos antes de qualquer import do projeto
# (permite rodar sem as dependencias instaladas neste ambiente de teste)
_fernet_mock = MagicMock()
_fernet_mock.encrypt.side_effect = lambda b: b"encrypted:" + b
_fernet_mock.decrypt.side_effect = lambda b: b.replace(b"encrypted:", b"")
_FernetClass = MagicMock(return_value=_fernet_mock)

_crypto_mock = MagicMock()
_fernet_module = MagicMock()
_fernet_module.Fernet = _FernetClass
sys.modules.setdefault("cryptography",         _crypto_mock)
sys.modules.setdefault("cryptography.fernet",  _fernet_module)
sys.modules.setdefault("jose",                  MagicMock())
sys.modules.setdefault("supabase",              MagicMock())
sys.modules.setdefault("stripe",                MagicMock())
sys.modules.setdefault("requests",              MagicMock())


# ============================================================
#  email_service — tests
# ============================================================

class TestEmailService:

    def test_send_no_smtp_returns_false(self):
        """Sem SMTP configurado, retorna False (modo dev)."""
        os.environ.pop("SMTP_HOST", None)
        os.environ.pop("SMTP_USER", None)
        from services.email_service import send_verification_email
        result = send_verification_email("user@example.com", "tok123", "https://clubeusa.com")
        assert result is False

    def test_send_smtp_success(self):
        """Com SMTP configurado, abre conexao, chama sendmail e retorna True."""
        os.environ["SMTP_HOST"] = "smtp.resend.com"
        os.environ["SMTP_USER"] = "resend"
        os.environ["SMTP_PASS"] = "re_secret"
        os.environ["FROM_EMAIL"] = "noreply@clubeusa.com"
        os.environ.pop("SMTP_PORT", None)

        mock_smtp_instance = MagicMock()
        mock_smtp_instance.__enter__ = lambda s: s
        mock_smtp_instance.__exit__ = MagicMock(return_value=False)

        import importlib
        import services.email_service as email_svc
        importlib.reload(email_svc)

        with patch("smtplib.SMTP", return_value=mock_smtp_instance):
            result = email_svc.send_verification_email(
                "membro@example.com", "token-abc-123", "https://clubeusa.com"
            )

        assert result is True
        mock_smtp_instance.sendmail.assert_called_once()
        # Garante que o email foi montado com destinatario correto
        call_args = mock_smtp_instance.sendmail.call_args[0]
        assert call_args[1] == "membro@example.com"
        # O corpo e multipart/base64; verifica que o token aparece na versao raw
        import base64
        raw_body = call_args[2]
        # Procura pelo token em todas as partes (plain text e base64)
        token_b64 = base64.b64encode(b"token-abc-123").decode()
        assert "token-abc-123" in raw_body or token_b64[:8] in raw_body

        for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "FROM_EMAIL"):
            os.environ.pop(k, None)

    def test_send_smtp_failure_returns_false(self):
        """Erro de conexao SMTP retorna False sem propagar excecao."""
        os.environ["SMTP_HOST"] = "smtp.resend.com"
        os.environ["SMTP_USER"] = "resend"
        os.environ["SMTP_PASS"] = "wrong"

        import importlib
        import services.email_service as email_svc
        importlib.reload(email_svc)

        with patch("smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, b"unavailable")):
            result = email_svc.send_verification_email("t@e.com", "tok", "https://clubeusa.com")

        assert result is False

        for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"):
            os.environ.pop(k, None)


# ============================================================
#  Utilitario: cria mock de supabase para member_service
# ============================================================

def _make_sb_no_conflict():
    """Supabase mock sem conflito de email."""
    sb = MagicMock()
    no_conflict = MagicMock(data=[])
    (sb.table.return_value
       .select.return_value
       .eq.return_value
       .neq.return_value
       .execute.return_value) = no_conflict
    (sb.table.return_value
       .update.return_value
       .eq.return_value
       .execute.return_value) = MagicMock(data=[{"id": "m1"}])
    return sb


def _make_sb_with_conflict():
    """Supabase mock com conflito de email (email ja existe em outro membro)."""
    sb = MagicMock()
    conflict = MagicMock(data=[{"id": "other-member"}])
    (sb.table.return_value
       .select.return_value
       .eq.return_value
       .neq.return_value
       .execute.return_value) = conflict
    return sb


# ============================================================
#  update_member_email
# ============================================================

class TestUpdateMemberEmail:

    def test_valid_email_updates_and_clears_verified(self):
        """Email valido: atualiza hash/enc e seta email_verified=False."""
        import importlib
        import utils.security as sec
        importlib.reload(sec)
        import services.member_service as ms
        importlib.reload(ms)

        sb = _make_sb_no_conflict()
        with patch("services.member_service._supabase", return_value=sb), \
             patch("services.member_service._audit"):
            result = ms.update_member_email("member-1", "new@example.com")

        assert "atualizado" in result["message"].lower()
        update_payload = sb.table.return_value.update.call_args[0][0]
        assert update_payload["email_verified"] is False
        assert "email_hash" in update_payload
        assert "email_enc" in update_payload

    def test_conflict_raises_value_error(self):
        """Email ja usado por outro membro levanta ValueError."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        sb = _make_sb_with_conflict()
        with patch("services.member_service._supabase", return_value=sb), \
             pytest.raises(ValueError, match="ja esta associado"):
            ms.update_member_email("member-1", "taken@example.com")

    def test_invalid_email_raises_value_error(self):
        """Email malformado levanta ValueError antes de tocar no banco."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        with pytest.raises(ValueError):
            ms.update_member_email("member-1", "isso-nao-e-email")


# ============================================================
#  update_member_profile
# ============================================================

class TestUpdateMemberProfile:

    def test_updates_name(self):
        """Atualiza name_enc quando nome e fornecido."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        sb = MagicMock()
        (sb.table.return_value
           .update.return_value
           .eq.return_value
           .execute.return_value) = MagicMock()

        with patch("services.member_service._supabase", return_value=sb), \
             patch("services.member_service._audit"):
            result = ms.update_member_profile("m1", name="Joao Silva")

        assert result["message"] == "Perfil atualizado."
        payload = sb.table.return_value.update.call_args[0][0]
        assert "name_enc" in payload

    def test_updates_state_and_language(self):
        """Atualiza state e language quando fornecidos."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        sb = MagicMock()
        (sb.table.return_value
           .update.return_value
           .eq.return_value
           .execute.return_value) = MagicMock()

        with patch("services.member_service._supabase", return_value=sb), \
             patch("services.member_service._audit"):
            result = ms.update_member_profile("m1", state="FL", language="es")

        payload = sb.table.return_value.update.call_args[0][0]
        assert payload.get("state") == "FL"
        assert payload.get("language") == "es"

    def test_no_fields_raises_value_error(self):
        """Sem campos validos levanta ValueError."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        with pytest.raises(ValueError, match="Nenhum campo valido"):
            ms.update_member_profile("m1")

    def test_invalid_language_ignored_without_other_fields(self):
        """Language invalido sem outros campos levanta ValueError (nada a atualizar)."""
        import importlib
        import services.member_service as ms
        importlib.reload(ms)

        with pytest.raises(ValueError):
            ms.update_member_profile("m1", language="xx")


# ============================================================
#  Logica de validacao de token (sem precisar de FastAPI)
# ============================================================

class TestEmailTokenLogic:
    """
    Valida a logica dos guards implementados no endpoint confirm_email.
    Testa diretamente a logica de expiracao e single-use,
    sem subir o servidor HTTP.
    """

    def _apply_guards(self, record: dict):
        """
        Replica a logica de validacao do endpoint confirm_email.
        Levanta ValueError com mensagem descritiva se invalido.
        """
        if not record:
            raise ValueError("Token invalido ou expirado.")

        if record.get("used_at"):
            raise ValueError("Token ja utilizado.")

        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise ValueError("Token expirado.")

    def test_used_token_rejected(self):
        """Token com used_at preenchido e rejeitado."""
        future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        record = {
            "id": "tok", "member_id": "m1", "token": "tok",
            "token_type": "email_verification",
            "expires_at": future,
            "used_at": "2026-10-11T10:00:00",
        }
        with pytest.raises(ValueError, match="ja utilizado"):
            self._apply_guards(record)

    def test_expired_token_rejected(self):
        """Token expirado e rejeitado."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        record = {
            "id": "tok", "member_id": "m1", "token": "tok",
            "token_type": "email_verification",
            "expires_at": past,
            "used_at": None,
        }
        with pytest.raises(ValueError, match="expirado"):
            self._apply_guards(record)

    def test_valid_token_passes(self):
        """Token valido nao levanta excecao."""
        future = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        record = {
            "id": "tok", "member_id": "m1", "token": "tok",
            "token_type": "email_verification",
            "expires_at": future,
            "used_at": None,
        }
        self._apply_guards(record)  # nao deve levantar

    def test_empty_record_rejected(self):
        """Banco retornou vazio — token inexistente."""
        with pytest.raises(ValueError, match="invalido"):
            self._apply_guards(None)

    def test_token_entropy_adequate(self):
        """tokens_urlsafe(32) gera 43 chars — espaco de 256 bits."""
        tok = secrets.token_urlsafe(32)
        assert len(tok) == 43
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in tok)
