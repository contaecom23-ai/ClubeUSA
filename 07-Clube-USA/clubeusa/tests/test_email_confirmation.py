# ============================================================
#  tests/test_email_confirmation.py — Clube USA
#  Testa o fluxo de confirmação de email:
#    - send_confirmation_email (serviço de email)
#    - endpoint POST /auth/email/send-confirmation
#    - endpoint GET  /auth/email/confirm/{token}
#    - auto-trigger no register_member
# ============================================================

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
#  Testes unitários: email_service.send_confirmation_email
# ============================================================

class TestEmailService:
    def test_dev_mode_returns_true_no_smtp(self):
        """Em dev, retorna True sem chamar SMTP."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            from services.email_service import send_confirmation_email
            result = send_confirmation_email("test@example.com", "João", "https://clubeusa.com/confirm/abc")
        assert result is True

    def test_prod_missing_smtp_returns_false(self):
        """Em prod sem SMTP configurado, retorna False."""
        env = {
            "ENVIRONMENT": "production",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASS": "",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("SMTP_HOST", None)
            from services import email_service
            result = email_service.send_confirmation_email(
                "test@example.com", "João", "https://clubeusa.com/confirm/abc"
            )
        assert result is False

    def test_prod_smtp_success(self):
        """Em prod com SMTP configurado e envio bem-sucedido, retorna True."""
        env = {
            "ENVIRONMENT": "production",
            "SMTP_HOST":   "smtp.sendgrid.net",
            "SMTP_PORT":   "587",
            "SMTP_USER":   "apikey",
            "SMTP_PASS":   "SG.fake",
            "FROM_EMAIL":  "noreply@clubeusa.com",
        }
        with patch.dict(os.environ, env):
            import smtplib
            mock_smtp = MagicMock()
            mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp.__exit__  = MagicMock(return_value=False)

            with patch("smtplib.SMTP", return_value=mock_smtp):
                from services import email_service
                result = email_service.send_confirmation_email(
                    "user@example.com", "Maria", "https://clubeusa.com/confirm/xyz"
                )
        assert result is True

    def test_prod_smtp_failure_returns_false(self):
        """Em prod com SMTP que lança exceção, retorna False sem explodir."""
        env = {
            "ENVIRONMENT": "production",
            "SMTP_HOST":   "smtp.broken.com",
            "SMTP_PORT":   "587",
            "SMTP_USER":   "user",
            "SMTP_PASS":   "pass",
        }
        with patch.dict(os.environ, env):
            with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("sem rota")):
                from services import email_service
                result = email_service.send_confirmation_email(
                    "user@example.com", "Carlos", "https://clubeusa.com/confirm/t"
                )
        assert result is False


# ============================================================
#  Testes unitários: router email_confirmation (sem Supabase)
# ============================================================

def _fake_member_row(confirmed=False, has_email=True):
    row = {
        "id":              "mem-uuid-1",
        "email_enc":       "ENCRYPTED_EMAIL" if has_email else None,
        "email_confirmed": confirmed,
        "name_enc":        "ENCRYPTED_NAME",
    }
    return row


class TestEmailConfirmationRouter:
    """Testa a lógica do router isolado (sem HTTP, sem Supabase real)."""

    def _make_token(self):
        raw = secrets.token_urlsafe(32)
        h   = hashlib.sha256(raw.encode()).hexdigest()
        return raw, h

    def test_send_confirmation_no_email_raises_400(self):
        """Membro sem email cadastrado → 400."""
        from fastapi import HTTPException
        import asyncio

        sb_mock = MagicMock()
        sb_mock.table().select().eq().execute.return_value = MagicMock(
            data=[_fake_member_row(has_email=False)]
        )

        with patch("routers.email_confirmation._sb", return_value=sb_mock):
            from routers.email_confirmation import send_email_confirmation
            with pytest.raises(HTTPException) as exc:
                asyncio.get_event_loop().run_until_complete(
                    send_email_confirmation({"sub": "mem-uuid-1"})
                )
            assert exc.value.status_code == 400

    def test_send_confirmation_already_confirmed_returns_200(self):
        """Email já confirmado → 200 com mensagem."""
        import asyncio

        sb_mock = MagicMock()
        sb_mock.table().select().eq().execute.return_value = MagicMock(
            data=[_fake_member_row(confirmed=True)]
        )

        with patch("routers.email_confirmation._sb", return_value=sb_mock):
            from routers.email_confirmation import send_email_confirmation
            result = asyncio.get_event_loop().run_until_complete(
                send_email_confirmation({"sub": "mem-uuid-1"})
            )
        assert "confirmado" in result["message"].lower()

    def test_confirm_token_invalid_returns_html_erro(self):
        """Token não encontrado → HTML de erro."""
        import asyncio

        sb_mock = MagicMock()
        sb_mock.table().select().eq().execute.return_value = MagicMock(data=[])

        with patch("routers.email_confirmation._sb", return_value=sb_mock):
            from routers.email_confirmation import confirm_email
            html = asyncio.get_event_loop().run_until_complete(
                confirm_email("token-invalido-qualquer")
            )
        assert "inválido" in html or "invalido" in html.lower()

    def test_confirm_token_expired_returns_html_erro(self):
        """Token expirado → HTML de erro, token deletado."""
        import asyncio

        expired_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        sb_mock = MagicMock()

        sb_mock.table("email_confirmation_tokens").select(
            "id,member_id,expires_at,used_at"
        ).eq().execute.return_value = MagicMock(data=[{
            "id":         "tok-1",
            "member_id":  "mem-uuid-1",
            "expires_at": expired_at,
            "used_at":    None,
        }])

        with patch("routers.email_confirmation._sb", return_value=sb_mock):
            from routers.email_confirmation import confirm_email
            html = asyncio.get_event_loop().run_until_complete(
                confirm_email("qualquer-token")
            )
        assert "expirado" in html.lower()

    def test_confirm_token_already_used(self):
        """Token já usado → HTML informativo."""
        import asyncio

        used_at = datetime.now(timezone.utc).isoformat()
        sb_mock = MagicMock()

        sb_mock.table("email_confirmation_tokens").select(
            "id,member_id,expires_at,used_at"
        ).eq().execute.return_value = MagicMock(data=[{
            "id":         "tok-2",
            "member_id":  "mem-uuid-1",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "used_at":    used_at,
        }])

        with patch("routers.email_confirmation._sb", return_value=sb_mock):
            from routers.email_confirmation import confirm_email
            html = asyncio.get_event_loop().run_until_complete(
                confirm_email("qualquer-token")
            )
        assert "confirmado" in html.lower()

    def test_oversized_token_rejected(self):
        """Token com > 200 chars é rejeitado (path traversal / DoS protection)."""
        import asyncio
        from routers.email_confirmation import confirm_email

        big_token = "A" * 201
        html = asyncio.get_event_loop().run_until_complete(confirm_email(big_token))
        assert "inválido" in html or "invalido" in html.lower()


# ============================================================
#  Testes: _trigger_email_confirmation em member_service
# ============================================================

class TestMemberServiceEmailTrigger:
    """
    Testa que register_member dispara (ou não) _trigger_email_confirmation.
    Patchamos _trigger_email_confirmation diretamente — o que nos interessa é
    se é chamada ou não, não os detalhes internos (esses são testados nos
    testes de email_service).
    """

    def _make_sb_mock(self, member_id="new-id-1", referral_code="ABCD1234"):
        """
        Retorna um mock de Supabase que diferencia chamadas por tabela
        usando side_effect no método table().
        """
        from unittest.mock import MagicMock

        members_mock    = MagicMock()
        audit_mock      = MagicMock()

        # members: select (duplicata check) -> vazio; insert -> retorna novo membro
        members_select_mock = MagicMock()
        members_select_mock.eq.return_value.execute.return_value = MagicMock(data=[])
        members_mock.select.return_value = members_select_mock

        members_insert_mock = MagicMock()
        members_insert_mock.execute.return_value = MagicMock(data=[{
            "id": member_id, "plan": "free", "referral_code": referral_code,
        }])
        members_mock.insert.return_value = members_insert_mock

        # audit_logs: insert sempre ok
        audit_mock.insert.return_value.execute.return_value = MagicMock(data=[{}])

        def _table(name):
            if name == "members":
                return members_mock
            return audit_mock

        sb_mock = MagicMock()
        sb_mock.table.side_effect = _table
        return sb_mock

    def test_register_with_email_triggers_confirmation(self):
        """Ao registrar com email, _trigger_email_confirmation é chamado."""
        from services import member_service

        with (
            patch("services.member_service._supabase", return_value=self._make_sb_mock()),
            patch("services.group_manager.assign_member_to_group",
                  return_value={"invite_link": "#", "name": "G"}),
            patch("services.member_service._trigger_email_confirmation") as mock_trigger,
            patch("utils.security.hash_pii",           return_value="hashed"),
            patch("utils.security.encrypt",            side_effect=lambda x: f"ENC({x})"),
            patch("utils.security.validate_phone",     return_value="+15551234567"),
            patch("utils.security.validate_email",     return_value="user@example.com"),
            patch("utils.security.generate_referral_code", return_value="XKCD8765"),
            patch("utils.security.create_token",       return_value="jwt.token"),
            patch.dict(os.environ, {
                "SUPABASE_URL":         "https://fake.supabase.co",
                "SUPABASE_SERVICE_KEY": "fake",
                "ENCRYPTION_KEY":       "fake-enc-key-32chars",
                "JWT_SECRET":           "fake-jwt",
                "APP_URL":              "https://clubeusa.com",
            }),
        ):
            member_service.register_member(
                phone="5551234567",
                email="user@example.com",
                name="Test User",
            )

        mock_trigger.assert_called_once()
        args = mock_trigger.call_args[0]
        assert args[0] == "new-id-1"          # member_id
        assert args[1] == "user@example.com"  # email

    def test_register_without_email_no_confirmation_sent(self):
        """Ao registrar sem email, _trigger_email_confirmation não é chamado."""
        from services import member_service

        with (
            patch("services.member_service._supabase", return_value=self._make_sb_mock()),
            patch("services.group_manager.assign_member_to_group",
                  return_value={"invite_link": "#", "name": "G"}),
            patch("services.member_service._trigger_email_confirmation") as mock_trigger,
            patch("utils.security.hash_pii",           return_value="hashed"),
            patch("utils.security.encrypt",            side_effect=lambda x: f"ENC({x})"),
            patch("utils.security.validate_phone",     return_value="+15551111111"),
            patch("utils.security.generate_referral_code", return_value="AAAA0000"),
            patch("utils.security.create_token",       return_value="jwt.token"),
            patch.dict(os.environ, {
                "SUPABASE_URL":         "https://fake.supabase.co",
                "SUPABASE_SERVICE_KEY": "fake",
                "ENCRYPTION_KEY":       "fake-enc-key-32chars",
                "JWT_SECRET":           "fake-jwt",
                "APP_URL":              "https://clubeusa.com",
            }),
        ):
            member_service.register_member(phone="5551111111")

        mock_trigger.assert_not_called()
