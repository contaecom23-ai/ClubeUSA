# ============================================================
#  tests/test_analytics_service.py — Clube USA
#  Testes do analytics_service.py — Fase 0.3
# ============================================================
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


def _make_member(created_at=None, email_enc=None, email_confirmed=False, state="CA", status="active"):
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    return {
        "id": "m1",
        "created_at": created_at,
        "email_enc": email_enc,
        "email_confirmed": email_confirmed,
        "state": state,
        "status": status,
    }


def _table_mock(data=None, count=None):
    """Cria mock de tabela Supabase com suporte a chaining."""
    m = MagicMock()
    result = MagicMock()
    result.data = data or []
    result.count = count
    m.select.return_value = m
    m.gte.return_value = m
    m.in_.return_value = m
    m.execute.return_value = result
    return m


# ============================================================
#  get_growth
# ============================================================

class TestGetGrowth:
    def test_returns_expected_keys(self, mocker):
        from services.analytics_service import get_growth
        sb = MagicMock()
        sb.table.return_value = _table_mock(data=[])
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_growth(7)
        assert "period_days" in result
        assert "total_in_period" in result
        assert "series" in result
        assert result["period_days"] == 7

    def test_series_has_correct_length(self, mocker):
        from services.analytics_service import get_growth
        sb = MagicMock()
        sb.table.return_value = _table_mock(data=[])
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_growth(14)
        assert len(result["series"]) == 14

    def test_counts_members_per_day(self, mocker):
        from services.analytics_service import get_growth
        today = datetime.now(timezone.utc).date().isoformat()
        members = [{"created_at": today + "T12:00:00Z"}, {"created_at": today + "T15:00:00Z"}]
        sb = MagicMock()
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_growth(7)
        today_entry = next(e for e in result["series"] if e["date"] == today)
        assert today_entry["new_members"] == 2

    def test_clamps_days_to_90(self, mocker):
        from services.analytics_service import get_growth
        sb = MagicMock()
        sb.table.return_value = _table_mock(data=[])
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_growth(999)
        assert result["period_days"] == 90
        assert len(result["series"]) == 90

    def test_cumulative_is_monotone(self, mocker):
        from services.analytics_service import get_growth
        today = datetime.now(timezone.utc).date().isoformat()
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        members = [
            {"created_at": yesterday + "T10:00:00Z"},
            {"created_at": today + "T10:00:00Z"},
        ]
        sb = MagicMock()
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_growth(7)
        cumulatives = [e["cumulative"] for e in result["series"]]
        assert cumulatives == sorted(cumulatives)


# ============================================================
#  get_funnel
# ============================================================

class TestGetFunnel:
    def _build_sb(self, mocker, members, clicks):
        sb = MagicMock()

        members_mock = _table_mock(data=members)
        clicks_mock  = _table_mock(data=clicks)

        def table_router(name):
            return members_mock if name == "members" else clicks_mock

        sb.table.side_effect = table_router
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        return sb

    def test_returns_expected_keys(self, mocker):
        from services.analytics_service import get_funnel
        self._build_sb(mocker, [], [])
        result = get_funnel()
        assert "total_registered" in result
        assert "email_provided" in result
        assert "email_confirmed" in result
        assert "members_with_clicks" in result
        assert "rates" in result

    def test_email_provided_count(self, mocker):
        from services.analytics_service import get_funnel
        members = [
            _make_member(email_enc="enc1"),
            _make_member(email_enc=None),
            _make_member(email_enc="enc2"),
        ]
        self._build_sb(mocker, members, [])
        result = get_funnel()
        assert result["email_provided"] == 2
        assert result["total_registered"] == 3

    def test_email_confirmed_count(self, mocker):
        from services.analytics_service import get_funnel
        members = [
            _make_member(email_enc="e1", email_confirmed=True),
            _make_member(email_enc="e2", email_confirmed=False),
        ]
        self._build_sb(mocker, members, [])
        result = get_funnel()
        assert result["email_confirmed"] == 1

    def test_members_with_clicks_unique(self, mocker):
        from services.analytics_service import get_funnel
        clicks = [
            {"member_id": "m1"},
            {"member_id": "m1"},   # mesmo membro, conta 1
            {"member_id": "m2"},
        ]
        self._build_sb(mocker, [], clicks)
        result = get_funnel()
        assert result["members_with_clicks"] == 2

    def test_rates_are_percentages(self, mocker):
        from services.analytics_service import get_funnel
        members = [_make_member(email_enc="e", email_confirmed=True)] * 4
        clicks  = [{"member_id": "m1"}, {"member_id": "m2"}]
        self._build_sb(mocker, members, clicks)
        result = get_funnel()
        assert 0 <= result["rates"]["email_provided_pct"] <= 100
        assert 0 <= result["rates"]["email_confirmed_pct"] <= 100
        assert 0 <= result["rates"]["clicked_pct"] <= 100


