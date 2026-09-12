"""
Tests for Fase 0.2 (referral redirect) and Fase 0.3 (analytics time-series).
"""
import pytest
from unittest.mock import MagicMock


# ============================================================
#  FASE 0.3 — get_growth_analytics
# ============================================================

def test_growth_analytics_returns_expected_keys(mocker):
    from services.admin_service import get_growth_analytics
    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = [
        {"created_at": "2026-09-10T12:00:00Z"},
        {"created_at": "2026-09-11T08:00:00Z"},
    ]
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth_analytics(days=7)

    assert "series" in result
    assert "period_days" in result
    assert "total_signups" in result
    assert "total_referrals" in result
    assert "referral_rate_pct" in result
    assert result["period_days"] == 7
    assert isinstance(result["series"], list)
    assert len(result["series"]) == 7


def test_growth_analytics_series_has_correct_fields(mocker):
    from services.admin_service import get_growth_analytics
    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth_analytics(days=3)

    for item in result["series"]:
        assert "date" in item
        assert "signups" in item
        assert "referrals" in item


def test_growth_analytics_zero_division_safe(mocker):
    from services.admin_service import get_growth_analytics
    mock_sb = MagicMock()
    mock_sb.table().select().gte().execute.return_value.data = []
    mocker.patch("services.admin_service._supabase", return_value=mock_sb)

    result = get_growth_analytics(days=7)
    assert result["referral_rate_pct"] == 0
    assert result["total_signups"] == 0


# ============================================================
#  FASE 0.2 — /i/{code} redirect
# ============================================================

def test_referral_redirect_valid_code(mocker):
    import os
    os.environ.setdefault("SUPABASE_URL", "http://fake")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-key")
    os.environ.setdefault("SECRET_KEY", "fake-secret-32-chars-padded-here")
    os.environ.setdefault("APP_URL", "https://clubeusa.com")

    from fastapi.testclient import TestClient
    # Patch supabase before importing app
    mocker.patch("supabase.create_client", return_value=MagicMock())

    import importlib, sys
    # Remove cached modules so env vars take effect
    for mod in list(sys.modules.keys()):
        if mod.startswith(("api.main", "services", "utils", "deps", "routers")):
            del sys.modules[mod]

    import api.main as app_module
    client = TestClient(app_module.app, follow_redirects=False)

    resp = client.get("/i/ABC123")
    assert resp.status_code == 302
    assert "ref=ABC123" in resp.headers["location"]


def test_referral_redirect_invalid_code_returns_404(mocker):
    import os
    os.environ.setdefault("APP_URL", "https://clubeusa.com")

    from fastapi.testclient import TestClient
    mocker.patch("supabase.create_client", return_value=MagicMock())

    import sys
    for mod in list(sys.modules.keys()):
        if mod.startswith(("api.main", "services", "utils", "deps", "routers")):
            del sys.modules[mod]

    import api.main as app_module
    client = TestClient(app_module.app)

    resp = client.get("/i/INVALID CODE WITH SPACES!")
    assert resp.status_code == 404
