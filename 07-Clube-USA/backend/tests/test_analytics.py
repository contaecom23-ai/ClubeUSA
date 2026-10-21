import pytest
from unittest.mock import MagicMock

# conftest.py já seta SUPABASE_URL e demais env vars antes dos imports do app
from analytics.service import track_event, VALID_EVENT_TYPES


# ---------------------------------------------------------------------------
# track_event — testes unitários (sem HTTP)
# ---------------------------------------------------------------------------

class TestTrackEvent:
    def test_user_registered_insere_evento(self):
        sb = MagicMock()
        track_event(sb, "user.registered", user_id="u-001")
        sb.table.assert_called_once_with("analytics_events")
        payload = sb.table.return_value.insert.call_args[0][0]
        assert payload["event_type"] == "user.registered"
        assert payload["user_id"] == "u-001"

    def test_user_logged_in_insere_evento(self):
        sb = MagicMock()
        track_event(sb, "user.logged_in", user_id="u-002")
        payload = sb.table.return_value.insert.call_args[0][0]
        assert payload["event_type"] == "user.logged_in"

    def test_referral_converted_com_metadata(self):
        sb = MagicMock()
        track_event(sb, "referral.converted", user_id="u-003", metadata={"slug": "joao-x7k2"})
        payload = sb.table.return_value.insert.call_args[0][0]
        assert payload["event_type"] == "referral.converted"
        assert payload["metadata"]["slug"] == "joao-x7k2"

    def test_tipo_desconhecido_nao_insere(self):
        sb = MagicMock()
        track_event(sb, "evento.invalido")
        sb.table.assert_not_called()

    def test_sem_user_id_nao_inclui_campo(self):
        sb = MagicMock()
        track_event(sb, "user.registered")
        payload = sb.table.return_value.insert.call_args[0][0]
        assert "user_id" not in payload

    def test_erro_supabase_nao_propaga(self):
        sb = MagicMock()
        sb.table.side_effect = Exception("DB indisponível")
        track_event(sb, "user.registered", user_id="u-004")  # não deve lançar


# ---------------------------------------------------------------------------
# GET /admin/analytics/summary — testes de endpoint
# ---------------------------------------------------------------------------

class TestAdminAnalyticsEndpoint:
    def test_sem_admin_key_configurada_retorna_503(self, client, mock_supabase, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
        resp = client.get("/admin/analytics/summary", headers={"X-Admin-Key": "qualquer"})
        assert resp.status_code == 503

    def test_key_errada_retorna_401(self, client, mock_supabase, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "chave-correta")
        resp = client.get("/admin/analytics/summary", headers={"X-Admin-Key": "chave-errada"})
        assert resp.status_code == 401

    def test_sem_header_retorna_422(self, client, mock_supabase, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "chave-correta")
        resp = client.get("/admin/analytics/summary")
        assert resp.status_code == 422

    def test_key_valida_retorna_resumo_completo(self, client, mock_supabase, monkeypatch):
        from config import settings
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "chave-admin-teste")

        # Configura mock: todas as queries de count retornam 5; data vazia para breakdown diário
        execute_result = MagicMock()
        execute_result.count = 5
        execute_result.data = []

        table = mock_supabase.table.return_value
        table.select.return_value.eq.return_value.gte.return_value.execute.return_value = execute_result
        table.select.return_value.gte.return_value.execute.return_value = execute_result

        resp = client.get(
            "/admin/analytics/summary",
            headers={"X-Admin-Key": "chave-admin-teste"},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert "signups_today" in body
        assert "signups_last_7d" in body
        assert "signups_last_30d" in body
        assert "logins_today" in body
        assert "logins_last_7d" in body
        assert "referral_clicks_last_7d" in body
        assert "referral_conversions_last_7d" in body
        assert "referral_conversion_rate" in body
        assert "daily_signups_last_30d" in body
        assert len(body["daily_signups_last_30d"]) == 31  # 30 dias + hoje

    def test_token_usuario_sem_admin_key_retorna_422(self, client, mock_supabase, monkeypatch):
        """Endpoint admin ignora Bearer token de usuário — exige X-Admin-Key."""
        from config import settings
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "chave-admin-teste")
        resp = client.get(
            "/admin/analytics/summary",
            headers={"Authorization": "Bearer jwt-de-usuario-qualquer"},
        )
        assert resp.status_code == 422
