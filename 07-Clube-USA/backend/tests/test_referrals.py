"""
Testes do sistema de REFERRAL — Fase 0.2.

Cobertura:
- GET /referrals/me: caminho feliz, sem autenticação
- POST /referrals/click/{slug}: slug válido, slug inválido, formato inválido
- Integração com registro: slug gerado no cadastro, referred_by_slug salvo, slug inválido ignorado
"""

from unittest.mock import MagicMock, call

from tests.conftest import make_jwt

VALID_REGISTER_PAYLOAD = {
    "email": "ana@example.com",
    "password": "Senha123!",
    "first_name": "Ana",
    "last_name": "Lima",
    "zip_code": "33101",
    "phone": "305-555-0001",
}


# ─────────────────── GET /referrals/me ───────────────────

class TestGetMyReferralStats:
    def test_returns_stats_with_slug(self, client, mock_supabase):
        token = make_jwt("user-ref-01")

        profile_mock = MagicMock()
        profile_mock.data = {"referral_slug": "ana-abc1"}

        signup_mock = MagicMock()
        signup_mock.count = 3

        click_mock = MagicMock()
        click_mock.count = 10

        # Encadeia respostas na ordem de chamada de .execute()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_mock
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            signup_mock,
            click_mock,
        ]

        resp = client.get(
            "/referrals/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "ana-abc1"
        assert data["signup_count"] == 3
        assert data["click_count"] == 10
        assert "/i/ana-abc1" in data["referral_url"]

    def test_requires_auth(self, client, mock_supabase):
        resp = client.get("/referrals/me")
        assert resp.status_code == 403

    def test_no_slug_returns_zeros(self, client, mock_supabase):
        token = make_jwt("user-no-slug")

        profile_mock = MagicMock()
        profile_mock.data = {"referral_slug": None}

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_mock

        resp = client.get(
            "/referrals/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] is None
        assert data["signup_count"] == 0
        assert data["click_count"] == 0


# ─────────────────── POST /referrals/click/{slug} ────────

class TestTrackClick:
    def test_valid_slug_returns_204(self, client, mock_supabase):
        profile_mock = MagicMock()
        profile_mock.data = [{"id": "some-user-id"}]

        click_insert_mock = MagicMock()

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = profile_mock
        mock_supabase.table.return_value.insert.return_value.execute.return_value = click_insert_mock

        resp = client.post("/referrals/click/ana-abc1")
        assert resp.status_code == 204

    def test_unknown_slug_returns_404(self, client, mock_supabase):
        empty_mock = MagicMock()
        empty_mock.data = []

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = empty_mock

        resp = client.post("/referrals/click/naoexiste")
        assert resp.status_code == 404

    def test_invalid_slug_format_returns_422(self, client, mock_supabase):
        # Slug com caracteres inválidos (ex: /../ path traversal attempt)
        resp = client.post("/referrals/click/../../etc")
        assert resp.status_code in (404, 422)  # path param inválido ou 404 no slug

    def test_slug_too_short_returns_422(self, client, mock_supabase):
        resp = client.post("/referrals/click/ab")
        assert resp.status_code == 422


# ─────────────── Integração: register + referral ─────────

class TestRegisterWithReferral:
    def _setup_register_mocks(self, mock_supabase, user_id: str = "new-user-id"):
        auth_resp = MagicMock()
        auth_resp.user = MagicMock()
        auth_resp.user.id = user_id
        mock_supabase.auth.sign_up.return_value = auth_resp

        # Slug uniqueness check retorna vazio (slug disponível)
        empty_mock = MagicMock()
        empty_mock.data = []

        table_mock = MagicMock()
        table_mock.select.return_value.eq.return_value.execute.return_value = empty_mock
        table_mock.insert.return_value.execute.return_value = MagicMock()

        mock_supabase.table.return_value = table_mock
        return table_mock

    def test_register_generates_referral_slug(self, client, mock_supabase):
        table_mock = self._setup_register_mocks(mock_supabase)

        resp = client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        assert resp.status_code == 200

        # O insert do perfil deve conter referral_slug
        insert_calls = table_mock.insert.call_args_list
        profile_insert = insert_calls[0][0][0]
        assert "referral_slug" in profile_insert
        assert profile_insert["referral_slug"]  # não vazio

    def test_register_with_valid_ref_stores_referred_by(self, client, mock_supabase):
        auth_resp = MagicMock()
        auth_resp.user = MagicMock()
        auth_resp.user.id = "new-user-xyz"
        mock_supabase.auth.sign_up.return_value = auth_resp

        table_mock = MagicMock()

        # 1a chamada: verifica unicidade do novo slug -> vazio (disponível)
        # 2a chamada: valida referred_by_slug -> retorna dado (existe)
        slug_unique_mock = MagicMock()
        slug_unique_mock.data = []

        ref_exists_mock = MagicMock()
        ref_exists_mock.data = [{"id": "referrer-id"}]

        table_mock.select.return_value.eq.return_value.execute.side_effect = [
            slug_unique_mock,
            ref_exists_mock,
        ]
        table_mock.insert.return_value.execute.return_value = MagicMock()
        mock_supabase.table.return_value = table_mock

        payload = {**VALID_REGISTER_PAYLOAD, "referred_by_slug": "maria-xyz9"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 200

        # register_user faz múltiplos inserts (perfil + analytics events).
        # Buscamos o insert do perfil (contém 'id').
        all_inserts = [call[0][0] for call in table_mock.insert.call_args_list]
        profile_insert = next((d for d in all_inserts if "id" in d), None)
        assert profile_insert is not None, "Insert de perfil não encontrado"
        assert profile_insert.get("referred_by_slug") == "maria-xyz9"

    def test_register_with_invalid_ref_silently_ignored(self, client, mock_supabase):
        table_mock = self._setup_register_mocks(mock_supabase)

        payload = {**VALID_REGISTER_PAYLOAD, "referred_by_slug": "naoexiste-0000"}
        resp = client.post("/auth/register", json=payload)

        # Cadastro não falha com código inválido
        assert resp.status_code == 200

    def test_register_invalid_ref_format_returns_422(self, client, mock_supabase):
        payload = {**VALID_REGISTER_PAYLOAD, "referred_by_slug": "!!invalid!!"}
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 422
