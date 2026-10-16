# ============================================================
#  tests/test_analytics.py — Clube USA
#  Testes do analytics_service.py (Fase 0.3)
# ============================================================
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


def _make_member(plan="free", email_enc=None, email_confirmed=False, total_clicks=0,
                 referral_count=0, referred_by=None, days_ago=5):
    created = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {
        "id": "uuid-test",
        "plan": plan,
        "status": "active",
        "email_enc": email_enc,
        "email_confirmed": email_confirmed,
        "total_clicks": total_clicks,
        "referral_count": referral_count,
        "referred_by": referred_by,
        "created_at": created,
    }


class TestAnalyticsService:
    def _patch_supabase(self, members):
        mock_sb = MagicMock()
        mock_result = MagicMock()
        mock_result.data = members
        mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value = mock_result
        return mock_sb

    def test_empty_analytics_when_no_members(self):
        import services.analytics_service as svc
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value.data = []
            mock_client.return_value = mock_sb
            result = svc.get_analytics()
        assert result["funnel"]["registered"] == 0
        assert result["growth_30d"] == []
        assert result["funnel_rates"]["engagement_pct"] == 0.0

    def test_funnel_counts_correctly(self):
        import services.analytics_service as svc
        members = [
            _make_member(email_enc="enc1", email_confirmed=True, total_clicks=3),
            _make_member(email_enc="enc2", email_confirmed=False, total_clicks=0),
            _make_member(email_enc=None,   email_confirmed=False, total_clicks=1),
        ]
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value.data = members
            mock_client.return_value = mock_sb
            result = svc.get_analytics()
        assert result["funnel"]["registered"] == 3
        assert result["funnel"]["email_set"] == 2
        assert result["funnel"]["email_confirmed"] == 1
        assert result["funnel"]["made_first_click"] == 2

    def test_funnel_rates_calculated(self):
        import services.analytics_service as svc
        members = [
            _make_member(email_enc="e1", email_confirmed=True,  total_clicks=1),
            _make_member(email_enc="e2", email_confirmed=False, total_clicks=0),
        ]
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value.data = members
            mock_client.return_value = mock_sb
            result = svc.get_analytics()
        assert result["funnel_rates"]["email_set_pct"] == 100.0
        assert result["funnel_rates"]["email_confirm_pct"] == 50.0
        assert result["funnel_rates"]["engagement_pct"] == 50.0

    def test_growth_30d_groups_by_day(self):
        import services.analytics_service as svc
        # 2 members created today, 1 created 25 days ago, 1 created 35 days ago (outside window)
        members = [
            _make_member(days_ago=0),
            _make_member(days_ago=0),
            _make_member(days_ago=25),
            _make_member(days_ago=35),
        ]
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value.data = members
            mock_client.return_value = mock_sb
            result = svc.get_analytics()
        # only 30d window: 3 members, grouped into 2 date buckets
        total_in_growth = sum(d["count"] for d in result["growth_30d"])
        assert total_in_growth == 3
        assert len(result["growth_30d"]) == 2  # 2 distinct days

    def test_referral_stats(self):
        import services.analytics_service as svc
        members = [
            _make_member(referral_count=3, referred_by=None),
            _make_member(referral_count=1, referred_by="other-uuid"),
            _make_member(referral_count=0, referred_by="other-uuid"),
        ]
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.is_.return_value.execute.return_value.data = members
            mock_client.return_value = mock_sb
            result = svc.get_analytics()
        r = result["referrals"]
        assert r["members_who_referred"] == 2
        assert r["total_referrals_made"] == 4
        assert r["avg_per_referrer"] == 2.0
        assert r["members_via_referral"] == 2

    def test_log_event_silent_on_db_error(self):
        """log_event não propaga exceção se DB falha."""
        import services.analytics_service as svc
        with patch.object(svc, "_supabase") as mock_client:
            mock_client.return_value.table.return_value.insert.return_value.execute.side_effect = Exception("DB down")
            svc.log_event("uuid-123", "member.registered", {"test": True})
        # Sem exception = passou

    def test_log_event_inserts_correct_data(self):
        import services.analytics_service as svc
        with patch.object(svc, "_supabase") as mock_client:
            mock_sb = MagicMock()
            mock_client.return_value = mock_sb
            svc.log_event("uuid-abc", "email.confirmed", {"source": "link"})
        insert_call = mock_sb.table.return_value.insert.call_args[0][0]
        assert insert_call["member_id"] == "uuid-abc"
        assert insert_call["event_type"] == "email.confirmed"
        assert insert_call["metadata"]["source"] == "link"
