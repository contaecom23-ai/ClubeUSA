"""
Testes para get_growth_analytics — Fase 0.3
Usa apenas dados existentes em members.created_at (sem migração).
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock


def _make_members(n: int, days_back: int = 10, with_referral: int = 0):
    now = datetime.now(timezone.utc)
    members = []
    for i in range(n):
        d = now - timedelta(days=i % max(days_back, 1))
        members.append({
            "id": f"id-{i}",
            "plan": "vip" if i < 2 else "free",
            "referred_by": f"ref-{i}" if i < with_referral else None,
            "created_at": d.isoformat(),
        })
    return members


def _mock_sb(members):
    mock_client = MagicMock()
    (mock_client.table.return_value
     .select.return_value
     .gte.return_value
     .execute.return_value.data) = members
    return mock_client


@patch("services.admin_service._supabase")
def test_returns_correct_series_length(mock_sb):
    from services.admin_service import get_growth_analytics
    mock_sb.return_value = _mock_sb(_make_members(10))

    result = get_growth_analytics(30)

    assert result["days"] == 30
    assert len(result["daily_registrations"]) == 30
    assert result["total_registrations"] == 10


@patch("services.admin_service._supabase")
def test_returns_7_day_series(mock_sb):
    from services.admin_service import get_growth_analytics
    mock_sb.return_value = _mock_sb(_make_members(5))

    result = get_growth_analytics(7)

    assert result["days"] == 7
    assert len(result["daily_registrations"]) == 7


@patch("services.admin_service._supabase")
def test_referral_rate_calculated_correctly(mock_sb):
    from services.admin_service import get_growth_analytics
    members = _make_members(10, with_referral=4)
    mock_sb.return_value = _mock_sb(members)

    result = get_growth_analytics(30)

    assert result["via_referral"] == 4
    assert result["referral_conversion_rate"] == 0.4


@patch("services.admin_service._supabase")
def test_plan_breakdown_counts_correctly(mock_sb):
    from services.admin_service import get_growth_analytics
    mock_sb.return_value = _mock_sb(_make_members(10))

    result = get_growth_analytics(30)

    assert result["plan_breakdown"]["vip"] == 2
    assert result["plan_breakdown"]["free"] == 8
    assert result["plan_breakdown"]["vip"] + result["plan_breakdown"]["free"] == 10


@patch("services.admin_service._supabase")
def test_empty_period_returns_zeroed_series(mock_sb):
    from services.admin_service import get_growth_analytics
    mock_sb.return_value = _mock_sb([])

    result = get_growth_analytics(7)

    assert result["total_registrations"] == 0
    assert result["referral_conversion_rate"] == 0.0
    assert all(entry["count"] == 0 for entry in result["daily_registrations"])


@patch("services.admin_service._supabase")
def test_series_dates_are_ascending(mock_sb):
    from services.admin_service import get_growth_analytics
    mock_sb.return_value = _mock_sb([])

    result = get_growth_analytics(14)

    dates = [e["date"] for e in result["daily_registrations"]]
    assert dates == sorted(dates), "Série deve estar em ordem cronológica ascendente"


@patch("services.admin_service._supabase")
def test_period_end_is_today(mock_sb):
    from services.admin_service import get_growth_analytics
    from datetime import date
    mock_sb.return_value = _mock_sb([])

    result = get_growth_analytics(30)

    assert result["period_end"] == date.today().isoformat()


@patch("services.admin_service._supabase")
def test_no_referral_rate_is_zero_not_error(mock_sb):
    from services.admin_service import get_growth_analytics
    members = _make_members(5, with_referral=0)
    mock_sb.return_value = _mock_sb(members)

    result = get_growth_analytics(30)

    assert result["referral_conversion_rate"] == 0.0
    assert result["via_referral"] == 0
