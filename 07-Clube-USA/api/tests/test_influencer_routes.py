"""
Testes das rotas de influenciadores — Fase 1.3.
DB mockado via dependency override (sem Supabase real).
"""

import os
from unittest.mock import MagicMock

import pytest

from security import create_access_token


# ─── helpers ──────────────────────────────────────────────────────────────────

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key-for-unit-tests"}


def _token(user_id: str = "user-a") -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _setup_rpc_leaderboard(mock_db, rows: list) -> None:
    mock_db.rpc.return_value.execute.return_value.data = rows


def _setup_rpc_count(mock_db, count: int) -> None:
    """Configura get_valid_referral_count para retornar count."""
    mock_db.rpc.return_value.execute.return_value.data = count


def _setup_payouts_select(mock_db, rows: list) -> None:
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = rows


# ─── Badge logic (unit, sem HTTP) ─────────────────────────────────────────────

class TestBadgeComputation:
    def test_no_badge_below_50(self):
        from models import compute_badge
        badge, next_b, next_at = compute_badge(0)
        assert badge == "none"
        assert next_b == "parceiro"
        assert next_at == 50

    def test_parceiro_at_50(self):
        from models import compute_badge
        badge, next_b, next_at = compute_badge(50)
        assert badge == "parceiro"
        assert next_b == "embaixador"
        assert next_at == 250

    def test_embaixador_at_250(self):
        from models import compute_badge
        badge, next_b, next_at = compute_badge(250)
        assert badge == "embaixador"
        assert next_b == "hall_da_fama"
        assert next_at == 1000

    def test_hall_da_fama_at_1000(self):
        from models import compute_badge
        badge, next_b, next_at = compute_badge(1000)
        assert badge == "hall_da_fama"
        assert next_b is None
        assert next_at is None

    def test_exact_boundary_999(self):
        from models import compute_badge
        badge, _, _ = compute_badge(999)
        assert badge == "embaixador"


# ─── GET /api/influencer/leaderboard ──────────────────────────────────────────

class TestLeaderboard:
    def test_public_no_auth_required(self, client, mock_db):
        _setup_rpc_leaderboard(mock_db, [])
        r = client.get("/api/influencer/leaderboard")
        assert r.status_code == 200
        body = r.json()
        assert "entries" in body
        assert "payout_rate_usd" in body

    def test_returns_ranked_entries(self, client, mock_db):
        rows = [
            {"user_id": "u1", "display_name": "João", "city": "Miami", "state": "FL", "valid_referrals": 300},
            {"user_id": "u2", "display_name": "Maria", "city": "Orlando", "state": "FL", "valid_referrals": 55},
        ]
        _setup_rpc_leaderboard(mock_db, rows)

        r = client.get("/api/influencer/leaderboard")
        assert r.status_code == 200
        entries = r.json()["entries"]
        assert len(entries) == 2
        assert entries[0]["rank"] == 1
        assert entries[0]["valid_referrals"] == 300
        assert entries[0]["badge"] == "embaixador"   # 300 >= 250
        assert entries[1]["rank"] == 2
        assert entries[1]["badge"] == "parceiro"      # 55 >= 50

    def test_no_email_in_leaderboard(self, client, mock_db):
        """PII (email, telefone) nunca aparece no leaderboard."""
        rows = [
            {"user_id": "u1", "display_name": "João", "city": "Miami", "state": "FL", "valid_referrals": 100},
        ]
        _setup_rpc_leaderboard(mock_db, rows)

        r = client.get("/api/influencer/leaderboard")
        entry = r.json()["entries"][0]
        assert "email" not in entry
        assert "phone" not in entry
        assert "password" not in entry

    def test_payout_rate_null_when_not_configured(self, client, mock_db):
        _setup_rpc_leaderboard(mock_db, [])
        # Default PAYOUT_RATE_USD = 0.0 → payout_rate_usd should be None
        r = client.get("/api/influencer/leaderboard")
        assert r.json()["payout_rate_usd"] is None


# ─── GET /api/influencer/status ───────────────────────────────────────────────

