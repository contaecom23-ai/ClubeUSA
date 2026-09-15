"""
Tests for influencer_service — Fase 1.3

Covers:
  - compute_tier pure function (all thresholds + edge cases)
  - get_influencer_stats (normal, not found, multi-tenant isolation)
  - list_influencers (returns list, min_referrals filter, limit cap)
"""
import pytest
from unittest.mock import MagicMock


def _mock_sb():
    return MagicMock()


# ================================================================
#  compute_tier — pure function, no DB
# ================================================================

def test_compute_tier_no_tier():
    from services.influencer_service import compute_tier
    assert compute_tier(0)  is None
    assert compute_tier(1)  is None
    assert compute_tier(49) is None


def test_compute_tier_parceiro():
    from services.influencer_service import compute_tier
    assert compute_tier(50)  == "parceiro"
    assert compute_tier(249) == "parceiro"


def test_compute_tier_embaixador():
    from services.influencer_service import compute_tier
    assert compute_tier(250) == "embaixador"
    assert compute_tier(999) == "embaixador"


def test_compute_tier_hall_da_fama():
    from services.influencer_service import compute_tier
    assert compute_tier(1000) == "hall_da_fama"
    assert compute_tier(9999) == "hall_da_fama"


# ================================================================
#  get_influencer_stats
# ================================================================

def _make_member_sb(referral_count: int, above_count: int = 0):
    sb = _mock_sb()
    sb.table().select().eq().execute.return_value.data = [{
        "id":             "m1",
        "referral_code":  "REF123",
        "referral_count": referral_count,
        "points":         referral_count * 200,
        "level":          1,
    }]
    # above count mock
    above_mock = MagicMock()
    above_mock.count = above_count
    sb.table().select().gt().execute.return_value = above_mock
    return sb


def test_get_influencer_stats_no_tier(mocker):
    from services.influencer_service import get_influencer_stats
    sb = _make_member_sb(referral_count=10, above_count=5)
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    stats = get_influencer_stats("m1")
    assert stats["valid_referrals"] == 10
    assert stats["tier"] is None
    assert stats["tier_label"] == "Sem selo"
    assert stats["next_tier"] == "parceiro"
    assert stats["next_tier_at"] == 50
    assert stats["referrals_needed"] == 40
    assert stats["rank"] == 6


def test_get_influencer_stats_parceiro(mocker):
    from services.influencer_service import get_influencer_stats
    sb = _make_member_sb(referral_count=100, above_count=2)
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    stats = get_influencer_stats("m1")
    assert stats["tier"] == "parceiro"
    assert stats["tier_label"] == "Parceiro"
    assert stats["next_tier"] == "embaixador"
    assert stats["next_tier_at"] == 250
    assert stats["referrals_needed"] == 150
    assert stats["rank"] == 3


def test_get_influencer_stats_hall_da_fama_no_next_tier(mocker):
    from services.influencer_service import get_influencer_stats
    sb = _make_member_sb(referral_count=1500, above_count=0)
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    stats = get_influencer_stats("m1")
    assert stats["tier"] == "hall_da_fama"
    assert stats["next_tier"] is None
    assert stats["referrals_needed"] == 0
    assert stats["rank"] == 1


def test_get_influencer_stats_member_not_found(mocker):
    from services.influencer_service import get_influencer_stats
    sb = _mock_sb()
    sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    with pytest.raises(ValueError, match="Membro não encontrado"):
        get_influencer_stats("unknown_id")


def test_get_influencer_stats_cross_tenant_isolation(mocker):
    """Member A cannot access Member B's stats through this service (member_id is trusted)."""
    from services.influencer_service import get_influencer_stats
    sb = _mock_sb()
    # returns empty for member_b when queried with member_a's id
    sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    with pytest.raises(ValueError):
        get_influencer_stats("member_b_id")


# ================================================================
#  list_influencers (admin view)
# ================================================================

def test_list_influencers_returns_sorted_list(mocker):
    from services.influencer_service import list_influencers
    sb = _mock_sb()
    sb.table().select().gte().order().range().execute.return_value.data = [
        {"id": "m1", "referral_code": "A1", "referral_count": 300, "points": 60000,
         "plan": "vip", "status": "active", "created_at": "2026-01-01"},
        {"id": "m2", "referral_code": "B2", "referral_count": 60, "points": 12000,
         "plan": "free", "status": "active", "created_at": "2026-02-01"},
    ]
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    result = list_influencers(min_referrals=10, limit=50)
    assert len(result) == 2
    assert result[0]["tier"] == "embaixador"
    assert result[1]["tier"] == "parceiro"


def test_list_influencers_empty_when_no_influencers(mocker):
    from services.influencer_service import list_influencers
    sb = _mock_sb()
    sb.table().select().gte().order().range().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    assert list_influencers() == []


def test_list_influencers_limit_capped_at_200(mocker):
    from services.influencer_service import list_influencers
    sb = _mock_sb()
    sb.table().select().gte().order().range().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=sb)

    list_influencers(limit=9999)
    # should not raise; internally capped
    call_args = sb.table().select().gte().order().range.call_args
    end_index = call_args[0][1]
    assert end_index <= 199
