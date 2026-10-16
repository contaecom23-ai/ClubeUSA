import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone


def _mock_sb():
    return MagicMock()


def test_get_analytics_structure(mocker):
    from services.admin_service import get_analytics

    mock_sb = _mock_sb()
    now = datetime.now(timezone.utc)

    mock_sb.table().select().is_().execute.return_value.data = [
        {"plan": "free", "status": "active",   "language": "pt", "referral_count": 0, "total_clicks": 2, "created_at": now.isoformat(), "referred_by": None},
        {"plan": "vip",  "status": "active",   "language": "pt", "referral_count": 3, "total_clicks": 0, "created_at": now.isoformat(), "referred_by": "uuid-abc"},
        {"plan": "free", "status": "inactive", "language": "es", "referral_count": 0, "total_clicks": 0, "created_at": now.isoformat(), "referred_by": None},
    ]
    mock_sb.table().select().execute.return_value.data = []
    mock_sb.table().select().gte().execute.return_value.data = []

    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_analytics()

    assert "generated_at" in result
    assert "members" in result
    assert "valid_signups" in result
    assert "referrals" in result
    assert "engagement" in result

    members = result["members"]
    assert "total" in members
    assert "active" in members
    assert "vip" in members
    assert "new_today" in members
    assert "new_this_week" in members
    assert "new_this_month" in members
    assert "by_language" in members
    assert "via_referral" in members

    vs = result["valid_signups"]
    assert "count" in vs
    assert "percent" in vs
    assert "definition" in vs


def test_get_analytics_valid_signups_logic(mocker):
    from services.admin_service import get_analytics

    mock_sb = _mock_sb()
    now = datetime.now(timezone.utc)

    mock_sb.table().select().is_().execute.return_value.data = [
        # valid: active + has clicks
        {"plan": "free", "status": "active", "language": "pt", "referral_count": 0, "total_clicks": 5, "created_at": now.isoformat(), "referred_by": None},
        # valid: active + has referrals
        {"plan": "free", "status": "active", "language": "pt", "referral_count": 2, "total_clicks": 0, "created_at": now.isoformat(), "referred_by": None},
        # NOT valid: active but no actions
        {"plan": "free", "status": "active", "language": "pt", "referral_count": 0, "total_clicks": 0, "created_at": now.isoformat(), "referred_by": None},
        # NOT valid: inactive
        {"plan": "free", "status": "inactive", "language": "pt", "referral_count": 1, "total_clicks": 1, "created_at": now.isoformat(), "referred_by": None},
    ]
    mock_sb.table().select().execute.return_value.data = []
    mock_sb.table().select().gte().execute.return_value.data = []

    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_analytics()
    assert result["valid_signups"]["count"] == 2
    assert result["members"]["total"] == 4


def test_get_analytics_via_referral_count(mocker):
    from services.admin_service import get_analytics

    mock_sb = _mock_sb()
    now = datetime.now(timezone.utc)

    mock_sb.table().select().is_().execute.return_value.data = [
        {"plan": "free", "status": "active", "language": "pt", "referral_count": 0, "total_clicks": 1, "created_at": now.isoformat(), "referred_by": "uuid-1"},
        {"plan": "free", "status": "active", "language": "pt", "referral_count": 0, "total_clicks": 1, "created_at": now.isoformat(), "referred_by": None},
    ]
    mock_sb.table().select().execute.return_value.data = []
    mock_sb.table().select().gte().execute.return_value.data = []

    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_analytics()
    assert result["members"]["via_referral"] == 1
