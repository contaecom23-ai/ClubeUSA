"""
Testes da Fase 1.3: Programa de Influenciadores.

Cobertura:
- compute_tier: todos os limiares (0, 49, 50, 249, 250, 999, 1000)
- compute_tier_progress: progresso e tier seguinte corretos
- GET /influencer/me: auth obrigatória, IDOR (user_id do token, nunca do cliente), stats corretas, slug nulo
- GET /admin/influencer/leaderboard: admin key obrigatória, resposta correta
"""

import pytest
from unittest.mock import MagicMock, call, patch
from fastapi.testclient import TestClient

from influencer.schemas import InfluencerTier
from influencer.service import compute_tier, compute_tier_progress, get_influencer_stats, get_leaderboard


# ---------------------------------------------------------------------------
# compute_tier
# ---------------------------------------------------------------------------

class TestComputeTier:
    def test_zero_referrals(self):
        assert compute_tier(0) == InfluencerTier.none

    def test_below_parceiro(self):
        assert compute_tier(49) == InfluencerTier.none

    def test_exactly_parceiro(self):
        assert compute_tier(50) == InfluencerTier.parceiro

    def test_above_parceiro(self):
        assert compute_tier(100) == InfluencerTier.parceiro

    def test_below_embaixador(self):
        assert compute_tier(249) == InfluencerTier.parceiro

    def test_exactly_embaixador(self):
        assert compute_tier(250) == InfluencerTier.embaixador

    def test_above_embaixador(self):
        assert compute_tier(500) == InfluencerTier.embaixador

    def test_below_hall(self):
        assert compute_tier(999) == InfluencerTier.embaixador

    def test_exactly_hall(self):
        assert compute_tier(1000) == InfluencerTier.hall_da_fama

    def test_above_hall(self):
        assert compute_tier(5000) == InfluencerTier.hall_da_fama


# ---------------------------------------------------------------------------
# compute_tier_progress
# ---------------------------------------------------------------------------

class TestComputeTierProgress:
    def test_zero_progress(self):
        p = compute_tier_progress(0)
        assert p.next_tier == InfluencerTier.parceiro
        assert p.referrals_needed == 50
        assert p.progress_pct == 0

    def test_halfway_to_parceiro(self):
        p = compute_tier_progress(25)
        assert p.next_tier == InfluencerTier.parceiro
        assert p.referrals_needed == 25
        assert p.progress_pct == 50

    def test_at_parceiro(self):
        p = compute_tier_progress(50)
        assert p.next_tier == InfluencerTier.embaixador
        assert p.referrals_needed == 200

    def test_at_embaixador(self):
        p = compute_tier_progress(250)
        assert p.next_tier == InfluencerTier.hall_da_fama
        assert p.referrals_needed == 750

    def test_at_hall(self):
        p = compute_tier_progress(1000)
        assert p.next_tier is None
        assert p.referrals_needed == 0
        assert p.progress_pct == 100


# ---------------------------------------------------------------------------
# GET /influencer/me (endpoint)
# ---------------------------------------------------------------------------

