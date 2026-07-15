"""
Testes unitários de Fase 0.1 — Auth.
Rodar: cd 07-Clube-USA && pytest

Os testes mockam o cliente Supabase — nenhuma conexão real é feita.
"""
import os

# Env vars mínimas antes de qualquer import do projeto
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-that-is-long-enough-for-tests-xyzxyz"
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from backend.config import get_settings
from backend.routers.auth import RegisterRequest
from backend.services.auth_service import AuthService, pwd_context


# ── Helpers ───────────────────────────────────────────────────────────────────

def settings():
    # Limpar cache entre testes se necessário; normalmente é ok reutilizar
    get_settings.cache_clear()
    return get_settings()


def make_db(*, select_data=None, insert_data=None, update_data=None):
    """Constrói mock do cliente Supabase com chain builder."""
    db = MagicMock()

    def _result(data):
        r = MagicMock()
        r.data = data if data is not None else []
        return r

    table = db.table.return_value
    table.select.return_value.eq.return_value.execute.return_value = _result(select_data)
    table.insert.return_value.execute.return_value = _result(insert_data)
    table.update.return_value.eq.return_value.execute.return_value = _result(update_data)
    return db


def make_svc(db=None, *, select_data=None, insert_data=None, update_data=None):
    if db is None:
        db = make_db(select_data=select_data, insert_data=insert_data, update_data=update_data)
    s = settings()
    svc = AuthService(db, s)
    svc.email_svc.send_confirmation_email = AsyncMock()
    return svc


# ── Password & JWT ────────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        svc = make_svc()
        h = svc._hash_password("senha123")
        assert h != "senha123"

    def test_correct_password_verifies(self):
        svc = make_svc()
        h = svc._hash_password("senha123")
        assert svc._verify_password("senha123", h)

    def test_wrong_password_fails(self):
        svc = make_svc()
        h = svc._hash_password("correta")
        assert not svc._verify_password("errada", h)


class TestJWT:
    def test_token_roundtrip(self):
        svc = make_svc()
        token = svc._create_token("uid-001", "a@b.com")
        payload = svc._decode_token(token)
        assert payload["sub"] == "uid-001"
        assert payload["email"] == "a@b.com"

    def test_tampered_token_raises_401(self):
        from fastapi import HTTPException
        svc = make_svc()
        with pytest.raises(HTTPException) as exc:
            svc._decode_token("token.invalido.aqui")
        assert exc.value.status_code == 401


# ── Register ──────────────────────────────────────────────────────────────────

class TestRegister:
    @pytest.mark.asyncio
    async def test_success(self):
        new_user = {"id": "uid-abc", "email": "novo@test.com", "full_name": "Novo Silva"}
        # Primeira chamada select → vazio (email livre); insert → retorna usuário
        db = MagicMock()
        empty = MagicMock(); empty.data = []
        inserted = MagicMock(); inserted.data = [new_user]
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = empty
        db.table.return_value.insert.return_value.execute.return_value = inserted

        svc = make_svc(db)
        result = await svc.register(
            RegisterRequest(email="novo@test.com", password="senha123", full_name="Novo Silva")
        )
        assert result["email"] == "novo@test.com"
        assert "user_id" in result
        svc.email_svc.send_confirmation_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self):
        from fastapi import HTTPException
        svc = make_svc(select_data=[{"id": "existing"}])
        with pytest.raises(HTTPException) as exc:
            await svc.register(
                RegisterRequest(email="existe@test.com", password="senha123", full_name="Já Existe")
            )
        assert exc.value.status_code == 409

    def test_password_too_short_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="abc", full_name="Nome")

    def test_empty_name_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="senha123", full_name="   ")


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_success_returns_token(self):
        hashed = pwd_context.hash("senha123")
        user = {"id": "uid-001", "email": "u@test.com", "password_hash": hashed,
                 "full_name": "User", "email_confirmed": True}
        svc = make_svc(select_data=[user])
        result = await svc.login("u@test.com", "senha123")
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["email"] == "u@test.com"

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self):
        from fastapi import HTTPException
        hashed = pwd_context.hash("correta")
        user = {"id": "uid-001", "email": "u@test.com", "password_hash": hashed,
                 "full_name": "User", "email_confirmed": True}
        svc = make_svc(select_data=[user])
        with pytest.raises(HTTPException) as exc:
            await svc.login("u@test.com", "errada")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_401(self):
        from fastapi import HTTPException
        svc = make_svc(select_data=[])
        with pytest.raises(HTTPException) as exc:
            await svc.login("nao@existe.com", "qualquer")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_error_message_is_identical_for_both_failure_cases(self):
        """Mesma mensagem para usuário inexistente e senha errada — evita user enumeration."""
        from fastapi import HTTPException
        hashed = pwd_context.hash("correta")
        user = {"id": "uid-001", "email": "u@test.com", "password_hash": hashed,
                 "full_name": "User", "email_confirmed": True}

        svc_no_user = make_svc(select_data=[])
        svc_wrong_pw = make_svc(select_data=[user])

        with pytest.raises(HTTPException) as exc_no_user:
            await svc_no_user.login("nao@existe.com", "qualquer")
        with pytest.raises(HTTPException) as exc_wrong_pw:
            await svc_wrong_pw.login("u@test.com", "errada")

        assert exc_no_user.value.detail == exc_wrong_pw.value.detail