class TestInfluencerStatus:
    def test_requires_auth(self, client, mock_db):
        r = client.get("/api/influencer/status")
        assert r.status_code == 403

    def test_status_no_referrals(self, client, mock_db):
        _setup_rpc_count(mock_db, 0)
        _setup_payouts_select(mock_db, [])

        r = client.get("/api/influencer/status", headers=_token())
        assert r.status_code == 200
        body = r.json()
        assert body["valid_referrals"] == 0
        assert body["badge"] == "none"
        assert body["next_badge"] == "parceiro"
        assert body["total_paid_usd"] == 0.0

    def test_status_shows_badge_for_50_referrals(self, client, mock_db):
        _setup_rpc_count(mock_db, 50)
        _setup_payouts_select(mock_db, [])

        r = client.get("/api/influencer/status", headers=_token())
        assert r.status_code == 200
        assert r.json()["badge"] == "parceiro"

    def test_status_estimated_earning_null_when_rate_not_set(self, client, mock_db):
        _setup_rpc_count(mock_db, 100)
        _setup_payouts_select(mock_db, [])

        r = client.get("/api/influencer/status", headers=_token())
        # PAYOUT_RATE_USD = 0.0 (default) → estimativa None
        assert r.json()["estimated_earning_usd"] is None

    def test_status_total_paid_includes_all_payouts(self, client, mock_db):
        _setup_rpc_count(mock_db, 80)
        _setup_payouts_select(mock_db, [{"amount_usd": "25.00"}, {"amount_usd": "10.00"}])

        r = client.get("/api/influencer/status", headers=_token())
        assert r.json()["total_paid_usd"] == 35.0


# ─── Admin: GET /api/admin/influencer/pending ─────────────────────────────────

class TestAdminPending:
    def test_requires_admin_key(self, client, mock_db):
        r = client.get("/api/admin/influencer/pending")
        assert r.status_code == 403

    def test_wrong_admin_key_rejected(self, client, mock_db):
        r = client.get("/api/admin/influencer/pending", headers={"X-Admin-Key": "wrong"})
        assert r.status_code == 403

    def test_returns_empty_when_rate_not_configured(self, client, mock_db):
        """Se PAYOUT_RATE_USD = 0, não há como calcular pendências."""
        r = client.get("/api/admin/influencer/pending", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert r.json() == []


# ─── Admin: POST /api/admin/influencer/payouts ────────────────────────────────

class TestRegisterPayout:
    def test_requires_admin_key(self, client, mock_db):
        r = client.post("/api/admin/influencer/payouts", json={
            "user_id": "u1", "amount_usd": 50.0, "payment_method": "paypal"
        })
        assert r.status_code == 403

    def test_register_payout_success(self, client, mock_db):
        # Usuário existe
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "u1"}]
        # rpc count
        mock_db.rpc.return_value.execute.return_value.data = 75
        # insert retorna o registro
        mock_db.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "payout-1",
            "user_id": "u1",
            "valid_referrals": 75,
            "amount_usd": "50.00",
            "payment_method": "paypal",
            "payment_ref": "PP-12345",
            "notes": None,
            "created_at": "2026-07-27T00:00:00+00:00",
        }]

        r = client.post(
            "/api/admin/influencer/payouts",
            json={"user_id": "u1", "amount_usd": 50.0, "payment_method": "paypal", "payment_ref": "PP-12345"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["user_id"] == "u1"
        assert body["amount_usd"] == 50.0
        assert body["payment_method"] == "paypal"

    def test_register_payout_user_not_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        r = client.post(
            "/api/admin/influencer/payouts",
            json={"user_id": "ghost", "amount_usd": 10.0, "payment_method": "venmo"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 404

    def test_negative_amount_rejected(self, client, mock_db):
        r = client.post(
            "/api/admin/influencer/payouts",
            json={"user_id": "u1", "amount_usd": -5.0, "payment_method": "zelle"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_invalid_payment_method_rejected(self, client, mock_db):
        r = client.post(
            "/api/admin/influencer/payouts",
            json={"user_id": "u1", "amount_usd": 10.0, "payment_method": "bitcoin"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422
