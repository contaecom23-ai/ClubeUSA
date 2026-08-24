import pytest
from unittest.mock import MagicMock


def _mock_sb():
    return MagicMock()


# ---- get_metrics ----

def test_get_metrics_returns_expected_keys(mocker):
    from services.admin_service import get_metrics
    mock_sb = _mock_sb()
    # members total
    mock_sb.table().select().execute.return_value.data = [
        {"plan": "free", "status": "active"},
        {"plan": "vip",  "status": "active"},
        {"plan": "free", "status": "inactive"},
    ]
    # clicks this week
    mock_sb.table().select().gte().execute.return_value.data = [{}] * 5
    # deals by status
    mock_sb.table().select().eq().execute.return_value.data = [{}] * 3
    # alerts active
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_metrics()
    assert "members" in result
    assert "deals" in result
    assert "engagement" in result
    assert "alerts" in result


# ---- list_members ----

def test_list_members_returns_list(mocker):
    from services.admin_service import list_members
    mock_sb = _mock_sb()
    mock_sb.table().select().order().range().execute.return_value.data = [
        {"id": "m1", "phone_enc": "enc", "name_enc": "enc2", "plan": "free", "status": "active", "points": 100}
    ]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)
    mocker.patch("services.admin_service._decrypt", return_value="decrypted")

    result = list_members()
    assert isinstance(result, list)
    assert len(result) == 1


# ---- set_member_status ----

def test_set_member_status_returns_true(mocker):
    from services.admin_service import set_member_status
    mock_sb = _mock_sb()
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "m1"}]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = set_member_status("m1", "banned")
    assert result is True


def test_set_member_status_invalid_raises(mocker):
    from services.admin_service import set_member_status
    mocker.patch("services.admin_service._supabase", return_value=_mock_sb())

    with pytest.raises(ValueError, match="Status inválido"):
        set_member_status("m1", "suspended")


# ---- approve_deal / reject_deal ----

def test_approve_deal_returns_true(mocker):
    from services.admin_service import approve_deal
    mock_sb = _mock_sb()
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "d1"}]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    assert approve_deal("d1") is True


def test_reject_deal_returns_true(mocker):
    from services.admin_service import reject_deal
    mock_sb = _mock_sb()
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "d1"}]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    assert reject_deal("d1") is True


# ---- get_analytics ----

def _make_analytics_mock(members=None, logins=None, referrals=None):
    """Retorna mock de supabase pré-configurado para get_analytics."""
    mock_sb = MagicMock()

    def table_select_router(table_name):
        mock_table = MagicMock()
        if table_name == "members":
            mock_table.select().execute.return_value.data = members or []
        elif table_name == "audit_logs":
            # encadeia .select().eq().gte().execute()
            mock_table.select().eq().gte().execute.return_value.data = logins or []
        elif table_name == "referrals":
            mock_table.select().gte().execute.return_value.data = referrals or []
        return mock_table

    mock_sb.table.side_effect = table_select_router
    return mock_sb


def test_get_analytics_structure(mocker):
    from services.admin_service import get_analytics

    members = [
        {"created_at": "2026-08-24T10:00:00+00:00", "referred_by": None,  "state": "FL", "plan": "free"},
        {"created_at": "2026-08-23T09:00:00+00:00", "referred_by": "uid1","state": "TX", "plan": "free"},
        {"created_at": "2026-08-22T08:00:00+00:00", "referred_by": "uid1","state": "FL", "plan": "vip"},
    ]
    logins = [
        {"created_at": "2026-08-24T11:00:00+00:00"},
        {"created_at": "2026-08-24T12:00:00+00:00"},
    ]
    refs = [{"created_at": "2026-08-23T09:00:00+00:00"}]

    mocker.patch("services.admin_service._supabase",
                 return_value=_make_analytics_mock(members, logins, refs))

    result = get_analytics(days=7)

    assert "period_days" in result
    assert result["period_days"] == 7
    assert "total_members" in result
    assert result["total_members"] == 3
    assert "referral_rate_pct" in result
    assert "plan_distribution" in result
    assert "top_states" in result
    assert "registrations_by_day" in result
    assert "logins_by_day" in result
    assert "referrals_by_day" in result


def test_get_analytics_series_length(mocker):
    from services.admin_service import get_analytics

    mocker.patch("services.admin_service._supabase",
                 return_value=_make_analytics_mock())

    result = get_analytics(days=14)

    assert len(result["registrations_by_day"]) == 14
    assert len(result["logins_by_day"]) == 14
    assert len(result["referrals_by_day"]) == 14
    assert all("date" in d and "count" in d for d in result["registrations_by_day"])


def test_get_analytics_referral_rate(mocker):
    from services.admin_service import get_analytics

    members = [
        {"created_at": "2026-08-01T00:00:00+00:00", "referred_by": "x", "state": "FL", "plan": "free"},
        {"created_at": "2026-08-01T00:00:00+00:00", "referred_by": None, "state": "CA", "plan": "free"},
    ]
    mocker.patch("services.admin_service._supabase",
                 return_value=_make_analytics_mock(members, [], []))

    result = get_analytics(days=30)
    assert result["referral_rate_pct"] == 50.0


def test_get_analytics_empty_db(mocker):
    from services.admin_service import get_analytics

    mocker.patch("services.admin_service._supabase",
                 return_value=_make_analytics_mock([], [], []))

    result = get_analytics(days=7)
    assert result["total_members"] == 0
    assert result["referral_rate_pct"] == 0.0
    assert all(d["count"] == 0 for d in result["registrations_by_day"])
