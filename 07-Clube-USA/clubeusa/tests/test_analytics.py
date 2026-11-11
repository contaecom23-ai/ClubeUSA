"""Tests for Fase 0.3 — Analytics endpoint and service."""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_SECRET = "test-admin-secret-fixed"


def _make_app():
    import os
    os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-key")
    os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-chars-pad")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
    os.environ.setdefault("STRIPE_SECRET_KEY", "")
    os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "")
    os.environ.setdefault("STRIPE_VIP_PRICE_ID", "")
    os.environ["ADMIN_SECRET"] = _ADMIN_SECRET
    from api.main import app
    return app


def _admin_header() -> dict:
    return {"Authorization": f"Bearer {_ADMIN_SECRET}"}


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------

FAKE_DAILY = [{"reg_date": "2026-11-01", "cnt": 5}, {"reg_date": "2026-11-02", "cnt": 3}]
FAKE_FUNNEL = [
    {"stage": "registered",     "cnt": 100},
    {"stage": "email_verified", "cnt": 80},
    {"stage": "had_click",      "cnt": 60},
    {"stage": "referred",       "cnt": 20},
    {"stage": "vip",            "cnt": 10},
]
FAKE_TOP_REFS = [{"referral_code": "ABC123", "referral_count": 7}]


def _mock_sb(daily=FAKE_DAILY, funnel=FAKE_FUNNEL, top_refs=FAKE_TOP_REFS, ref_clicks=42):
    sb = MagicMock()

    daily_result = MagicMock()
    daily_result.data = daily
    sb.rpc.return_value.execute.return_value = daily_result

    # second rpc call (funnel) needs different data — use side_effect
    funnel_result = MagicMock()
    funnel_result.data = funnel

    sb.rpc.side_effect = [
        MagicMock(**{"execute.return_value": daily_result}),
        MagicMock(**{"execute.return_value": funnel_result}),
    ]

    # top referrers query chain
    top_chain = MagicMock()
    top_chain.execute.return_value.data = top_refs
    sb.table.return_value.select.return_value.gt.return_value.order.return_value.limit.return_value = top_chain

    # referral link clicks (count query)
    clicks_result = MagicMock()
    clicks_result.count = ref_clicks
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = clicks_result

    return sb


def test_get_analytics_summary_values():
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        from services.admin_service import get_analytics
        result = get_analytics(days_back=30)

    s = result["summary"]
    assert s["total_members"] == 100
    assert s["new_in_period"] == 8   # 5 + 3
    assert s["email_verified"] == 80
    assert s["email_verified_rate"] == 0.8
    assert s["vip"] == 10
    assert s["vip_rate"] == 0.1
    assert s["referred_members"] == 20


def test_get_analytics_daily_signups_passthrough():
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        from services.admin_service import get_analytics
        result = get_analytics(days_back=30)

    assert result["daily_signups"] == [
        {"date": "2026-11-01", "count": 5},
        {"date": "2026-11-02", "count": 3},
    ]


def test_get_analytics_days_clamped_low():
    """days_back < 7 should be clamped to 7."""
    with patch("services.admin_service._supabase", return_value=_mock_sb()) as mock_sb_func:
        from services.admin_service import get_analytics
        result = get_analytics(days_back=1)
    assert result["period_days"] == 7


def test_get_analytics_days_clamped_high():
    """days_back > 90 should be clamped to 90."""
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        from services.admin_service import get_analytics
        result = get_analytics(days_back=999)
    assert result["period_days"] == 90


def test_get_analytics_zero_registered_no_division():
    """Should not raise when registered == 0 (avoid ZeroDivisionError)."""
    funnel_zero = [{"stage": "registered", "cnt": 0}, {"stage": "email_verified", "cnt": 0},
                   {"stage": "had_click", "cnt": 0}, {"stage": "referred", "cnt": 0}, {"stage": "vip", "cnt": 0}]
    with patch("services.admin_service._supabase", return_value=_mock_sb(funnel=funnel_zero)):
        from services.admin_service import get_analytics
        result = get_analytics(days_back=30)
    assert result["summary"]["email_verified_rate"] == 0
    assert result["summary"]["vip_rate"] == 0


def test_get_analytics_top_referrers():
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        from services.admin_service import get_analytics
        result = get_analytics(days_back=30)
    assert result["top_referrers"] == FAKE_TOP_REFS


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

def _build_client():
    app = _make_app()
    return TestClient(app, raise_server_exceptions=True)


def test_admin_analytics_requires_auth():
    client = _build_client()
    resp = client.get("/admin/analytics")
    assert resp.status_code in (401, 403)


def test_admin_analytics_returns_200():
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        client = _build_client()
        resp = client.get("/admin/analytics", headers=_admin_header())
    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "daily_signups" in body
    assert "funnel" in body
    assert "top_referrers" in body


def test_admin_analytics_days_param_forwarded():
    with patch("services.admin_service._supabase", return_value=_mock_sb()):
        client = _build_client()
        resp = client.get("/admin/analytics?days=14", headers=_admin_header())
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 14
