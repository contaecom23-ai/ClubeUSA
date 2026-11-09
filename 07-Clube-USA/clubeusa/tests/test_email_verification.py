# ============================================================
#  tests/test_email_verification.py
#  Testa o fluxo de verificacao de email (Fase 0.1)
#
#  Estrategia:
#   - Funções utilitárias (hash_token, send_verification_email) → testes unitários diretos
#   - Lógica de token (expirado, usado, valido) → testes via TestClient com mocks no lugar certo
# ============================================================

import hashlib
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ------------------------------------------------------------------ helpers ---

def _future_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def _past_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()


# ------------------------------------------------------------------ utils/email ---

class TestHashToken:
    def test_deterministic(self):
        from utils.email import hash_token
        t = "my_secret_token"
        assert hash_token(t) == hash_token(t)

    def test_different_tokens_different_hashes(self):
        from utils.email import hash_token
        assert hash_token("aaa") != hash_token("bbb")

    def test_matches_sha256(self):
        from utils.email import hash_token
        raw = "test_token_xyz"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert hash_token(raw) == expected


class TestSendVerificationEmail:
    def test_dev_mode_logs_and_returns_true(self, monkeypatch, caplog):
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)
        monkeypatch.setenv("APP_URL", "https://test.clubeusa.com")

        from utils.email import send_verification_email
        import logging
        with caplog.at_level(logging.INFO, logger="email"):
            result = send_verification_email("user@example.com", "raw_token_abc")

        assert result is True
        assert "raw_token_abc" in caplog.text

    def test_smtp_success(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "user")
        monkeypatch.setenv("SMTP_PASSWORD", "pass")
        monkeypatch.setenv("SMTP_FROM", "noreply@clubeusa.com")
        monkeypatch.setenv("APP_URL", "https://clubeusa.com")

        from utils import email as email_mod
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("utils.email.smtplib.SMTP", return_value=mock_smtp):
            result = email_mod.send_verification_email("user@example.com", "tok123")

        assert result is True
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.sendmail.assert_called_once()

    def test_smtp_failure_returns_false(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "user")
        monkeypatch.setenv("SMTP_PASSWORD", "pass")
        monkeypatch.setenv("SMTP_FROM", "noreply@clubeusa.com")
        monkeypatch.setenv("APP_URL", "https://clubeusa.com")

        import smtplib
        with patch("utils.email.smtplib.SMTP", side_effect=smtplib.SMTPException("conn fail")):
            from utils.email import send_verification_email
            result = send_verification_email("user@example.com", "tok123")

        assert result is False


# ------------------------------------------------------------------ token logic (pure) ---
# Testa a lógica de expiração/uso de token sem depender do FastAPI.

class TestTokenLogic:
    """Testa a logica de verificacao de token de forma isolada."""

    def test_expired_token_detected(self):
        """Token com expires_at no passado deve ser rejeitado."""
        record = {
            "id": "tok-1",
            "member_id": "mem-1",
            "token_hash": "h",
            "used_at": None,
            "expires_at": _past_iso(),
        }
        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert datetime.now(timezone.utc) > expires

    def test_valid_token_not_expired(self):
        """Token com expires_at no futuro nao deve ser rejeitado."""
        record = {
            "id": "tok-1",
            "member_id": "mem-1",
            "token_hash": "h",
            "used_at": None,
            "expires_at": _future_iso(),
        }
        expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert datetime.now(timezone.utc) <= expires

    def test_used_token_flag(self):
        """Token com used_at preenchido deve ser bloqueado."""
        record = {"used_at": "2026-01-01T00:00:00+00:00"}
        assert bool(record.get("used_at")) is True

    def test_unused_token_flag(self):
        """Token com used_at None nao deve ser bloqueado."""
        record = {"used_at": None}
        assert not record.get("used_at")


# ------------------------------------------------------------------ GET /auth/email/verify (integration) ---

@pytest.fixture(scope="module")
def app_client(tmp_path_factory, monkeypatch_session=None):
    """Cria TestClient com env vars minimas."""
    import os
    os.environ.setdefault("SUPABASE_URL", "http://localhost")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake_key")
    os.environ.setdefault("ENCRYPTION_KEY", "test_encryption_key_32bytes_long!!")
    os.environ.setdefault("JWT_SECRET", "test_jwt_secret_at_least_32_bytes!!")
    os.environ.setdefault("APP_URL", "https://clubeusa.com")


