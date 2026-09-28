"""
Influencer tier tracking — Fase 1.3

Tiers (based on valid OTP-verified referrals stored in members.referral_count):
  Parceiro     >=  50
  Embaixador   >= 250
  Hall da Fama >= 1000

Commission amounts per valid referral and monthly bonuses are a business decision.
See DECISOES.md D-006. This module only handles tracking and tier computation.
"""
import os
import logging

log = logging.getLogger("influencer_service")

_TIERS = [
    ("hall_da_fama", 1000),
    ("embaixador",   250),
    ("parceiro",     50),
]

TIER_LABELS = {
    "hall_da_fama": "Hall da Fama",
    "embaixador":   "Embaixador",
    "parceiro":     "Parceiro",
}

_NEXT_TIER = {
    None:           ("parceiro",     50),
    "parceiro":     ("embaixador",   250),
    "embaixador":   ("hall_da_fama", 1000),
    "hall_da_fama": None,
}


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def compute_tier(referral_count: int) -> str | None:
    """Pure function: return tier slug for the given referral_count."""
    for slug, threshold in _TIERS:
        if referral_count >= threshold:
            return slug
    return None


def get_influencer_stats(member_id: str) -> dict:
    """Return influencer tier stats for a given member_id."""
    sb = _supabase()

    result = sb.table("members").select(
        "id,referral_code,referral_count,points,level"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro não encontrado.")

    m = result.data[0]
    count = m["referral_count"] or 0
    tier  = compute_tier(count)
    next_entry = _NEXT_TIER.get(tier)

    # rank among all members with referrals (higher = better)
    above_result = sb.table("members").select("id", count="exact").gt(
        "referral_count", count
    ).execute()
    rank = (above_result.count or 0) + 1 if above_result.count is not None else None

    return {
        "referral_code":    m["referral_code"],
        "valid_referrals":  count,
        "tier":             tier,
        "tier_label":       TIER_LABELS.get(tier, "Sem selo"),
        "rank":             rank,
        "next_tier":        next_entry[0] if next_entry else None,
        "next_tier_label":  TIER_LABELS.get(next_entry[0]) if next_entry else None,
        "next_tier_at":     next_entry[1] if next_entry else None,
        "referrals_needed": (next_entry[1] - count) if next_entry else 0,
    }


def list_influencers(min_referrals: int = 10, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return members sorted by referral_count desc — admin view only.

    Names are not included to avoid unnecessary PII decryption;
    referral_code is the opaque identifier.
    """
    limit  = min(max(limit, 1), 200)
    offset = max(offset, 0)
    min_referrals = max(min_referrals, 1)

    sb = _supabase()
    result = (
        sb.table("members")
        .select("id,referral_code,referral_count,points,plan,status,created_at")
        .gte("referral_count", min_referrals)
        .order("referral_count", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    rows = []
    for m in (result.data or []):
        count = m["referral_count"] or 0
        tier  = compute_tier(count)
        rows.append({
            "member_id":       m["id"],
            "referral_code":   m["referral_code"],
            "valid_referrals": count,
            "tier":            tier,
            "tier_label":      TIER_LABELS.get(tier, "Sem selo"),
            "points":          m["points"],
            "plan":            m["plan"],
            "status":          m["status"],
            "joined_at":       m["created_at"],
        })
    return rows
