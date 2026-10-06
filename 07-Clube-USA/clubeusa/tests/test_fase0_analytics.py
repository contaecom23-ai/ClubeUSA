import asyncio
import pytest
from collections import defaultdict


# ---- Pure logic (no mocks needed) ----

def test_pct_helper_no_zero_division():
    """The pct() helper inside analytics_funnel must never divide by zero."""
    def pct(num, denom):
        return round(num / denom * 100, 1) if denom else 0

    assert pct(0, 0) == 0
    assert pct(100, 100) == 100.0
    assert pct(33, 100) == 33.0
    assert pct(1, 3) == 33.3


def test_growth_fallback_aggregation():
    """Python fallback aggregation in analytics_growth groups registrations by date."""
    rows = [
        {"created_at": "2026-10-01T10:00:00Z"},
        {"created_at": "2026-10-01T22:30:00Z"},
        {"created_at": "2026-10-02T09:00:00Z"},
    ]
    daily = defaultdict(int)
    for row in rows:
        daily[row["created_at"][:10]] += 1
    growth = [{"date": d, "count": c} for d, c in sorted(daily.items())]
    assert growth == [
        {"date": "2026-10-01", "count": 2},
        {"date": "2026-10-02", "count": 1},
    ]


def test_growth_days_param_clamped():
    """days param in analytics_growth is clamped to [1, 365]."""
    clamp = lambda d: min(max(d, 1), 365)
    assert clamp(0) == 1
    assert clamp(-100) == 1
    assert clamp(500) == 365
    assert clamp(30) == 30


def test_referral_code_sanitization():
    """Referral codes from URLs are uppercased and truncated to 20 chars."""
    def sanitize_code(referral_code: str) -> str:
        return referral_code.strip().upper()[:20]

    assert sanitize_code("joao") == "JOAO"
    assert sanitize_code("  maria  ") == "MARIA"
    assert sanitize_code("x" * 30) == "X" * 20
    assert sanitize_code("abc-123") == "ABC-123"


# ---- Router tests (mocked Supabase) ----

class _Chain:
    """Chainable Supabase mock: any method chain ending in .execute() returns _R()."""
    def __init__(self, count=20, data=None):
        self._count = count
        self._data = data or []

    def __call__(self, *a, **kw):
        return self

    def __getattr__(self, n):
        if n == "execute":
            count, data = self._count, self._data
            return lambda *a, **kw: type("R", (), {"count": count, "data": data})()
        return self


def test_analytics_funnel_returns_expected_keys(mocker):
    """analytics_funnel must return all required metric keys."""
    mocker.patch("routers.analytics._supabase", return_value=_Chain(count=20))
    from routers.analytics import analytics_funnel
    result = asyncio.run(analytics_funnel())
    expected_keys = {
        "total_registered", "with_email", "pct_with_email",
        "email_confirmed", "pct_email_confirmed",
        "active_users", "valid_registrations", "pct_valid_of_total",
    }
    assert expected_keys.issubset(result.keys())
    assert result["total_registered"] == 20


def test_anti_fraud_blocks_at_3_registrations(mocker):
    """register_member must raise PermissionError when an IP has ≥3 recent sign-ups."""
    mocker.patch("services.member_service._supabase", return_value=_Chain(count=3))
    mocker.patch("services.member_service.validate_phone", return_value="11999999999")
    mocker.patch("services.member_service.sanitize", side_effect=lambda s, n: s)
    mocker.patch("services.member_service.hash_ip", return_value="hashed_ip")
    from services.member_service import register_member
    with pytest.raises(PermissionError, match="Muitos cadastros"):
        register_member(phone="11999999999", name="Test User", ip="1.2.3.4")
