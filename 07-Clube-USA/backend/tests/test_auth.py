"""Testes de autenticação."""
import pytest
from unittest.mock import MagicMock
from gotrue.errors import AuthApiError


def _supabase_error(msg: str) -> AuthApiError:
    return AuthApiError(msg, 400, "unexpected_failure")


class TestRegister:
    def test_success(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        fake_user = MagicMock()
        fake_user.user = MagicMock(id="uuid-123")
        mock_auth.auth.sign_up.return_value = fake_user

        resp = client.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "Senha123",
            "full_name": "João Silva",
        })
        assert resp.status_code == 201
        assert "e-mail" in resp.json()["message"].lower()

    def test_duplicate_email(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        mock_auth.auth.sign_up.side_effect = _supabase_error("already registered")

        resp = client.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "Senha123",
            "full_name": "João Silva",
        })
        assert resp.status_code == 409

    def test_weak_password_short(self, client, patch_supabase):
        resp = client.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "abc",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    def test_weak_password_no_number(self, client, patch_supabase):
        resp = client.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "SenhaSemNumero",
            "full_name": "João Silva",
        })
        assert resp.status_code == 422

    def test_invalid_email(self, client, patch_supabase):
        resp = client.post("/auth/register", json={
            "email": "nao-e-email",
            "password": "Senha123",
            "full_name": "João",
        })
        assert resp.status_code == 422

    def test_name_too_short(self, client, patch_supabase):
        resp = client.post("/auth/register", json={
            "email": "joao@exemplo.com",
            "password": "Senha123",
            "full_name": "J",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_success(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        fake_session = MagicMock()
        fake_session.session = MagicMock(
            access_token="access-tok",
            refresh_token="refresh-tok",
            expires_in=3600,
        )
        mock_auth.auth.sign_in_with_password.return_value = fake_session

        resp = client.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "Senha123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access-tok"
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        mock_auth.auth.sign_in_with_password.side_effect = _supabase_error("invalid credentials")

        resp = client.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "Errada123",
        })
        assert resp.status_code == 401

    def test_email_not_verified(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        fake_resp = MagicMock()
        fake_resp.session = None  # Supabase não retorna sessão sem email confirmado
        mock_auth.auth.sign_in_with_password.return_value = fake_resp

        resp = client.post("/auth/login", json={
            "email": "joao@exemplo.com",
            "password": "Senha123",
        })
        assert resp.status_code == 403


class TestVerifyEmail:
    def test_success(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        mock_auth.auth.verify_otp.return_value = MagicMock()

        resp = client.post("/auth/verify-email", json={
            "token_hash": "valid-hash",
            "type": "email",
        })
        assert resp.status_code == 200
        assert "verificado" in resp.json()["message"].lower()

    def test_invalid_token(self, client, patch_supabase):
        mock_auth, _ = patch_supabase
        mock_auth.auth.verify_otp.side_effect = _supabase_error("invalid token")

        resp = client.post("/auth/verify-email", json={
            "token_hash": "bad-hash",
            "type": "email",
        })
        assert resp.status_code == 400