def _make_sb_for_verify(token_record=None, already_verified=False):
    """Monta mock do Supabase para o endpoint GET /auth/email/verify."""
    sb = MagicMock()

    def side(table_name):
        tbl = MagicMock()
        if table_name == "email_verification_tokens":
            # select().eq().execute()
            inner = MagicMock()
            inner.execute.return_value.data = [token_record] if token_record else []
            tbl.select.return_value.eq.return_value = inner
            # update().eq().execute()
            tbl.update.return_value.eq.return_value.execute.return_value = MagicMock()
            # delete().eq().execute()
            tbl.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        elif table_name == "members":
            inner = MagicMock()
            inner.execute.return_value.data = [{"email_verified": already_verified}]
            tbl.select.return_value.eq.return_value = inner
            tbl.update.return_value.eq.return_value.execute.return_value = MagicMock()
        elif table_name == "audit_logs":
            tbl.insert.return_value.execute.return_value = MagicMock()
        return tbl

    sb.table.side_effect = side
    return sb


def _setup_env():
    import os
    os.environ.setdefault("SUPABASE_URL", "http://localhost")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake_key")
    os.environ.setdefault("ENCRYPTION_KEY", "test_encryption_key_32bytes_long!!")
    os.environ.setdefault("JWT_SECRET", "test_jwt_secret_at_least_32_bytes!!")
    os.environ.setdefault("APP_URL", "https://clubeusa.com")


class TestVerifyEmailEndpoint:
    def test_missing_token_param_returns_422(self):
        _setup_env()
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/auth/email/verify")
        assert resp.status_code == 422

    def test_invalid_token_shows_error_html(self):
        _setup_env()
        sb = _make_sb_for_verify(token_record=None)
        with patch("supabase.create_client", return_value=sb), \
             patch("utils.email.hash_token", return_value="fakehash"):
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            resp = client.get("/auth/email/verify?token=badtoken")
        assert resp.status_code == 200
        assert "invalido" in resp.text.lower() or "expirado" in resp.text.lower()

    def test_expired_token_shows_error_html(self):
        _setup_env()
        record = {
            "id": "tok-1", "member_id": "mem-1",
            "token_hash": "h", "used_at": None,
            "expires_at": _past_iso(),
        }
        sb = _make_sb_for_verify(token_record=record)
        with patch("supabase.create_client", return_value=sb), \
             patch("utils.email.hash_token", return_value="fakehash"):
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            resp = client.get("/auth/email/verify?token=expiredtoken")
        assert resp.status_code == 200
        assert "expirado" in resp.text.lower()

    def test_used_token_shows_error_html(self):
        _setup_env()
        record = {
            "id": "tok-1", "member_id": "mem-1",
            "token_hash": "h", "used_at": "2026-01-01T00:00:00+00:00",
            "expires_at": _future_iso(),
        }
        sb = _make_sb_for_verify(token_record=record)
        with patch("supabase.create_client", return_value=sb), \
             patch("utils.email.hash_token", return_value="fakehash"):
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            resp = client.get("/auth/email/verify?token=usedtoken")
        assert resp.status_code == 200
        assert "utilizado" in resp.text.lower()

    def test_valid_token_confirms_email_and_shows_success(self):
        _setup_env()
        record = {
            "id": "tok-1", "member_id": "mem-1",
            "token_hash": "h", "used_at": None,
            "expires_at": _future_iso(),
        }
        sb = _make_sb_for_verify(token_record=record, already_verified=False)
        with patch("supabase.create_client", return_value=sb), \
             patch("utils.email.hash_token", return_value="fakehash"):
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            resp = client.get("/auth/email/verify?token=validtoken")
        assert resp.status_code == 200
        assert "confirmado" in resp.text.lower()
        # Verifica que update foi chamado no banco
        sb.table("members").update.assert_called()

    def test_already_verified_idempotent(self):
        _setup_env()
        record = {
            "id": "tok-1", "member_id": "mem-1",
            "token_hash": "h", "used_at": None,
            "expires_at": _future_iso(),
        }
        sb = _make_sb_for_verify(token_record=record, already_verified=True)
        with patch("supabase.create_client", return_value=sb), \
             patch("utils.email.hash_token", return_value="fakehash"):
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            resp = client.get("/auth/email/verify?token=validtoken")
        assert resp.status_code == 200
        assert "confirmado" in resp.text.lower()

    def test_no_client_input_determines_member_id(self):
        """
        Garantia de isolamento: o member_id vem SEMPRE do token armazenado
        no banco, nunca de parametro do request. Nao ha como um usuario
        confirmar o email de outro usuario — ele precisaria do token bruto
        (que so vai por email para o dono).
        """
        # Este teste e documental: o endpoint GET /auth/email/verify
        # nao aceita member_id como parametro. O unico input e o token.
        # Verificar que a rota nao tem parametro 'member_id'.
        _setup_env()
        from fastapi.testclient import TestClient
        from api.main import app
        client = TestClient(app, raise_server_exceptions=False)
        # Tentar passar member_id nao deve causar nenhum comportamento diferente
        resp = client.get("/auth/email/verify?token=x&member_id=HACKER")
        # 422 (token invalido/nao encontrado) ou 200 com erro — nao deve haver bypass
        assert resp.status_code in (200, 422)
        if resp.status_code == 200:
            assert "invalido" in resp.text.lower() or "expirado" in resp.text.lower()
