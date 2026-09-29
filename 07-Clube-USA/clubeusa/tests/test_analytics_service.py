# tests/test_analytics_service.py — Fase 0.3: analytics básico
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


# ============================================================
#  get_metrics — extensão com email_confirmation
# ============================================================

def test_metrics_includes_email_confirmation(mocker):
    from services.admin_service import get_metrics

    mock_sb = MagicMock()
    mock_sb.table().select().execute.return_value.data = [
        {"plan": "free", "status": "active", "created_at": "2026-09-01T10:00:00Z",
         "email_enc": "enc1", "email_confirmed_at": "2026-09-02T10:00:00Z"},
        {"plan": "free", "status": "active", "created_at": "2026-09-01T11:00:00Z",
         "email_enc": "enc2", "email_confirmed_at": None},
        {"plan": "vip",  "status": "active", "created_at": "2026-09-01T12:00:00Z",
         "email_enc": None,   "email_confirmed_at": None},
    ]
    mock_sb.table().select().gte().execute.return_value.data = []
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_metrics()
    m = result["members"]
    assert m["total"] == 3
    assert m["email_confirmed"] == 1
    assert m["confirmation_rate"] == 50.0   # 1 confirmed out of 2 with email


def test_metrics_confirmation_rate_zero_when_no_email(mocker):
    from services.admin_service import get_metrics

    mock_sb = MagicMock()
    mock_sb.table().select().execute.return_value.data = [
        {"plan": "free", "status": "active", "created_at": "2026-09-01T10:00:00Z",
         "email_enc": None, "email_confirmed_at": None},
    ]
    mock_sb.table().select().gte().execute.return_value.data = []
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_metrics()
    assert result["members"]["confirmation_rate"] == 0.0


# ============================================================
#  get_growth
# ============================================================

def test_get_growth_returns_correct_length(mocker):
    from services.admin_service import get_growth

    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth(days=7)
    assert len(result) == 7
    for row in result:
        assert "date" in row
        assert "count" in row


def test_get_growth_counts_correctly(mocker):
    from services.admin_service import get_growth

    today = datetime.now(timezone.utc).date().isoformat()
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = [
        {"created_at": f"{today}T10:00:00Z"},
        {"created_at": f"{today}T11:00:00Z"},
        {"created_at": f"{yesterday}T09:00:00Z"},
    ]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth(days=7)
    by_date = {r["date"]: r["count"] for r in result}
    assert by_date[today] == 2
    assert by_date[yesterday] == 1


def test_get_growth_fills_empty_days_with_zero(mocker):
    from services.admin_service import get_growth

    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth(days=5)
    assert all(r["count"] == 0 for r in result)


# ============================================================
#  get_funnel
# ============================================================

def test_get_funnel_returns_expected_keys(mocker):
    from services.admin_service import get_funnel

    mock_sb = MagicMock()
    mock_sb.table().select().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_funnel()
    for key in ("registered", "email_provided", "email_confirmed",
                "engaged", "via_referral", "confirmation_rate",
                "engagement_rate", "referral_rate"):
        assert key in result


def test_get_funnel_calculates_rates(mocker):
    from services.admin_service import get_funnel

    mock_sb = MagicMock()
    mock_sb.table().select().execute.return_value.data = [
        {"email_enc": "e1", "email_confirmed_at": "2026-09-01T00:00:00Z",
         "total_clicks": 3,  "referred_by": "ref-1"},
        {"email_enc": "e2", "email_confirmed_at": None,
         "total_clicks": 0,  "referred_by": None},
        {"email_enc": None,  "email_confirmed_at": None,
         "total_clicks": 0,  "referred_by": "ref-2"},
        {"email_enc": "e3", "email_confirmed_at": "2026-09-02T00:00:00Z",
         "total_clicks": 1,  "referred_by": None},
    ]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    r = get_funnel()
    assert r["registered"]      == 4
    assert r["email_provided"]  == 3
    assert r["email_confirmed"] == 2
    assert r["engaged"]         == 2
    assert r["via_referral"]    == 2
    assert r["confirmation_rate"] == round(2 / 3 * 100, 1)
    assert r["engagement_rate"]   == 50.0
    assert r["referral_rate"]     == 50.0


def test_get_funnel_zero_rates_when_empty(mocker):
    from services.admin_service import get_funnel

    mock_sb = MagicMock()
    mock_sb.table().select().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    r = get_funnel()
    assert r["registered"] == 0
    assert r["confirmation_rate"] == 0.0
    assert r["engagement_rate"]   == 0.0
    assert r["referral_rate"]     == 0.0
