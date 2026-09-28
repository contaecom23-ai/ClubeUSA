"""tests/test_influencer_service.py — Fase 1.3 influencer tiers"""
import pytest
from unittest.mock import MagicMock


# ---- get_tier (função pura — sem mock necessário) ----

def test_get_tier_no_referrals():
    from services.influencer_service import get_tier
    r = get_tier(0)
    assert r["tier"] is None
    assert r["tier_label"] == "Sem selo"
    assert r["next_tier"] == "parceiro"
    assert r["referrals_needed"] == 50


def test_get_tier_below_parceiro():
    from services.influencer_service import get_tier
    r = get_tier(49)
    assert r["tier"] is None
    assert r["next_tier"] == "parceiro"
    assert r["referrals_needed"] == 1


def test_get_tier_exact_parceiro():
    from services.influencer_service import get_tier
    r = get_tier(50)
    assert r["tier"] == "parceiro"
    assert r["tier_label"] == "Parceiro"
    assert r["next_tier"] == "embaixador"
    assert r["referrals_needed"] == 200


def test_get_tier_between_parceiro_embaixador():
    from services.influencer_service import get_tier
    r = get_tier(100)
    assert r["tier"] == "parceiro"
    assert r["next_tier"] == "embaixador"
    assert r["referrals_needed"] == 150


def test_get_tier_exact_embaixador():
    from services.influencer_service import get_tier
    r = get_tier(250)
    assert r["tier"] == "embaixador"
    assert r["tier_label"] == "Embaixador"
    assert r["next_tier"] == "hall_da_fama"
    assert r["referrals_needed"] == 750


def test_get_tier_exact_hall_da_fama():
    from services.influencer_service import get_tier
    r = get_tier(1000)
    assert r["tier"] == "hall_da_fama"
    assert r["tier_label"] == "Hall da Fama"
    assert r["next_tier"] is None
    assert r["referrals_needed"] == 0


def test_get_tier_beyond_hall_da_fama():
    from services.influencer_service import get_tier
    r = get_tier(9999)
    assert r["tier"] == "hall_da_fama"
    assert r["next_tier"] is None
    assert r["referrals_needed"] == 0


# ---- get_member_influencer_stats ----

def test_get_member_influencer_stats_returns_tier(mocker):
    from services.influencer_service import get_member_influencer_stats
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"referral_code": "ABCD1234", "referral_count": 75}
    ]
    mocker.patch("services.influencer_service._supabase", return_value=mock_sb)

    r = get_member_influencer_stats("member-uuid")
    assert r["tier"] == "parceiro"
    assert r["valid_referrals"] == 75
    assert r["referral_code"] == "ABCD1234"


def test_get_member_influencer_stats_not_found(mocker):
    from services.influencer_service import get_member_influencer_stats
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=mock_sb)

    assert get_member_influencer_stats("ghost-id") is None


# ---- list_influencers ----

def test_list_influencers_with_tiers(mocker):
    from services.influencer_service import list_influencers
    mock_sb = MagicMock()
    mock_sb.table().select().gte().order().limit().execute.return_value.data = [
        {"id": "u1", "referral_code": "AAA", "referral_count": 1200, "created_at": "2026-01-01"},
        {"id": "u2", "referral_code": "BBB", "referral_count": 300, "created_at": "2026-02-01"},
        {"id": "u3", "referral_code": "CCC", "referral_count": 60,  "created_at": "2026-03-01"},
    ]
    mocker.patch("services.influencer_service._supabase", return_value=mock_sb)

    rows = list_influencers(min_referrals=1)
    assert len(rows) == 3
    assert rows[0]["tier"] == "hall_da_fama"
    assert rows[1]["tier"] == "embaixador"
    assert rows[2]["tier"] == "parceiro"
    # PII: IDs estão presentes para admin, mas sem name/phone
    assert "id" in rows[0]


def test_list_influencers_empty(mocker):
    from services.influencer_service import list_influencers
    mock_sb = MagicMock()
    mock_sb.table().select().gte().order().limit().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=mock_sb)

    assert list_influencers() == []


def test_list_influencers_min_referrals_filter(mocker):
    """Confirma que min_referrals é passado para a query (isolamento de dados)."""
    from services.influencer_service import list_influencers
    mock_sb = MagicMock()
    mock_sb.table().select().gte().order().limit().execute.return_value.data = []
    mocker.patch("services.influencer_service._supabase", return_value=mock_sb)

    list_influencers(min_referrals=50)
    mock_sb.table().select().gte.assert_called_with("referral_count", 50)
