# tests/test_analytics.py — Fase 0.3
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")


def _mock_sb(table_responses: dict):
    """Cria mock do Supabase client com respostas configuradas por tabela/acao."""
    sb = MagicMock()

    def make_table_mock(table_name):
        resp_cfg = table_responses.get(table_name, {})
        tbl = MagicMock()

        def select_mock(*args, **kwargs):
            chain = MagicMock()
            data = resp_cfg.get("data", [])
            count = resp_cfg.get("count", len(data))
            result = MagicMock(data=data, count=count)
            chain.execute.return_value = result
            chain.eq.return_value = chain
            chain.gt.return_value = chain
            chain.gte.return_value = chain
            chain.order.return_value = chain
            chain.limit.return_value = chain
            chain.in_.return_value = chain
            return chain

        tbl.select = select_mock
        return tbl

    sb.table.side_effect = make_table_mock
    return sb


class TestGetFunnel:
    def test_returns_correct_counts(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            def table_select(table_name):
                tbl = MagicMock()
                def sel(*a, **kw):
                    chain = MagicMock()
                    counts = {
                        "members": 100,
                        "clicks": 500,
                    }
                    result = MagicMock(data=[], count=counts.get(table_name, 0))
                    chain.execute.return_value = result
                    chain.eq.return_value = chain
                    chain.gt.return_value = chain
                    chain.gte.return_value = chain
                    chain.order.return_value = chain
                    chain.limit.return_value = chain
                    return chain
                tbl.select = sel
                return tbl

            sb.table.side_effect = table_select

            from analytics_service import get_funnel
            result = get_funnel()

            assert "total_members" in result
            assert "vip_members" in result
            assert "total_clicks" in result
            assert "vip_conversion" in result
            assert "engagement_rate" in result

    def test_zero_members_no_division_error(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            def table_select(table_name):
                tbl = MagicMock()
                def sel(*a, **kw):
                    chain = MagicMock()
                    result = MagicMock(data=[], count=0)
                    chain.execute.return_value = result
                    chain.eq.return_value = chain
                    chain.gt.return_value = chain
                    chain.gte.return_value = chain
                    chain.order.return_value = chain
                    chain.limit.return_value = chain
                    return chain
                tbl.select = sel
                return tbl

            sb.table.side_effect = table_select

            from analytics_service import get_funnel
            result = get_funnel()
            assert result["vip_conversion"] == 0
            assert result["engagement_rate"] == 0


class TestGetGrowth:
    def test_returns_list_with_correct_length(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            tbl = MagicMock()
            chain = MagicMock()
            chain.execute.return_value = MagicMock(data=[
                {"created_at": "2026-08-01T12:00:00+00:00"},
                {"created_at": "2026-08-01T15:00:00+00:00"},
                {"created_at": "2026-08-05T10:00:00+00:00"},
            ], count=3)
            chain.gte.return_value = chain
            chain.order.return_value = chain
            tbl.select.return_value = chain
            sb.table.return_value = tbl

            from analytics_service import get_growth
            result = get_growth(days=30)

            assert len(result) == 30
            for entry in result:
                assert "date" in entry
                assert "new_members" in entry

    def test_aggregates_multiple_signups_same_day(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            tbl = MagicMock()
            chain = MagicMock()
            chain.execute.return_value = MagicMock(data=[
                {"created_at": "2026-08-20T01:00:00+00:00"},
                {"created_at": "2026-08-20T02:00:00+00:00"},
                {"created_at": "2026-08-20T03:00:00+00:00"},
            ], count=3)
            chain.gte.return_value = chain
            chain.order.return_value = chain
            tbl.select.return_value = chain
            sb.table.return_value = tbl

            from analytics_service import get_growth
            result = get_growth(days=7)

            day_2026_08_20 = next((r for r in result if r["date"] == "2026-08-20"), None)
            if day_2026_08_20:
                assert day_2026_08_20["new_members"] == 3


class TestGetTopReferrers:
    def test_returns_referrers_sorted(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            tbl = MagicMock()
            chain = MagicMock()
            chain.execute.return_value = MagicMock(data=[
                {"id": "aaa", "referral_count": 10, "points": 2000, "level": "gold"},
                {"id": "bbb", "referral_count": 5,  "points": 1000, "level": "silver"},
            ], count=2)
            chain.gt.return_value = chain
            chain.order.return_value = chain
            chain.limit.return_value = chain
            tbl.select.return_value = chain
            sb.table.return_value = tbl

            from analytics_service import get_top_referrers
            result = get_top_referrers(limit=10)

            assert len(result) == 2
            assert result[0]["referral_count"] == 10
            assert result[0]["member_id"] == "aaa"

    def test_empty_referrers(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            tbl = MagicMock()
            chain = MagicMock()
            chain.execute.return_value = MagicMock(data=[], count=0)
            chain.gt.return_value = chain
            chain.order.return_value = chain
            chain.limit.return_value = chain
            tbl.select.return_value = chain
            sb.table.return_value = tbl

            from analytics_service import get_top_referrers
            result = get_top_referrers()
            assert result == []


class TestGetEngagement:
    def test_returns_engagement_counts(self):
        with patch("analytics_service._sb") as mock_sb_fn:
            sb = MagicMock()
            mock_sb_fn.return_value = sb

            call_count = [0]

            def table_side(table_name):
                tbl = MagicMock()
                def sel(*a, **kw):
                    chain = MagicMock()
                    counts = {"audit_logs": 42, "clicks": 100, "referrals": 5}
                    result = MagicMock(data=[], count=counts.get(table_name, 0))
                    chain.execute.return_value = result
                    chain.eq.return_value = chain
                    chain.gte.return_value = chain
                    chain.order.return_value = chain
                    chain.limit.return_value = chain
                    return chain
                tbl.select = sel
                return tbl

            sb.table.side_effect = table_side

            from analytics_service import get_engagement
            result = get_engagement(days=7)

            assert result["period_days"] == 7
            assert "logins" in result
            assert "deal_clicks" in result
            assert "new_referrals" in result
