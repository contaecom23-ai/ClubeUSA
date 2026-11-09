# ============================================================
#  tests/test_analytics.py — Clube USA
#  Testa analytics_service (sem Supabase real)
# ============================================================

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def _make_sb(members=None, clicks=None, deals=None, referrals=None):
    """Fábrica de mock Supabase com dados configuráveis."""

    members   = members   if members   is not None else []
    clicks    = clicks    if clicks    is not None else []
    deals     = deals     if deals     is not None else []
    referrals = referrals if referrals is not None else []

    sb = MagicMock()

    def _table(name):
        t = MagicMock()

        # select().execute()
        rows_map = {
            "members":   members,
            "clicks":    clicks,
            "deals":     deals,
            "referrals": referrals,
        }

        def _build_query(rows_ref):
            q = MagicMock()
            q.execute.return_value = MagicMock(data=list(rows_ref))
            q.select.return_value  = q
            q.gte.return_value     = q
            q.in_.return_value     = q
            q.eq.return_value      = q
            q.order.return_value   = q
            return q

        t.select.side_effect = lambda *a, **kw: _build_query(rows_map.get(name, []))
        return t

    sb.table.side_effect = _table
    return sb


# ─────────────────────────────────────────────
#  get_overview
# ─────────────────────────────────────────────

class TestGetOverview:
    def _patch(self, members, clicks, deals, referrals):
        sb = _make_sb(members=members, clicks=clicks, deals=deals, referrals=referrals)
        return patch("services.analytics_service._sb", return_value=sb)

    def test_empty_db_returns_zeros(self):
        with self._patch([], [], [], []):
            from services.analytics_service import get_overview
            result = get_overview()

        assert result["members"]["total"] == 0
        assert result["funnel"]["registered"] == 0
        assert result["funnel"]["email_rate_pct"] == 0
        assert result["referrals"]["conversion_rate_pct"] == 0

    def test_basic_counts(self):
        members = [
            {"plan": "free", "status": "active", "created_at": _now_iso(), "email_confirmed": True,  "total_clicks": 5},
            {"plan": "vip",  "status": "active", "created_at": _now_iso(), "email_confirmed": False, "total_clicks": 0},
            {"plan": "free", "status": "active", "created_at": _days_ago(10), "email_confirmed": False, "total_clicks": 0},
        ]
        with self._patch(members, [], [], []):
            from services.analytics_service import get_overview
            result = get_overview()

        assert result["members"]["total"] == 3
        assert result["members"]["vip"] == 1
        assert result["funnel"]["email_confirmed"] == 1
        assert result["funnel"]["has_activity"] == 1
        assert result["funnel"]["email_rate_pct"] == pytest.approx(33.3, 0.1)

    def test_referral_conversion_rate(self):
        referrals = [
            {"status": "confirmed"},
            {"status": "confirmed"},
            {"status": "pending"},
        ]
        with self._patch([], [], [], referrals):
            from services.analytics_service import get_overview
            result = get_overview()

        assert result["referrals"]["total"] == 3
        assert result["referrals"]["confirmed"] == 2
        assert result["referrals"]["conversion_rate_pct"] == pytest.approx(66.7, 0.1)


# ─────────────────────────────────────────────
#  Série temporal
# ─────────────────────────────────────────────

class TestTimeSeries:
    def test_registrations_fills_missing_days(self):
        """Dias sem cadastros devem aparecer com count=0."""
        members = [
            {"created_at": _now_iso()},
            {"created_at": _now_iso()},
        ]
        sb = _make_sb(members=members)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_registrations_by_day
            series = get_registrations_by_day(7)

        assert len(series) == 7
        assert all("date" in s and "count" in s for s in series)
        # Hoje deve ter 2
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_entry = next(s for s in series if s["date"] == today)
        assert today_entry["count"] == 2
        # Dias anteriores sem dados devem ser 0
        assert sum(s["count"] for s in series if s["date"] != today) == 0

    def test_clicks_by_day_structure(self):
        clicks = [
            {"clicked_at": _days_ago(1)},
            {"clicked_at": _days_ago(1)},
            {"clicked_at": _days_ago(3)},
        ]
        sb = _make_sb(clicks=clicks)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_clicks_by_day
            series = get_clicks_by_day(7)

        assert len(series) == 7
        total = sum(s["count"] for s in series)
        assert total == 3

    def test_days_capped_at_90(self):
        sb = _make_sb()
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_registrations_by_day
            series = get_registrations_by_day(999)
        assert len(series) == 90

    def test_days_minimum_is_1(self):
        sb = _make_sb()
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_registrations_by_day
            series = get_registrations_by_day(0)
        assert len(series) == 1


# ─────────────────────────────────────────────
#  Funil
# ─────────────────────────────────────────────

class TestFunnel:
    def test_funnel_steps_always_present(self):
        sb = _make_sb()
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_funnel
            result = get_funnel()

        assert "steps" in result
        step_names = [s["step"] for s in result["steps"]]
        assert "Cadastrados" in step_names
        assert "Email confirmado" in step_names
        assert "Primeira ação (clique)" in step_names
        assert "VIP" in step_names

    def test_funnel_rates_descend(self):
        members = [
            {"plan": "free", "email_confirmed": True,  "total_clicks": 1, "created_at": _now_iso()},
            {"plan": "free", "email_confirmed": False, "total_clicks": 0, "created_at": _now_iso()},
            {"plan": "free", "email_confirmed": False, "total_clicks": 0, "created_at": _now_iso()},
            {"plan": "free", "email_confirmed": False, "total_clicks": 0, "created_at": _now_iso()},
        ]
        sb = _make_sb(members=members)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_funnel
            result = get_funnel()

        rates = [s["rate"] for s in result["steps"]]
        assert rates[0] == 100.0
        assert rates[1] <= rates[0]
        assert rates[2] <= rates[1]
        assert rates[3] <= rates[2]


