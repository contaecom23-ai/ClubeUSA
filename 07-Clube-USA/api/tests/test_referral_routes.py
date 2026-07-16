"""Testes das rotas de referral — DB mockado."""
from unittest.mock import MagicMock

import pytest

from security import create_access_token


def _auth_header(user_id: str = "user-123") -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ─── /i/{code} — redirect ─────────────────────────────────────────────────────

class TestReferralRedirect:
    def test_redirects_to_register(self, client, mock_db):
        r = client.get("/i/abc123de", follow_redirects=False)
        assert r.status_code == 302
        assert "register.html" in r.headers["location"]
        assert "ref=abc123de" in r.headers["location"]

    def test_redirect_with_any_code(self, client, mock_db):
        # Nenhuma validação no redirect — anti-scanning
        r = client.get("/i/codigo-qualquer", follow_redirects=False)
        assert r.status_code == 302

    def test_redirect_encodes_special_chars(self, client, mock_db):
        r = client.get("/i/abc%20xyz", follow_redirects=False)
        assert r.status_code == 302
        location = r.headers["location"]
        assert "ref=" in location
        assert " " not in location  # espaço deve estar codificado


# ─── GET /api/referral/stats ──────────────────────────────────────────────────

class TestReferralStats:
    def test_success_with_referrals(self, client, mock_db):
        exec_mock = MagicMock()
        exec_mock.side_effect = [
            MagicMock(data=[{"referral_code": "abc123de"}]),  # user lookup
            MagicMock(data=[{"id": "u1"}, {"id": "u2"}]),    # referred users
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute = exec_mock

        r = client.get("/api/referral/stats", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["referral_code"] == "abc123de"
        assert data["referral_count"] == 2
        assert "abc123de" in data["referral_url"]

    def test_zero_referrals(self, client, mock_db):
        exec_mock = MagicMock()
        exec_mock.side_effect = [
            MagicMock(data=[{"referral_code": "xyz789ab"}]),
            MagicMock(data=[]),
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute = exec_mock

        r = client.get("/api/referral/stats", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["referral_count"] == 0
        assert data["referral_code"] == "xyz789ab"

    def test_no_auth_returns_401(self, client, mock_db):
        r = client.get("/api/referral/stats")
        assert r.status_code in (401, 403)

    def test_user_not_found_returns_404(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        r = client.get("/api/referral/stats", headers=_auth_header())
        assert r.status_code == 404

    def test_lazy_code_generation_for_old_users(self, client, mock_db):
        # Usuários sem código (pré-Fase 0.2) devem receber um gerado na hora
        exec_mock = MagicMock()
        exec_mock.side_effect = [
            MagicMock(data=[{"referral_code": None}]),  # usuário sem código
            MagicMock(data=[]),                          # sem colisão no código gerado
            MagicMock(data=[]),                          # usuários indicados: nenhum
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute = exec_mock

        r = client.get("/api/referral/stats", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["referral_code"] is not None
        assert len(data["referral_code"]) == 8
        assert data["referral_count"] == 0
        assert data["referral_url"] is not None

    def test_referral_url_format(self, client, mock_db):
        exec_mock = MagicMock()
        exec_mock.side_effect = [
            MagicMock(data=[{"referral_code": "test1234"}]),
            MagicMock(data=[]),
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute = exec_mock

        r = client.get("/api/referral/stats", headers=_auth_header())
        assert r.status_code == 200
        url = r.json()["referral_url"]
        assert url.endswith("/i/test1234")