# ── Confirm Email ─────────────────────────────────────────────────────────────

class TestConfirmEmail:
    @pytest.mark.asyncio
    async def test_valid_token_confirms(self):
        future = (datetime.now(tz=timezone.utc) + timedelta(hours=23)).isoformat()
        user = {"id": "uid-001", "email": "u@test.com",
                 "email_confirmed": False, "email_confirmation_expires_at": future}
        db = MagicMock()
        sel = MagicMock(); sel.data = [user]
        upd = MagicMock(); upd.data = []
        db.table.return_value.select.return_value.eq.return_value.execute.return_value = sel
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = upd
        svc = make_svc(db)
        result = await svc.confirm_email("valid-token")
        assert "sucesso" in result["message"]

    @pytest.mark.asyncio
    async def test_expired_token_returns_400(self):
        from fastapi import HTTPException
        past = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
        user = {"id": "uid-001", "email": "u@test.com",
                 "email_confirmed": False, "email_confirmation_expires_at": past}
        svc = make_svc(select_data=[user])
        with pytest.raises(HTTPException) as exc:
            await svc.confirm_email("expired-token")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_token_returns_400(self):
        from fastapi import HTTPException
        svc = make_svc(select_data=[])
        with pytest.raises(HTTPException) as exc:
            await svc.confirm_email("nao-existe")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_already_confirmed_is_idempotent(self):
        user = {"id": "uid-001", "email": "u@test.com",
                 "email_confirmed": True, "email_confirmation_expires_at": None}
        svc = make_svc(select_data=[user])
        result = await svc.confirm_email("any-token")
        assert "anteriormente" in result["message"]


# ── Isolamento Multi-Tenant ───────────────────────────────────────────────────

class TestMultiTenantIsolation:
    @pytest.mark.asyncio
    async def test_profile_of_other_user_returns_404(self):
        """user_id vem sempre do token JWT (servidor).
        Consultar ID que não pertence ao token → 404 (não vaza existência)."""
        from fastapi import HTTPException
        svc = make_svc(select_data=[])  # DB retorna vazio para qualquer ID
        with pytest.raises(HTTPException) as exc:
            await svc.get_profile("uuid-de-outro-usuario")
        assert exc.value.status_code == 404

    def test_get_current_user_id_rejects_missing_header(self):
        from fastapi import HTTPException, Request as StarletteRequest
        from starlette.testclient import TestClient
        svc = make_svc()
        req = MagicMock()
        req.headers = {}
        req.headers.get = lambda key, default="": default
        with pytest.raises(HTTPException) as exc:
            svc.get_current_user_id(req)
        assert exc.value.status_code == 401