class TestInfluencerMeEndpoint:
    def test_requires_auth(self, client):
        resp = client.get("/influencer/me")
        assert resp.status_code == 403

    def test_invalid_token_rejected(self, client):
        resp = client.get("/influencer/me", headers={"Authorization": "Bearer badtoken"})
        assert resp.status_code == 401

    def test_stats_returned_for_valid_user(self, client, mock_supabase):
        from tests.conftest import make_jwt
        token = make_jwt("user-abc")

        # profile query
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"referral_slug": "joao-ab12"}
        )
        # valid referral count
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(count=10)
        # total referral count
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=15)

        resp = client.get("/influencer/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "joao-ab12"
        assert data["tier"] == InfluencerTier.none
        assert data["valid_referral_count"] == 10
        assert data["total_referral_count"] == 15
        assert data["tier_progress"]["next_tier"] == InfluencerTier.parceiro

    def test_user_id_comes_from_token_not_client(self, client, mock_supabase):
        """IDOR: user_id nunca vem de query param ou body."""
        from tests.conftest import make_jwt
        # Token para user-111; tentativa de injetar user-999 via query param (deve ser ignorado)
        token = make_jwt("user-111")

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"referral_slug": "valid-slug"}
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(count=0)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=0)

        resp = client.get("/influencer/me?user_id=user-999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        # Verifica que o query ao DB usou user-111, não user-999
        first_eq_call = mock_supabase.table.return_value.select.return_value.eq.call_args_list[0]
        assert "user-111" in first_eq_call[0]

    def test_profile_not_found_returns_404(self, client, mock_supabase):
        from tests.conftest import make_jwt
        token = make_jwt("user-ghost")

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("not found")

        resp = client.get("/influencer/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_no_slug_returns_zero_stats(self, client, mock_supabase):
        from tests.conftest import make_jwt
        token = make_jwt("user-new")

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"referral_slug": None}
        )

        resp = client.get("/influencer/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] is None
        assert data["valid_referral_count"] == 0
        assert data["pending_credits_cents"] == 0

    def test_credits_computed_correctly(self, client, mock_supabase):
        """10 valid referrals × $2.00 = $20.00 pending credits."""
        from tests.conftest import make_jwt
        token = make_jwt("user-rich")

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"referral_slug": "rich-user"}
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(count=10)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=12)

        resp = client.get("/influencer/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending_credits_cents"] == 2000  # 10 × 200 cents
        assert data["pending_credits_usd"] == "20.00"
        assert data["payment_per_referral_usd"] == "2.00"
        assert data["monthly_cap_usd"] == "100.00"

    def test_parceiro_tier_at_50_referrals(self, client, mock_supabase):
        from tests.conftest import make_jwt
        token = make_jwt("user-par")

        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"referral_slug": "par-slug"}
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(count=50)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=60)

        resp = client.get("/influencer/me", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        assert data["tier"] == "parceiro"
        assert data["tier_progress"]["next_tier"] == "embaixador"


# ---------------------------------------------------------------------------
# GET /admin/influencer/leaderboard
# ---------------------------------------------------------------------------

class TestInfluencerLeaderboard:
    def test_no_admin_key_returns_422(self, client):
        resp = client.get("/admin/influencer/leaderboard")
        assert resp.status_code == 422

    def test_wrong_admin_key_returns_401(self, client):
        from config import settings
        settings.ADMIN_API_KEY = "correct-key"
        try:
            resp = client.get("/admin/influencer/leaderboard", headers={"X-Admin-Key": "wrong-key"})
            assert resp.status_code == 401
        finally:
            settings.ADMIN_API_KEY = ""

    def test_no_admin_configured_returns_503(self, client, mock_supabase):
        import os
        with patch.dict(os.environ, {"ADMIN_API_KEY": ""}):
            from config import settings
            original = settings.ADMIN_API_KEY
            settings.ADMIN_API_KEY = ""
            try:
                resp = client.get("/admin/influencer/leaderboard", headers={"X-Admin-Key": "anything"})
                assert resp.status_code == 503
            finally:
                settings.ADMIN_API_KEY = original

    def test_valid_admin_key_returns_leaderboard(self, client, mock_supabase):
        import os
        from config import settings
        settings.ADMIN_API_KEY = "test-admin-key-for-influencer"

        # Query 1: referred_by_slug + zip counts
        mock_supabase.table.return_value.select.return_value.neq.return_value.neq.return_value.execute.return_value = MagicMock(
            data=[
                {"referred_by_slug": "ana-x1y2"},
                {"referred_by_slug": "ana-x1y2"},
                {"referred_by_slug": "bob-z3w4"},
            ]
        )
        # Query 2: profile names
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[
                {"referral_slug": "ana-x1y2", "first_name": "Ana"},
                {"referral_slug": "bob-z3w4", "first_name": "Bob"},
            ]
        )

        resp = client.get("/admin/influencer/leaderboard", headers={"X-Admin-Key": "test-admin-key-for-influencer"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_influencers"] == 2
        assert len(data["entries"]) == 2
        assert data["entries"][0]["slug"] == "ana-x1y2"
        assert data["entries"][0]["rank"] == 1
        assert data["entries"][0]["valid_referral_count"] == 2
        assert data["entries"][1]["slug"] == "bob-z3w4"
        assert data["entries"][1]["rank"] == 2

        settings.ADMIN_API_KEY = ""

    def test_empty_leaderboard(self, client, mock_supabase):
        from config import settings
        settings.ADMIN_API_KEY = "test-admin-key-empty"

        mock_supabase.table.return_value.select.return_value.neq.return_value.neq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        resp = client.get("/admin/influencer/leaderboard", headers={"X-Admin-Key": "test-admin-key-empty"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries"] == []
        assert data["total_influencers"] == 0

        settings.ADMIN_API_KEY = ""

    def test_bearer_token_of_user_cannot_access_leaderboard(self, client, mock_supabase):
        """Isolamento: token de usuário comum não serve como X-Admin-Key."""
        from tests.conftest import make_jwt
        token = make_jwt("user-hacker")
        resp = client.get(
            "/admin/influencer/leaderboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422  # X-Admin-Key ausente
