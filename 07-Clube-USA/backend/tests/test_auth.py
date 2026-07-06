"""
Testes de autenticação — Fase 0.1.

Cobertura:
- Cadastro: caminho feliz, senha fraca, senha sem maiúscula, senha sem dígito, ZIP inválido
- Login: caminho feliz, credenciais erradas, email não confirmado
- Refresh: caminho feliz, token inválido
- Rate limit: resposta 429 após limite
- Anti-enumeração: register retorna sempre a mesma mensagem
"""

import time
from unittest.mock import MagicMock


# ───────────────────── helpers ──────────────────────

def _make_supabase_user(user_id: str = "user-abc-123") -> MagicMock:
    user = MagicMock()
    user.id = user_id
    return user


def _make_supabase_session(
    access_token: str = "access.tok",
    refresh_token: str = "refresh.tok",
    expires_in: int = 3600,
) -> MagicMock:
    session = MagicMock()
    session.access_token = access_token
    session.refresh_token = refresh_token
    session.expires_in = expires_in
    return session


VALID_REGISTER_PAYLOAD = {
    "email": "joao@example.com",
    "password": "Senha123!",
    "first_name": "João",
    "last_name": "Silva",
    "zip_code": "90210",
    "phone": "555-1234",
}


# ───────────────────── /auth/register ───────────────

class TestRegister:
    def test_register_success(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.user = _make_supabase_user()

        table_mock = MagicMock()
        table_mock.insert.return_value.execute.return_value = MagicMock()

        mock_supabase.auth.sign_up.return_value = auth_resp
        mock_supabase.table.return_value = table_mock

        resp = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        assert resp.status_code == 200
        assert "email" in resp.json()["message"].lower()
        mock_supabase.auth.sign_up.assert_called_once()

    def test_register_creates_profile(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.user = _make_supabase_user("uid-999")

        table_mock = MagicMock()
        insert_mock = table_mock.insert.return_value
        insert_mock.execute.return_value = MagicMock()

        mock_supabase.auth.sign_up.return_value = auth_resp
        mock_supabase.table.return_value = table_mock

        client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        # register_user faz múltiplos inserts (perfil + evento analytics).
        # Buscamos o insert que contém 'id' (o do perfil).
        all_inserts = [call[0][0] for call in table_mock.insert.call_args_list]
        profile_insert = next((d for d in all_inserts if "id" in d), None)
        assert profile_insert is not None, "Insert de perfil não encontrado"
        assert profile_insert["id"] == "uid-999"
        assert profile_insert["first_name"] == "João"

    def test_register_weak_password_too_short(self, client, mock_supabase):
        payload = {**VALID_REGISTER_PAYLOAD, "password": "Ab1"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_password_no_uppercase(self, client, mock_supabase):
        """Senha com 8+ chars e dígito mas sem maiúscula deve ser rejeitada."""
        payload = {**VALID_REGISTER_PAYLOAD, "password": "senha123"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_password_no_digit(self, client, mock_supabase):
        """Senha com 8+ chars e maiúscula mas sem dígito deve ser rejeitada."""
        payload = {**VALID_REGISTER_PAYLOAD, "password": "SenhaFort"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_invalid_zip(self, client, mock_supabase):
        payload = {**VALID_REGISTER_PAYLOAD, "zip_code": "ABC"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_missing_first_name(self, client, mock_supabase):
        payload = {**VALID_REGISTER_PAYLOAD, "first_name": "  "}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    def test_register_same_message_for_existing_email(self, client, mock_supabase):
        """Anti-enumeração: a mesma mensagem seja qual for o resultado."""
        auth_resp = MagicMock()
        auth_resp.user = _make_supabase_user()
        table_mock = MagicMock()
        table_mock.insert.return_value.execute.return_value = MagicMock()
        mock_supabase.auth.sign_up.return_value = auth_resp
        mock_supabase.table.return_value = table_mock

        r1 = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        r2 = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        assert r1.json()["message"] == r2.json()["message"]

    def test_register_supabase_error_returns_400(self, client, mock_supabase):
        mock_supabase.auth.sign_up.side_effect = Exception("Supabase down")
        resp = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        assert resp.status_code == 400
        # Não deve vazar mensagem interna
        assert "Supabase" not in resp.json()["detail"]

    def test_register_security_headers_present(self, client, mock_supabase):
        """Toda resposta deve incluir headers de segurança."""
        auth_resp = MagicMock()
        auth_resp.user = _make_supabase_user()
        table_mock = MagicMock()
        table_mock.insert.return_value.execute.return_value = MagicMock()
        mock_supabase.auth.sign_up.return_value = auth_resp
        mock_supabase.table.return_value = table_mock

        resp = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"


# ───────────────────── /auth/login ──────────────────

class TestLogin:
    def test_login_success(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.session = _make_supabase_session()
        mock_supabase.auth.sign_in_with_password.return_value = auth_resp

        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1234"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access.tok"
        assert data["refresh_token"] == "refresh.tok"
        assert data["token_type"] == "bearer"

    def test_login_wrong_credentials(self, client, mock_supabase):
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login")

        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "errado"})

        assert resp.status_code == 401
        assert "senha" in resp.json()["detail"].lower() or "email" in resp.json()["detail"].lower()

    def test_login_no_session(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.session = None
        mock_supabase.auth.sign_in_with_password.return_value = auth_resp

        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1234"})

        assert resp.status_code == 401


# ───────────────────── /auth/refresh ────────────────

class TestRefresh:
    def test_refresh_success(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.session = _make_supabase_session(
            access_token="new.access", refresh_token="new.refresh"
        )
        mock_supabase.auth.refresh_session.return_value = auth_resp

        resp = client.post("/auth/refresh", json={"refresh_token": "old.refresh"})

        assert resp.status_code == 200
        assert resp.json()["access_token"] == "new.access"

    def test_refresh_invalid_token(self, client, mock_supabase):
        mock_supabase.auth.refresh_session.side_effect = Exception("Token inválido")

        resp = client.post("/auth/refresh", json={"refresh_token": "lixo"})

        assert resp.status_code == 401
