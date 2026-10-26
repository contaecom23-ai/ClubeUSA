# tests/test_analytics.py — Fase 0.3: Analytics básico
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "api"))

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-chars-long")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32bytes-okay!")


def _make_sb(data_map: dict):
    """Cria mock de cliente Supabase que retorna dados conforme a tabela."""
    sb = MagicMock()

    def make_query(rows):
        q = MagicMock()
        q.select.return_value = q
        q.eq.return_value = q
        q.gte.return_value = q
        q.gt.return_value = q
        q.is_.return_value = q
        q.in_.return_value = q
        q.order.return_value = q
        q.limit.return_value = q
        r = MagicMock()
        r.data = rows
        r.count = len(rows)
        q.execute.return_value = r
        return q

    sb.table.side_effect = lambda name: make_query(data_map.get(name, []))
    return sb


class TestGetFunnel(unittest.TestCase):

    @patch("services.analytics_service._supabase")
    def test_empty_db_returns_zeros(self, mock_fn):
        mock_fn.return_value = _make_sb({})
        from services.analytics_service import get_funnel
        r = get_funnel()
        f = r["funnel"]
        self.assertEqual(f["registrations_total"], 0)
        self.assertEqual(f["vip_subscribers"], 0)
        self.assertEqual(f["referral_conversion_rate"], 0.0)
        self.assertEqual(f["logins_last_7d"], 0)
        self.assertEqual(f["deal_clicks_last_7d"], 0)

    @patch("services.analytics_service._supabase")
    def test_no_zero_division_with_no_members(self, mock_fn):
        mock_fn.return_value = _make_sb({
            "referrals": [{"status": "confirmed"}, {"status": "confirmed"}],
        })
        from services.analytics_service import get_funnel
        r = get_funnel()
        self.assertEqual(r["funnel"]["referral_conversion_rate"], 0.0)

    @patch("services.analytics_service._supabase")
    def test_counts_vip_and_referrals(self, mock_fn):
        now = datetime.now(timezone.utc)
        members = [
            {"id": "1", "plan": "vip",  "created_at": now.isoformat(), "referred_by": None,
             "email_enc": "e", "email_confirmed": True, "total_clicks": 1, "referral_count": 0},
            {"id": "2", "plan": "free", "created_at": now.isoformat(), "referred_by": "1",
             "email_enc": None, "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
            {"id": "3", "plan": "free", "created_at": (now - timedelta(days=40)).isoformat(), "referred_by": None,
             "email_enc": None, "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
        ]
        referrals = [{"status": "confirmed"}, {"status": "pending"}]
        mock_fn.return_value = _make_sb({"members": members, "referrals": referrals})
        from services.analytics_service import get_funnel
        f = get_funnel()["funnel"]
        self.assertEqual(f["registrations_total"], 3)
        self.assertEqual(f["vip_subscribers"], 1)
        self.assertEqual(f["referral_conversions_total"], 1)
        self.assertEqual(f["referral_conversions_pending"], 1)
        self.assertAlmostEqual(f["referral_conversion_rate"], 0.3333, places=3)

    @patch("services.analytics_service._supabase")
    def test_registrations_7d_and_30d(self, mock_fn):
        now = datetime.now(timezone.utc)
        members = [
            {"id": "1", "plan": "free", "created_at": now.isoformat(), "referred_by": None,
             "email_enc": None, "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
            {"id": "2", "plan": "free", "created_at": (now - timedelta(days=10)).isoformat(), "referred_by": None,
             "email_enc": None, "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
            {"id": "3", "plan": "free", "created_at": (now - timedelta(days=40)).isoformat(), "referred_by": None,
             "email_enc": None, "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
        ]
        mock_fn.return_value = _make_sb({"members": members, "referrals": []})
        from services.analytics_service import get_funnel
        f = get_funnel()["funnel"]
        self.assertEqual(f["registrations_total"], 3)
        self.assertEqual(f["registrations_last_7d"], 1)
        self.assertEqual(f["registrations_last_30d"], 2)

    @patch("services.analytics_service._supabase")
    def test_email_funnel_fields(self, mock_fn):
        now = datetime.now(timezone.utc)
        members = [
            {"id": "1", "plan": "free", "created_at": now.isoformat(), "referred_by": None,
             "email_enc": "enc", "email_confirmed": True,  "total_clicks": 1, "referral_count": 0},
            {"id": "2", "plan": "free", "created_at": now.isoformat(), "referred_by": None,
             "email_enc": "enc", "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
            {"id": "3", "plan": "free", "created_at": now.isoformat(), "referred_by": None,
             "email_enc": None,  "email_confirmed": False, "total_clicks": 0, "referral_count": 0},
        ]
        mock_fn.return_value = _make_sb({"members": members, "referrals": []})
        from services.analytics_service import get_funnel
        f = get_funnel()["funnel"]
        self.assertEqual(f["email_set"], 2)
        self.assertEqual(f["email_confirmed"], 1)
        self.assertEqual(f["email_confirmed_pct"], 50.0)
        self.assertEqual(f["made_first_click"], 1)
        self.assertAlmostEqual(f["engagement_pct"], 33.3, places=0)


class TestGetGrowth(unittest.TestCase):

    @patch("services.analytics_service._supabase")
    def test_returns_exactly_n_days(self, mock_fn):
        mock_fn.return_value = _make_sb({"members": []})
        from services.analytics_service import get_growth
        result = get_growth(days=30)
        self.assertEqual(len(result), 30)

    @patch("services.analytics_service._supabase")
    def test_each_entry_has_date_and_registrations(self, mock_fn):
        mock_fn.return_value = _make_sb({"members": []})
        from services.analytics_service import get_growth
        result = get_growth(days=7)
        for entry in result:
            self.assertIn("date", entry)
            self.assertIn("registrations", entry)
            self.assertIsInstance(entry["registrations"], int)

    @patch("services.analytics_service._supabase")
    def test_counts_today_registrations(self, mock_fn):
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        members = [{"created_at": now.isoformat()}, {"created_at": now.isoformat()}]
        mock_fn.return_value = _make_sb({"members": members})
        from services.analytics_service import get_growth
        result = get_growth(days=7)
        today_entry = next((d for d in result if d["date"] == today), None)
        self.assertIsNotNone(today_entry)
        self.assertEqual(today_entry["registrations"], 2)

    @patch("services.analytics_service._supabase")
    def test_days_in_chronological_order(self, mock_fn):
        mock_fn.return_value = _make_sb({"members": []})
        from services.analytics_service import get_growth
        result = get_growth(days=10)
        dates = [entry["date"] for entry in result]
        self.assertEqual(dates, sorted(dates))


class TestGetTopReferrers(unittest.TestCase):

    @patch("services.analytics_service._supabase")
    def test_empty_returns_empty_list(self, mock_fn):
        mock_fn.return_value = _make_sb({"members": []})
        from services.analytics_service import get_top_referrers
        result = get_top_referrers()
        self.assertEqual(result, [])

    @patch("services.analytics_service._supabase")
    def test_returns_referral_code_and_count(self, mock_fn):
        mock_fn.return_value = _make_sb({
            "members": [{"name_enc": None, "referral_code": "ABC123", "referral_count": 5}]
        })
        from services.analytics_service import get_top_referrers
        result = get_top_referrers(limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["referral_code"], "ABC123")
        self.assertEqual(result[0]["referral_count"], 5)


class TestGetEngagement(unittest.TestCase):

    @patch("services.analytics_service._supabase")
    def test_no_clicks_returns_zeros(self, mock_fn):
        mock_fn.return_value = _make_sb({"clicks": []})
        from services.analytics_service import get_engagement
        result = get_engagement()
        self.assertEqual(result["clicks_last_7d"], 0)
        self.assertEqual(result["top_categories"], [])

    @patch("services.analytics_service._supabase")
    def test_counts_clicks_and_top_categories(self, mock_fn):
        clicks = [{"deal_id": "deal-1"}, {"deal_id": "deal-1"}, {"deal_id": "deal-2"}]
        deals  = [{"id": "deal-1", "category": "electronics"}, {"id": "deal-2", "category": "kitchen"}]
        mock_fn.return_value = _make_sb({"clicks": clicks, "deals": deals})
        from services.analytics_service import get_engagement
        result = get_engagement()
        self.assertEqual(result["clicks_last_7d"], 3)
        self.assertEqual(len(result["top_categories"]), 2)
        self.assertEqual(result["top_categories"][0]["category"], "electronics")
        self.assertEqual(result["top_categories"][0]["clicks"], 2)


class TestLogEvent(unittest.TestCase):

    @patch("services.analytics_service._supabase")
    def test_silent_on_db_error(self, mock_fn):
        """log_event não propaga exceção se DB falha."""
        mock_fn.return_value.table.return_value.insert.return_value.execute.side_effect = Exception("DB down")
        from services.analytics_service import log_event
        log_event("uuid-123", "member.registered", {"test": True})

    @patch("services.analytics_service._supabase")
    def test_inserts_correct_data(self, mock_fn):
        mock_sb = MagicMock()
        mock_fn.return_value = mock_sb
        from services.analytics_service import log_event
        log_event("uuid-abc", "email.confirmed", {"source": "link"})
        insert_call = mock_sb.table.return_value.insert.call_args[0][0]
        self.assertEqual(insert_call["member_id"], "uuid-abc")
        self.assertEqual(insert_call["event_type"], "email.confirmed")
        self.assertEqual(insert_call["metadata"]["source"], "link")

    @patch("services.analytics_service._supabase")
    def test_defaults_empty_metadata(self, mock_fn):
        mock_sb = MagicMock()
        mock_fn.return_value = mock_sb
        from services.analytics_service import log_event
        log_event("uuid-xyz", "deal.clicked")
        insert_call = mock_sb.table.return_value.insert.call_args[0][0]
        self.assertEqual(insert_call["metadata"], {})


if __name__ == "__main__":
    unittest.main()