# ─────────────────────────────────────────────
#  Top deals
# ─────────────────────────────────────────────

class TestTopDeals:
    def test_no_clicks_returns_empty(self):
        sb = _make_sb(clicks=[])
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_top_deals
            result = get_top_deals(10)
        assert result == []

    def test_ordered_by_clicks_desc(self):
        clicks = (
            [{"deal_id": "aaa"}] * 5 +
            [{"deal_id": "bbb"}] * 2
        )
        deals = [
            {"id": "aaa", "title": "Deal A", "category": "electronics", "price_now": 99.0,
             "discount_pct": 20, "score": 8.0, "status": "sent", "sent_at": _now_iso()},
            {"id": "bbb", "title": "Deal B", "category": "kitchen", "price_now": 29.0,
             "discount_pct": 10, "score": 5.0, "status": "sent", "sent_at": _now_iso()},
        ]

        sb = MagicMock()

        def _table(name):
            t = MagicMock()
            q = MagicMock()

            if name == "clicks":
                q.execute.return_value = MagicMock(data=list(clicks))
            elif name == "deals":
                q.execute.return_value = MagicMock(data=list(deals))
            else:
                q.execute.return_value = MagicMock(data=[])

            q.select.return_value = q
            q.in_.return_value    = q
            q.gte.return_value    = q
            t.select.side_effect  = lambda *a, **kw: q
            return t

        sb.table.side_effect = _table

        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_top_deals
            result = get_top_deals(10)

        assert len(result) == 2
        assert result[0]["deal_id"] == "aaa"
        assert result[0]["clicks"] == 5
        assert result[1]["deal_id"] == "bbb"
        assert result[1]["clicks"] == 2

    def test_limit_respected(self):
        clicks = [{"deal_id": str(i)} for i in range(20)]
        deals  = [
            {"id": str(i), "title": f"Deal {i}", "category": "all", "price_now": 1.0,
             "discount_pct": 5, "score": 1.0, "status": "sent", "sent_at": _now_iso()}
            for i in range(20)
        ]

        sb = MagicMock()

        def _table(name):
            t = MagicMock()
            q = MagicMock()
            q.execute.return_value = MagicMock(
                data=list(clicks) if name == "clicks" else list(deals)
            )
            q.select.return_value = q
            q.in_.return_value    = q
            q.gte.return_value    = q
            t.select.side_effect  = lambda *a, **kw: q
            return t

        sb.table.side_effect = _table

        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_top_deals
            result = get_top_deals(5)

        assert len(result) <= 5


# ─────────────────────────────────────────────
#  Distribuição
# ─────────────────────────────────────────────

class TestDistribution:
    def test_state_distribution_groups_small_states(self):
        """Estados com < 3 membros devem ir para 'outros'."""
        members = (
            [{"state": "FL"}] * 10 +
            [{"state": "TX"}] * 5 +
            [{"state": "CA"}] * 2 +   # < 3, vai para 'outros'
            [{"state": "NY"}] * 1     # < 3, vai para 'outros'
        )
        sb = _make_sb(members=members)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_members_by_state
            result = get_members_by_state()

        states = {r["state"]: r["count"] for r in result}
        assert states["FL"] == 10
        assert states["TX"] == 5
        assert states["outros"] == 3   # CA=2 + NY=1

    def test_category_distribution_counts_per_member(self):
        members = [
            {"categories": ["electronics", "kitchen"]},
            {"categories": ["electronics"]},
            {"categories": ["all"]},
        ]
        sb = _make_sb(members=members)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_members_by_category
            result = get_members_by_category()

        cats = {r["category"]: r["count"] for r in result}
        assert cats["electronics"] == 2
        assert cats["kitchen"] == 1
        assert cats["all"] == 1

    def test_empty_state_becomes_nao_informado(self):
        members = [{"state": ""}, {"state": None}, {"state": "FL"}]
        sb = _make_sb(members=members)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_members_by_state
            result = get_members_by_state()

        states = {r["state"]: r["count"] for r in result}
        assert "não informado" in states or "outros" in states


# ─────────────────────────────────────────────
#  Referral stats
# ─────────────────────────────────────────────

class TestReferralStats:
    def test_empty_returns_zeros(self):
        sb = _make_sb(referrals=[])
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_referral_stats
            result = get_referral_stats()

        assert result["total"] == 0
        assert result["confirmed"] == 0
        assert result["conversion_rate_pct"] == 0
        assert result["unique_referrers"] == 0

    def test_referrers_with_3plus_milestone(self):
        referrals = (
            [{"referrer_id": "alice", "status": "confirmed"}] * 3 +
            [{"referrer_id": "bob",   "status": "confirmed"}] * 1
        )
        sb = _make_sb(referrals=referrals)
        with patch("services.analytics_service._sb", return_value=sb):
            from services.analytics_service import get_referral_stats
            result = get_referral_stats()

        assert result["unique_referrers"] == 2
        assert result["referrers_with_3plus"] == 1  # só alice
