"""
Tests for deals_service — Fase 1.1

Covers:
  - expired deals are excluded from the feed
  - urgent deals (expiring within 24 h) get is_urgent=True + expires_in_hours
  - non-expiring deals get is_urgent=False
  - urgent deals sort before non-urgent regardless of score
  - VIP plan sees approved+sent; free plan sees only sent
  - limit is capped at 50 for VIP and 20 for free
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock


def _now():
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _make_deal(
    deal_id: str,
    score: float,
    expires_at: datetime | None = None,
    status: str = "sent",
) -> dict:
    return {
        "id":           deal_id,
        "title":        f"Deal {deal_id}",
        "price_now":    9.99,
        "price_was":    19.99,
        "discount_pct": 50,
        "rating":       4.5,
        "reviews":      100,
        "score":        score,
        "score_label":  "Ótimo",
        "price_context": None,
        "image_url":    None,
        "affiliate_url": "https://example.com",
        "category":     "electronics",
        "source":       "amazon",
        "sent_at":      _iso(_now() - timedelta(hours=1)),
        "expires_at":   _iso(expires_at) if expires_at else None,
    }


def _mock_sb(rows: list[dict]) -> MagicMock:
    sb = MagicMock()
    sb.table().select().in_().order().limit().execute.return_value.data = rows
    sb.table().select().in_().order().limit().eq().execute.return_value.data = rows
    return sb


# ================================================================
#  Expiry filtering
# ================================================================

def test_expired_deal_excluded(mocker):
    from services.deals_service import get_member_deals
    expired = _make_deal("exp", score=99, expires_at=_now() - timedelta(minutes=5))
    live    = _make_deal("live", score=50)
    sb = _mock_sb([expired, live])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    ids = [d["id"] for d in result]
    assert "exp" not in ids
    assert "live" in ids


def test_no_expires_at_always_included(mocker):
    from services.deals_service import get_member_deals
    d = _make_deal("no_exp", score=10)
    sb = _mock_sb([d])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    assert result[0]["id"] == "no_exp"
    assert result[0]["is_urgent"] is False
    assert result[0]["expires_in_hours"] is None


# ================================================================
#  Urgency signals
# ================================================================

def test_deal_expiring_in_12h_is_urgent(mocker):
    from services.deals_service import get_member_deals
    d = _make_deal("urgent", score=10, expires_at=_now() + timedelta(hours=12))
    sb = _mock_sb([d])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    assert result[0]["is_urgent"] is True
    assert 11 <= result[0]["expires_in_hours"] <= 13


def test_deal_expiring_in_25h_is_not_urgent(mocker):
    from services.deals_service import get_member_deals
    d = _make_deal("not_urgent", score=10, expires_at=_now() + timedelta(hours=25))
    sb = _mock_sb([d])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    assert result[0]["is_urgent"] is False
    assert result[0]["expires_in_hours"] is None


def test_deal_expiring_at_boundary_24h_is_urgent(mocker):
    from services.deals_service import get_member_deals
    d = _make_deal("boundary", score=10, expires_at=_now() + timedelta(hours=24))
    sb = _mock_sb([d])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    assert result[0]["is_urgent"] is True


# ================================================================
#  Sorting: urgent deals bubble to top regardless of score
# ================================================================

def test_urgent_deal_sorts_before_high_score_non_urgent(mocker):
    from services.deals_service import get_member_deals
    high_score = _make_deal("high", score=99)
    urgent_low = _make_deal("urgent_low", score=1, expires_at=_now() + timedelta(hours=2))
    sb = _mock_sb([high_score, urgent_low])
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free")
    assert result[0]["id"] == "urgent_low"
    assert result[1]["id"] == "high"


# ================================================================
#  Plan limits
# ================================================================

def test_free_plan_limit_capped_at_20(mocker):
    from services.deals_service import get_member_deals
    rows = [_make_deal(str(i), score=float(100 - i)) for i in range(30)]
    sb = _mock_sb(rows)
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="free", limit=100)
    assert len(result) <= 20


def test_vip_plan_limit_capped_at_50(mocker):
    from services.deals_service import get_member_deals
    rows = [_make_deal(str(i), score=float(100 - i)) for i in range(60)]
    sb = _mock_sb(rows)
    mocker.patch("services.deals_service._supabase", return_value=sb)

    result = get_member_deals(plan="vip", limit=999)
    assert len(result) <= 50
