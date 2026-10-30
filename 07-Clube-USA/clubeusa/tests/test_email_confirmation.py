# ============================================================
#  tests/test_email_confirmation.py — Clube USA
#  Testa fluxo de confirmacao de email (Fase 0.1)
# ============================================================

import asyncio
import os
import secrets
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call


def run(coro):
    """Executa coroutine em teste sincrono."""
    return asyncio.get_event_loop().run_until_complete(coro)

os.environ.setdefault("SUPABASE_URL",         "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_KEY",  "test-service-key")
os.environ.setdefault("JWT_SECRET",            "test-jwt-secret-32byteslongXXXXX")
os.environ.setdefault("ENCRYPTION_KEY",        "test-encryption-key-32bytesXXXXX")
os.environ.setdefault("APP_URL",               "https://clubeusa.com")
os.environ.setdefault("ENVIRONMENT",           "test")


# ============================================================
#  email_service — sem SMTP real
# ============================================================

class TestEmailService:
    def test_dev_env_only_logs(self, caplog):
        """Em ambiente nao-producao, nao tenta SMTP."""
        import logging
        from services.email_service import send_email_confirmation

        with caplog.at_level(logging.INFO, logger="email_service"):
            send_email_confirmation("user@example.com", "Joao", "https://x.com/tok", "pt")

        assert any("DEV" in r.message for r in caplog.records)

    def test_body_pt(self):
        from services.email_service import _build_body
        body = _build_body("Ana", "https://link.com", "pt")
        assert "Ana" in body
        assert "https://link.com" in body
        assert "24 horas" in body

    def test_body_es(self):
        from services.email_service import _build_body
        body = _build_body("Carlos", "https://link.com", "es")
        assert "Carlos" in body
        assert "24 horas" in body

    def test_body_no_name(self):
        from services.email_service import _build_body
        body = _build_body("", "https://link.com", "pt")
        assert "https://link.com" in body

    def test_smtp_skips_without_host(self, caplog):
        """Sem SMTP_HOST, loga erro e retorna sem crash."""
        import logging
        from services.email_service import _send_smtp

        os.environ.pop("SMTP_HOST", None)
        with caplog.at_level(logging.ERROR, logger="email_service"):
            _send_smtp("user@example.com", "Subject", "Body")
        assert any("SMTP" in r.message for r in caplog.records)


# ============================================================
#  auth_email router — testa logica de negocio isolada
# ============================================================

def _make_sb_mock(member_row=None, pending_tokens=0, token_row=None):
    """Fabrica mock do Supabase para testes do router."""
    sb = MagicMock()

    # members.select
    members_chain = sb.table.return_value.select.return_value
    members_chain.eq.return_value.execute.return_value = MagicMock(
        data=[member_row] if member_row else []
    )

    # email_confirm_tokens — pending count
    tokens_select = MagicMock()
    tokens_select.eq.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(
        data=[{}] * pending_tokens
    )
    tokens_insert = MagicMock()
    tokens_insert.execute.return_value = MagicMock(data=[{"id": "tok-id"}])

    # token lookup for confirm
    token_chain = MagicMock()
    token_chain.eq.return_value.execute.return_value = MagicMock(
        data=[token_row] if token_row else []
    )

    def table_router(name):
        mock = MagicMock()
        if name == "members":
            mock.select.return_value = members_chain
            mock.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "email_confirm_tokens":
            mock.select.return_value = tokens_select
            mock.insert.return_value = tokens_insert
            mock.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "audit_logs":
            mock.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return mock

    sb.table.side_effect = table_router
    return sb


class TestConfirmEmail:
    """Testa confirm_email() isolado de Supabase."""

    def test_invalid_token_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        empty_sb = MagicMock()
        empty_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("routers.auth_email._sb", return_value=empty_sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.confirm_email("nonexistent-token"))
        assert exc.value.status_code == 400

    def test_used_token_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        used_token = {
            "id": "tok-id",
            "member_id": "member-123",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "used": True,
        }
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[used_token])

        with patch("routers.auth_email._sb", return_value=sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.confirm_email("some-valid-looking-token"))
        assert exc.value.status_code == 400
        assert "utilizado" in exc.value.detail

    def test_expired_token_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        expired_token = {
            "id": "tok-id",
            "member_id": "member-123",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "used": False,
        }
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[expired_token])

        with patch("routers.auth_email._sb", return_value=sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.confirm_email("expired-token"))
        assert exc.value.status_code == 400
        assert "expirado" in exc.value.detail

    def test_token_too_long_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            run(router_mod.confirm_email("A" * 129))
        assert exc.value.status_code == 400

    def test_valid_token_confirms_email(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")

        valid_token = {
            "id": "tok-id",
            "member_id": "member-123",
            "expires_at": (datetime.utcnow() + timedelta(hours=23)).isoformat(),
            "used": False,
        }

        update_mock = MagicMock()
        update_mock.eq.return_value.execute.return_value = MagicMock(data=[{}])
        insert_mock = MagicMock()
        insert_mock.execute.return_value = MagicMock(data=[{}])
        select_mock = MagicMock()
        select_mock.eq.return_value.execute.return_value = MagicMock(data=[valid_token])

        def table_side(name):
            m = MagicMock()
            m.select.return_value = select_mock
            m.update.return_value = update_mock
            m.insert.return_value = insert_mock
            return m

        sb = MagicMock()
        sb.table.side_effect = table_side

        with patch("routers.auth_email._sb", return_value=sb):
            result = run(router_mod.confirm_email("valid-token-here"))

        assert result["confirmed"] is True
        update_calls = [c for c in sb.table.call_args_list if c.args[0] == "members"]
        assert len(update_calls) >= 1


class TestRequestEmailConfirmation:
    """Testa request_email_confirmation() isolado."""

    def test_no_email_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        member_row = {"id": "m1", "email_enc": None, "email_confirmed": False, "language": "pt", "name_enc": None}
        select_mock = MagicMock()
        select_mock.eq.return_value.execute.return_value = MagicMock(data=[member_row])
        sb = MagicMock()
        sb.table.return_value.select.return_value = select_mock

        with patch("routers.auth_email._sb", return_value=sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.request_email_confirmation({"sub": "m1", "plan": "free"}))
        assert exc.value.status_code == 400
        assert "email" in exc.value.detail.lower()

    def test_already_confirmed_returns_400(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        member_row = {"id": "m1", "email_enc": "enc", "email_confirmed": True, "language": "pt", "name_enc": None}
        select_mock = MagicMock()
        select_mock.eq.return_value.execute.return_value = MagicMock(data=[member_row])
        sb = MagicMock()
        sb.table.return_value.select.return_value = select_mock

        with patch("routers.auth_email._sb", return_value=sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.request_email_confirmation({"sub": "m1", "plan": "free"}))
        assert exc.value.status_code == 400
        assert "confirmado" in exc.value.detail

    def test_too_many_pending_tokens_returns_429(self):
        import importlib
        router_mod = importlib.import_module("routers.auth_email")
        from fastapi import HTTPException

        member_row = {"id": "m1", "email_enc": "enc", "email_confirmed": False, "language": "pt", "name_enc": None}

        def table_side(name):
            m = MagicMock()
            if name == "members":
                m.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[member_row])
            elif name == "email_confirm_tokens":
                m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(data=[{}, {}, {}])
            return m

        sb = MagicMock()
        sb.table.side_effect = table_side

        with patch("routers.auth_email._sb", return_value=sb):
            with pytest.raises(HTTPException) as exc:
                run(router_mod.request_email_confirmation({"sub": "m1", "plan": "free"}))
        assert exc.value.status_code == 429
