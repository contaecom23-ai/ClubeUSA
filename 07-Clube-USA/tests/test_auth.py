"""
Testes para o fluxo de autenticação (Fase 0.1).
Banco de dados mockado — não requer PostgreSQL real.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone


# --- helpers ---

def _confirmed_user_row(user_id="user-123"):
    row = {
        "id": user_id,
        "password_hash": None,   # preenchido abaixo
        "email_confirmed": True,
        "is_active": True,
    }
    from backend.app.auth.utils import hash_password
    row["password_hash"] = hash_password("SenhaCorreta1!")
    return row


# ============================================================
# Registro
# ============================================================

class TestRegister:
    def test_register_success(self, client, mock_db):
        mock_db.fetchrow.return_value = None  # email não existe
        mock_db.fetchrow.side_effect = [
            None,                                    # SELECT existência
            {"id": "u1", "email": "a@b.com", "name": "Teste"},  # INSERT RETURNING
        ]
        with patch("backend.app.auth.service._send_confirmation_email", new=AsyncMock()):
            resp = client.post("/auth/register", json={
                "email": "a@b.com",
                "password": "senha1234",
                "name": "Teste",
            })
        assert resp.status_code == 201
        assert "email" in resp.json()["message"].lower()

    def test_register_duplicate_email(self, client, mock_db):
        mock_db.fetchrow.return_value = {"id": "existing"}
        resp = client.post("/auth/register", json={
            "email": "dup@b.com",
            "password": "senha1234",
            "name": "Dup",
        })
        assert resp.status_code == 409

    def test_register_short_password(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "a@b.com",
            "password": "123",
            "name": "Teste",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "nao_e_email",
            "password": "senha1234",
            "name": "Teste",
        })
        assert resp.status_code == 422

    def test_register_invalid_state(self, client, mock_db):
        resp = client.post("/auth/register", json={
            "email": "a@b.com",
            "password": "senha1234",
            "name": "Teste",
            "estado": "ZZ",
        })
        assert resp.status_code == 422


# ============================================================
# Login
# ============================================================

class TestLogin:
    def test_login_success(self, client, mock_db):
        mock_db.fetchrow.return_value = _confirmed_user_row()
        mock_db.execute = AsyncMock()
        resp = client.post("/auth/login", json={
            "email": "a@b.com",
            "password": "SenhaCorreta1!",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, mock_db):
        mock_db.fetchrow.return_value = _confirmed_user_row()
        resp = client.post("/auth/login", json={
            "email": "a@b.com",
            "password": "senhaerrada",
        })
        assert resp.status_code == 401

    def test_login_unconfirmed_email(self, client, mock_db):
        row = _confirmed_user_row()
        row["email_confirmed"] = False
        mock_db.fetchrow.return_value = row
        resp = client.post("/auth/login", json={
            "email": "a@b.com",
            "password": "SenhaCorreta1!",
        })
        assert resp.status_code == 403

    def test_login_inactive_user(self, client, mock_db):
        row = _confirmed_user_row()
        row["is_active"] = False
        mock_db.fetchrow.return_value = row
        resp = client.post("/auth/login", json={
            "email": "a@b.com",
            "password": "SenhaCorreta1!",
        })
        assert resp.status_code == 403

    def test_login_user_not_found(self, client, mock_db):
        mock_db.fetchrow.return_value = None
        resp = client.post("/auth/login", json={
            "email": "notexist@b.com",
            "password": "SenhaCorreta1!",
        })
        assert resp.status_code == 401


# ============================================================
# Confirmação de email
# ============================================================

class TestConfirmEmail:
    def test_confirm_success(self, client, mock_db):
        mock_db.fetchrow.return_value = {
            "id": "u1",
            "email_confirm_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        mock_db.execute = AsyncMock()
        resp = client.get("/auth/confirm-email?token=tokenvalido")
        assert resp.status_code == 200

    def test_confirm_invalid_token(self, client, mock_db):
        mock_db.fetchrow.return_value = None
        resp = client.get("/auth/confirm-email?token=tokeninvalido")
        assert resp.status_code == 400

    def test_confirm_expired_token(self, client, mock_db):
        mock_db.fetchrow.return_value = {
            "id": "u1",
            "email_confirm_expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        resp = client.get("/auth/confirm-email?token=expirado")
        assert resp.status_code == 400


# ============================================================
# JWT utils
# ============================================================

class TestJWT:
    def test_create_and_decode_access_token(self):
        from backend.app.auth.utils import create_access_token, decode_access_token
        token = create_access_token("user-42")
        user_id = decode_access_token(token)
        assert user_id == "user-42"

    def test_decode_invalid_token_raises(self):
        from backend.app.auth.utils import decode_access_token
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_access_token("token.invalido.aqui")
