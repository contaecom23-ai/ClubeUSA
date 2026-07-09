import logging
from collections import Counter
from typing import Optional

from fastapi import HTTPException, status
from supabase import Client

from influencer.schemas import InfluencerTier, InfluencerStats, LeaderboardEntry, LeaderboardResponse, TierProgress

logger = logging.getLogger(__name__)

# Tier thresholds (valid referrals needed)
_TIER_THRESHOLDS: list[tuple[InfluencerTier, int]] = [
    (InfluencerTier.hall_da_fama, 1000),
    (InfluencerTier.embaixador, 250),
    (InfluencerTier.parceiro, 50),
]


def compute_tier(valid_referral_count: int) -> InfluencerTier:
    for tier, threshold in _TIER_THRESHOLDS:
        if valid_referral_count >= threshold:
            return tier
    return InfluencerTier.none


def compute_tier_progress(valid_referral_count: int) -> TierProgress:
    current = compute_tier(valid_referral_count)

    if current == InfluencerTier.hall_da_fama:
        return TierProgress(next_tier=None, referrals_needed=0, progress_pct=100)

    if current == InfluencerTier.embaixador:
        needed = 1000 - valid_referral_count
        pct = int((valid_referral_count - 250) / (1000 - 250) * 100)
        return TierProgress(next_tier=InfluencerTier.hall_da_fama, referrals_needed=needed, progress_pct=pct)

    if current == InfluencerTier.parceiro:
        needed = 250 - valid_referral_count
        pct = int((valid_referral_count - 50) / (250 - 50) * 100)
        return TierProgress(next_tier=InfluencerTier.embaixador, referrals_needed=needed, progress_pct=pct)

    # none
    needed = 50 - valid_referral_count
    pct = int(valid_referral_count / 50 * 100) if valid_referral_count > 0 else 0
    return TierProgress(next_tier=InfluencerTier.parceiro, referrals_needed=needed, progress_pct=pct)


def _count_valid_referrals_for_slug(supabase: Client, slug: str) -> int:
    """
    Conta cadastros válidos atribuídos ao slug.
    Critério: referred_by_slug = slug AND zip_code != '' (proxy sem chamada por usuário).
    Alinha com count_valid_registrations_approx() da Fase 0.4.
    """
    try:
        result = (
            supabase.table("profiles")
            .select("id", count="exact")
            .eq("referred_by_slug", slug)
            .neq("zip_code", "")
            .execute()
        )
        return int(result.count or 0)
    except Exception as e:
        logger.error("_count_valid_referrals_for_slug error: %s", type(e).__name__)
        return 0


def _count_total_referrals_for_slug(supabase: Client, slug: str) -> int:
    """Total de cadastros via este link (válidos ou não) — para exibição."""
    try:
        result = (
            supabase.table("profiles")
            .select("id", count="exact")
            .eq("referred_by_slug", slug)
            .execute()
        )
        return int(result.count or 0)
    except Exception as e:
        logger.error("_count_total_referrals_for_slug error: %s", type(e).__name__)
        return 0


def _format_cents(cents: int) -> str:
    return f"{cents / 100:.2f}"


def get_influencer_stats(
    supabase: Client,
    user_id: str,
    payment_per_referral_cents: int,
    monthly_cap_cents: int,
) -> InfluencerStats:
    try:
        profile = (
            supabase.table("profiles")
            .select("referral_slug")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )

    if not profile.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )

    slug: Optional[str] = profile.data.get("referral_slug")

    if not slug:
        return InfluencerStats(
            slug=None,
            referral_url=None,
            valid_referral_count=0,
            total_referral_count=0,
            tier=InfluencerTier.none,
            tier_progress=compute_tier_progress(0),
            pending_credits_cents=0,
            pending_credits_usd="0.00",
            payment_per_referral_usd=_format_cents(payment_per_referral_cents),
            monthly_cap_usd=_format_cents(monthly_cap_cents),
        )

    valid_count = _count_valid_referrals_for_slug(supabase, slug)
    total_count = _count_total_referrals_for_slug(supabase, slug)
    tier = compute_tier(valid_count)
    progress = compute_tier_progress(valid_count)
    pending_cents = valid_count * payment_per_referral_cents

    return InfluencerStats(
        slug=slug,
        referral_url=f"/i/{slug}",
        valid_referral_count=valid_count,
        total_referral_count=total_count,
        tier=tier,
        tier_progress=progress,
        pending_credits_cents=pending_cents,
        pending_credits_usd=_format_cents(pending_cents),
        payment_per_referral_usd=_format_cents(payment_per_referral_cents),
        monthly_cap_usd=_format_cents(monthly_cap_cents),
    )


def get_leaderboard(supabase: Client, limit: int = 20) -> LeaderboardResponse:
    """
    Top influencers por cadastros válidos.
    Abordagem: busca todos os referrals válidos e agrupa em Python.
    Aceitável até ~100k perfis; escalar para view materializada no banco quando necessário.
    """
    try:
        # Todos os cadastros com referred_by_slug preenchido + zip válido
        result = (
            supabase.table("profiles")
            .select("referred_by_slug")
            .neq("referred_by_slug", None)
            .neq("zip_code", "")
            .execute()
        )
        rows = result.data or []
    except Exception as e:
        logger.error("get_leaderboard: query error: %s", type(e).__name__)
        rows = []

    # Conta por slug em Python
    counts: Counter = Counter(r["referred_by_slug"] for r in rows if r.get("referred_by_slug"))
    top = counts.most_common(limit)
    total_influencers = len(counts)

    if not top:
        return LeaderboardResponse(entries=[], total_influencers=0)

    # Busca nomes dos top influenciadores
    top_slugs = [slug for slug, _ in top]
    try:
        profiles_result = (
            supabase.table("profiles")
            .select("referral_slug, first_name")
            .in_("referral_slug", top_slugs)
            .execute()
        )
        name_map = {
            p["referral_slug"]: p.get("first_name", "")
            for p in (profiles_result.data or [])
        }
    except Exception as e:
        logger.error("get_leaderboard: name lookup error: %s", type(e).__name__)
        name_map = {}

    entries = [
        LeaderboardEntry(
            rank=rank + 1,
            slug=slug,
            first_name=name_map.get(slug, ""),
            valid_referral_count=count,
            tier=compute_tier(count),
        )
        for rank, (slug, count) in enumerate(top)
    ]

    return LeaderboardResponse(entries=entries, total_influencers=total_influencers)
