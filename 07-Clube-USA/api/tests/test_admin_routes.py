"""Testes das rotas admin — DB mockado, chave admin configurada no conftest."""
import pytest

ADMIN_KEY = "test-admin-key-for-unit-tests"
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}

# Dados de usuário para os testes de métricas
_USER_CONFIRMED = {
    "id": "u1",
    "email_confirmed_at": "2026-07-10T00:00:00+00:00",
    "referred_by_user_id": None,
    "created_at": "2026-07-10T00:00:00+00:00",
    "state": None, "city": None, "zip_code": None,
}
_USER_UNCONFIRMED_REFERRED = {
    "id": "u2",
    "email_confirmed_at": None,
    "referred_by_user_id": "u1",
    "created_at": "2026-07-15T00:00:00+00:00",
    "state": None, "city": None, "zip_code": None,
}

_EVENT_LOGIN = {"event_type": "user_login", "created_at": "2026-07-15T00:00:00+00:00"}
_EVENT_REGISTER = {"event_type": "user_registered", "created_at": "2026-07-15T00:00:00+00:00"}


def _set_users(mock_db, data):
    """Configura mock para query de usuários: select(...).execute()"""
    mock_db.table.return_value.select.return_value.execute.return_value.data = data


def _set_events(mock_db, data):
    """Configura mock para query de eventos: select(...).gte(...).execute()"""
    mock_db.table.return_value.select.return_value.gte.return_value.execute.return_value.data = data


# ─── /api/admin/metrics ───────────────────────────────────────────────────────

class TestAdminMetrics:
    def test_no_key_returns_403(self, client, mock_db):
        r = client.get("/api/admin/metrics")
        assert r.status_code == 403

    def test_wrong_key_returns_403(self, client, mock_db):
        r = client.get("/api/admin/metrics", headers={"X-Admin-Key": "wrong-key"})
        assert r.status_code == 403

    def test_empty_database(self, client, mock_db):
        _set_users(mock_db, [])
        _set_events(mock_db, [])

        r = client.get("/api/admin/metrics", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["users"]["total"] == 0
        assert data["users"]["confirmation_rate"] == 0.0
        assert data["referrals"]["total_attributed"] == 0
        assert data["referrals"]["attribution_rate"] == 0.0
        assert data["events"]["logins_last_7d"] == 0
        assert "as_of" in data

    def test_with_users_and_events(self, client, mock_db):
        _set_users(mock_db, [_USER_CONFIRMED, _USER_UNCONFIRMED_REFERRED])
        _set_events(mock_db, [_EVENT_LOGIN, _EVENT_REGISTER])

        r = client.get("/api/admin/metrics", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()

        assert data["users"]["total"] == 2
        assert data["users"]["confirmed"] == 1
        assert data["users"]["unconfirmed"] == 1
        assert 0 < data["users"]["confirmation_rate"] < 1

        assert data["referrals"]["total_attributed"] == 1
        assert data["referrals"]["attribution_rate"] == 0.5

        assert data["events"]["logins_last_30d"] == 1
        assert data["events"]["registrations_last_30d"] == 1

    def test_all_users_confirmed(self, client, mock_db):
        _set_users(mock_db, [_USER_CONFIRMED])
        _set_events(mock_db, [])

        r = client.get("/api/admin/metrics", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["users"]["confirmation_rate"] == 1.0
        assert data["users"]["unconfirmed"] == 0

    def test_response_has_all_fields(self, client, mock_db):
        _set_users(mock_db, [])
        _set_events(mock_db, [])

        r = client.get("/api/admin/metrics", headers=ADMIN_HEADERS)
        data = r.json()

        # Verifica estrutura completa
        assert set(data["users"].keys()) == {
            "total", "confirmed", "unconfirmed", "confirmation_rate",
            "new_last_7d", "new_last_30d", "valid_registrations", "valid_rate",
        }
        assert set(data["referrals"].keys()) == {"total_attributed", "attribution_rate"}
        assert set(data["events"].keys()) == {
            "logins_last_7d", "logins_last_30d",
            "registrations_last_7d", "registrations_last_30d",
        }
        assert "as_of" in data

    def test_valid_registrations_count(self, client, mock_db):
        # Usuário confirmado com localização = válido
        # Usuário confirmado sem localização = NÃO válido
        # Usuário não confirmado = NÃO válido
        confirmed_with_location = {
            "id": "u1", "email_confirmed_at": "2026-07-01T00:00:00+00:00",
            "referred_by_user_id": None, "created_at": "2026-07-01T00:00:00+00:00",
            "state": "FL", "city": "Miami", "zip_code": None,
        }
        confirmed_no_location = {
            "id": "u2", "email_confirmed_at": "2026-07-01T00:00:00+00:00",
            "referred_by_user_id": None, "created_at": "2026-07-01T00:00:00+00:00",
            "state": None, "city": None, "zip_code": None,
        }
        unconfirmed = {
            "id": "u3", "email_confirmed_at": None,
            "referred_by_user_id": None, "created_at": "2026-07-01T00:00:00+00:00",
            "state": "CA", "city": "LA", "zip_code": "90001",
        }
        _set_users(mock_db, [confirmed_with_location, confirmed_no_location, unconfirmed])
        _set_events(mock_db, [])

        r = client.get("/api/admin/metrics", headers=ADMIN_HEADERS)
        data = r.json()
        assert data["users"]["valid_registrations"] == 1
        assert data["users"]["valid_rate"] == pytest.approx(1/3, abs=0.01)
