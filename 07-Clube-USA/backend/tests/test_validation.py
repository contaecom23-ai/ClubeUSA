"""
Testes de validação de cadastro — Fase 0.4.

Cobertura:
- is_disposable_email: domínios conhecidos, Gmail, case-insensitive
- check_valid_registration: todos os quadrantes (confirmado/não + zip/sem zip) + erros
- GET /users/me/validation-status: autenticado válido, inválido, sem auth
- Bloqueio de email descartável no cadastro (integração com auth/service.py)
- registration.blocked trackado como analytics event
"""

from unittest.mock import MagicMock, patch

# conftest.py garante que backend/ está no sys.path e env vars mínimas estão definidas
from validation.service import is_disposable_email, check_valid_registration


# ─────────────────────────────────────────────────────────────────────────────
# is_disposable_email
# ─────────────────────────────────────────────────────────────────────────────

class TestIsDisposableEmail:
    def test_mailinator_bloqueado(self):
        assert is_disposable_email("user@mailinator.com") is True

    def test_yopmail_bloqueado(self):
        assert is_disposable_email("user@yopmail.com") is True

    def test_guerrillamail_bloqueado(self):
        assert is_disposable_email("test@guerrillamail.com") is True

    def test_gmail_permitido(self):
        assert is_disposable_email("joao@gmail.com") is False

    def test_hotmail_permitido(self):
        assert is_disposable_email("maria@hotmail.com") is False

    def test_dominio_empresa_permitido(self):
        assert is_disposable_email("carlos@empresa.com.br") is False

    def test_case_insensitive(self):
        assert is_disposable_email("user@MAILINATOR.COM") is True

    def test_formato_invalido_sem_arroba(self):
        assert is_disposable_email("emailsemarroba") is False


# ─────────────────────────────────────────────────────────────────────────────
# check_valid_registration
# ─────────────────────────────────────────────────────────────────────────────

def _make_auth_admin_response(confirmed: bool) -> MagicMock:
    user = MagicMock()
    user.email_confirmed_at = "2026-01-01T00:00:00Z" if confirmed else None
    resp = MagicMock()
    resp.user = user
    return resp


def _make_profile_result(zip_code: str) -> MagicMock:
    result = MagicMock()
    result.data = {"zip_code": zip_code}
    return result


class TestCheckValidRegistration:
    def test_email_confirmado_e_zip_preenchido_e_valido(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(confirmed=True)
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            _make_profile_result("90210")
        )
        result = check_valid_registration(sb, "user-001")
        assert result["is_valid"] is True
        assert result["email_confirmed"] is True
        assert result["has_real_action"] is True
        assert result["reasons"] == []

    def test_email_nao_confirmado_invalido(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(confirmed=False)
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            _make_profile_result("90210")
        )
        result = check_valid_registration(sb, "user-002")
        assert result["is_valid"] is False
        assert result["email_confirmed"] is False
        assert result["has_real_action"] is True
        assert "email_not_confirmed" in result["reasons"]

    def test_sem_zip_invalido(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(confirmed=True)
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            _make_profile_result("")
        )
        result = check_valid_registration(sb, "user-003")
        assert result["is_valid"] is False
        assert result["has_real_action"] is False
        assert "no_real_action" in result["reasons"]

    def test_sem_nenhum_criterio_invalido(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(confirmed=False)
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            _make_profile_result("")
        )
        result = check_valid_registration(sb, "user-004")
        assert result["is_valid"] is False
        assert len(result["reasons"]) == 2

    def test_erro_admin_api_gracioso(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.side_effect = Exception("Auth Admin indisponível")
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            _make_profile_result("10001")
        )
        result = check_valid_registration(sb, "user-005")
        assert result["email_confirmed"] is False
        assert result["is_valid"] is False

    def test_erro_profile_query_gracioso(self):
        sb = MagicMock()
        sb.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(confirmed=True)
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception(
            "DB timeout"
        )
        result = check_valid_registration(sb, "user-006")
        assert result["has_real_action"] is False
        assert result["is_valid"] is False


# ─────────────────────────────────────────────────────────────────────────────
# GET /users/me/validation-status
# ─────────────────────────────────────────────────────────────────────────────

class TestValidationStatusEndpoint:
    def test_usuario_valido_retorna_200_is_valid_true(self, client, mock_supabase):
        from tests.conftest import make_jwt

        mock_supabase.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(
            confirmed=True
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = _make_profile_result(
            "90210"
        )

        resp = client.get(
            "/users/me/validation-status",
            headers={"Authorization": f"Bearer {make_jwt('uid-valid')}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_valid"] is True
        assert body["email_confirmed"] is True
        assert body["has_real_action"] is True
        assert body["reasons"] == []

    def test_usuario_sem_email_confirmado_retorna_200_is_valid_false(
        self, client, mock_supabase
    ):
        from tests.conftest import make_jwt

        mock_supabase.auth.admin.get_user_by_id.return_value = _make_auth_admin_response(
            confirmed=False
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = _make_profile_result(
            "90210"
        )

        resp = client.get(
            "/users/me/validation-status",
            headers={"Authorization": f"Bearer {make_jwt('uid-unconfirmed')}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_valid"] is False
        assert "email_not_confirmed" in body["reasons"]

    def test_sem_autenticacao_retorna_403(self, client, mock_supabase):
        resp = client.get("/users/me/validation-status")
        assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Bloqueio de email descartável no cadastro
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistrationDisposableEmailBlock:
    VALID_PAYLOAD = {
        "email": "joao@gmail.com",
        "password": "Senha123!",
        "first_name": "João",
        "zip_code": "90210",
    }

    def test_email_descartavel_retorna_400(self, client, mock_supabase):
        payload = {**self.VALID_PAYLOAD, "email": "spammer@mailinator.com"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "temporário" in resp.json()["detail"].lower() or "permanente" in resp.json()["detail"].lower()

    def test_email_descartavel_nao_chama_supabase_signup(self, client, mock_supabase):
        """Garante que o bloqueio ocorre ANTES de criar o usuário no Supabase Auth."""
        payload = {**self.VALID_PAYLOAD, "email": "fake@yopmail.com"}
        client.post("/auth/register", json=payload)
        mock_supabase.auth.sign_up.assert_not_called()

    def test_email_descartavel_registra_evento_blocked(self, client, mock_supabase):
        """registration.blocked deve ser rastreado como analytics event."""
        table_mock = MagicMock()
        mock_supabase.table.return_value = table_mock

        payload = {**self.VALID_PAYLOAD, "email": "teste@guerrillamail.com"}
        client.post("/auth/register", json=payload)

        table_mock.insert.assert_called_once()
        event_payload = table_mock.insert.call_args[0][0]
        assert event_payload["event_type"] == "registration.blocked"
        assert event_payload["metadata"]["reason"] == "disposable_email"
        assert event_payload["metadata"]["domain"] == "guerrillamail.com"

    def test_email_gmail_cadastro_normal(self, client, mock_supabase):
        """Email legítimo não deve ser bloqueado."""
        auth_resp = MagicMock()
        auth_resp.user = MagicMock()
        auth_resp.user.id = "uid-normal"
        table_mock = MagicMock()
        table_mock.insert.return_value.execute.return_value = MagicMock()
        mock_supabase.auth.sign_up.return_value = auth_resp
        mock_supabase.table.return_value = table_mock

        resp = client.post("/auth/register", json=self.VALID_PAYLOAD)
        assert resp.status_code == 200
        mock_supabase.auth.sign_up.assert_called_once()
