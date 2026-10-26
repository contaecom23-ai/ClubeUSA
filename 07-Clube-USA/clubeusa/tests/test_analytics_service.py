# ============================================================
#  tests/test_analytics_service.py — Clube USA
#  Testes adicionais: get_referral_stats, get_geographic_breakdown, get_overview
#  (o núcleo do analytics_service é coberto por test_analytics.py)
# ============================================================
import pytest
from unittest.mock import MagicMock


def _table_mock(data=None, count=None):
    m = MagicMock()
    result = MagicMock()
    result.data = data or []
    result.count = count if count is not None else len(data or [])
    m.select.return_value = m
    m.eq.return_value = m
    m.gt.return_value = m
    m.gte.return_value = m
    m.in_.return_value = m
    m.order.return_value = m
    m.limit.return_value = m
    m.is_.return_value = m
    m.execute.return_value = result
    return m


# ============================================================
#  get_referral_stats
# ============================================================

class TestGetReferralStats:
    def _sb(self, mocker, referrals, member_count=10):
        sb = MagicMock()
        ref_mock = _table_mock(data=referrals)
        mem_mock = _table_mock(data=[], count=member_count)
        sb.table.side_effect = lambda n: ref_mock if n == "referrals" else mem_mock
        mocker.patch("services.analytics_service._supabase", return_value=sb)

    def test_returns_expected_keys(self, mocker):
        from services.analytics_service import get_referral_stats
        self._sb(mocker, [])
        r = get_referral_stats()
        assert "total_referrals" in r
        assert "confirmed_referrals" in r
        assert "unique_referrers" in r
        assert "referrer_adoption_pct" in r
        assert "confirmation_rate_pct" in r
        assert "top_referrers" in r

    def test_unique_referrers_deduped(self, mocker):
        from services.analytics_service import get_referral_stats
        referrals = [
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r2", "status": "pending"},
        ]
        self._sb(mocker, referrals, member_count=10)
        r = get_referral_stats()
        assert r["unique_referrers"] == 2
        assert r["total_referrals"] == 3
        assert r["confirmed_referrals"] == 2

    def test_adoption_rate_calculation(self, mocker):
        from services.analytics_service import get_referral_stats
        referrals = [
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r2", "status": "confirmed"},
        ]
        self._sb(mocker, referrals, member_count=10)
        r = get_referral_stats()
        assert r["referrer_adoption_pct"] == 20.0  # 2/10

    def test_zero_referrals(self, mocker):
        from services.analytics_service import get_referral_stats
        self._sb(mocker, [], member_count=5)
        r = get_referral_stats()
        assert r["total_referrals"] == 0
        assert r["confirmation_rate_pct"] == 0.0
        assert r["referrer_adoption_pct"] == 0.0


# ============================================================
#  get_geographic_breakdown
# ============================================================

class TestGetGeographicBreakdown:
    def test_top_states_sorted_by_count(self, mocker):
        from services.analytics_service import get_geographic_breakdown
        sb = MagicMock()
        members = [
            {"state": "FL"}, {"state": "FL"}, {"state": "FL"},
            {"state": "TX"}, {"state": "TX"},
            {"state": "CA"},
        ]
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        r = get_geographic_breakdown()
        assert r["total_members"] == 6
        assert r["top_states"][0]["state"] == "FL"
        assert r["top_states"][0]["members"] == 3

    def test_limits_to_10_states(self, mocker):
        from services.analytics_service import get_geographic_breakdown
        sb = MagicMock()
        members = [{"state": f"S{i}"} for i in range(15)]
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        r = get_geographic_breakdown()
        assert len(r["top_states"]) <= 10

    def test_handles_empty_state(self, mocker):
        from services.analytics_service import get_geographic_breakdown
        sb = MagicMock()
        members = [{"state": None}, {"state": ""}, {"state": "CA"}]
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        r = get_geographic_breakdown()
        assert r["total_members"] == 3


# ============================================================
#  get_overview
# ============================================================

class TestGetOverview:
    def test_overview_composes_all_sub_functions(self, mocker):
        from services import analytics_service as svc
        mocker.patch.object(svc, "get_funnel",               return_value={"funnel": {"registrations_total": 0}})
        mocker.patch.object(svc, "get_growth",               return_value=[])
        mocker.patch.object(svc, "get_top_referrers",        return_value=[])
        mocker.patch.object(svc, "get_engagement",           return_value={"clicks_last_7d": 0, "top_categories": []})
        mocker.patch.object(svc, "get_geographic_breakdown", return_value={"total_members": 0, "top_states": []})

        r = svc.get_overview()
        assert "as_of" in r
        assert "funnel" in r
        assert "growth_30d" in r
        assert "top_referrers" in r
        assert "engagement" in r
        assert "geographic" in r

    def test_overview_unwraps_funnel_key(self, mocker):
        from services import analytics_service as svc
        mocker.patch.object(svc, "get_funnel",               return_value={"funnel": {"registrations_total": 42}})
        mocker.patch.object(svc, "get_growth",               return_value=[])
        mocker.patch.object(svc, "get_top_referrers",        return_value=[])
        mocker.patch.object(svc, "get_engagement",           return_value={"clicks_last_7d": 0, "top_categories": []})
        mocker.patch.object(svc, "get_geographic_breakdown", return_value={"total_members": 0, "top_states": []})

        r = svc.get_overview()
        # funnel dict should be the inner dict, not wrapped in {"funnel": {}}
        assert r["funnel"]["registrations_total"] == 42