# ============================================================
#  get_engagement
# ============================================================

class TestGetEngagement:
    def test_returns_expected_keys(self, mocker):
        from services.analytics_service import get_engagement
        sb = MagicMock()
        clicks_mock = _table_mock(data=[])
        deals_mock  = _table_mock(data=[])

        def router(name):
            return clicks_mock if name == "clicks" else deals_mock

        sb.table.side_effect = router
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_engagement(7)
        assert "total_clicks" in result
        assert "series" in result
        assert "top_categories" in result
        assert len(result["series"]) == 7

    def test_total_clicks_counts_all_rows(self, mocker):
        from services.analytics_service import get_engagement
        today = datetime.now(timezone.utc).date().isoformat()
        clicks = [{"clicked_at": today + "T10:00:00Z", "deal_id": "d1"}] * 3
        sb = MagicMock()
        clicks_mock = _table_mock(data=clicks)
        deals_mock  = _table_mock(data=[{"id": "d1", "category": "electronics"}])

        def router(name):
            return clicks_mock if name == "clicks" else deals_mock

        sb.table.side_effect = router
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_engagement(7)
        assert result["total_clicks"] == 3


# ============================================================
#  get_referral_stats
# ============================================================

class TestGetReferralStats:
    def _build_sb(self, mocker, referrals, member_count=10):
        sb = MagicMock()
        referrals_mock = _table_mock(data=referrals)
        members_mock   = _table_mock(data=[], count=member_count)

        def router(name):
            return referrals_mock if name == "referrals" else members_mock

        sb.table.side_effect = router
        mocker.patch("services.analytics_service._supabase", return_value=sb)

    def test_returns_expected_keys(self, mocker):
        from services.analytics_service import get_referral_stats
        self._build_sb(mocker, [])
        result = get_referral_stats()
        assert "total_referrals" in result
        assert "confirmed_referrals" in result
        assert "unique_referrers" in result
        assert "referrer_adoption_pct" in result
        assert "top_referrers" in result

    def test_unique_referrers_deduped(self, mocker):
        from services.analytics_service import get_referral_stats
        referrals = [
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r2", "status": "pending"},
        ]
        self._build_sb(mocker, referrals, member_count=10)
        result = get_referral_stats()
        assert result["unique_referrers"] == 2
        assert result["total_referrals"] == 3
        assert result["confirmed_referrals"] == 2

    def test_adoption_rate_calculation(self, mocker):
        from services.analytics_service import get_referral_stats
        referrals = [
            {"referrer_id": "r1", "status": "confirmed"},
            {"referrer_id": "r2", "status": "confirmed"},
        ]
        self._build_sb(mocker, referrals, member_count=10)
        result = get_referral_stats()
        assert result["referrer_adoption_pct"] == 20.0  # 2/10


# ============================================================
#  get_geographic_breakdown
# ============================================================

class TestGetGeographicBreakdown:
    def test_returns_top_states(self, mocker):
        from services.analytics_service import get_geographic_breakdown
        sb = MagicMock()
        members = [
            {"state": "FL"}, {"state": "FL"}, {"state": "FL"},
            {"state": "TX"}, {"state": "TX"},
            {"state": "CA"},
        ]
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_geographic_breakdown()
        assert result["total_members"] == 6
        assert result["top_states"][0]["state"] == "FL"
        assert result["top_states"][0]["members"] == 3

    def test_limits_to_10_states(self, mocker):
        from services.analytics_service import get_geographic_breakdown
        sb = MagicMock()
        # 15 estados distintos
        members = [{"state": f"S{i}"} for i in range(15)]
        sb.table.return_value = _table_mock(data=members)
        mocker.patch("services.analytics_service._supabase", return_value=sb)
        result = get_geographic_breakdown()
        assert len(result["top_states"]) <= 10


# ============================================================
#  get_overview
# ============================================================

class TestGetOverview:
    def test_overview_calls_all_sub_functions(self, mocker):
        from services import analytics_service
        mocker.patch.object(analytics_service, "get_growth", return_value={"period_days": 7})
        mocker.patch.object(analytics_service, "get_funnel", return_value={"total_registered": 0})
        mocker.patch.object(analytics_service, "get_engagement", return_value={"total_clicks": 0})
        mocker.patch.object(analytics_service, "get_referral_stats", return_value={"total_referrals": 0})
        mocker.patch.object(analytics_service, "get_geographic_breakdown", return_value={"total_members": 0})

        result = analytics_service.get_overview()
        assert "growth_7d" in result
        assert "funnel" in result
        assert "engagement_7d" in result
        assert "referrals" in result
        assert "geographic" in result
