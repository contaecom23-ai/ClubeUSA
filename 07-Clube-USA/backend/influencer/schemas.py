from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class InfluencerTier(str, Enum):
    none = "none"
    parceiro = "parceiro"          # 50+ referrals
    embaixador = "embaixador"      # 250+ referrals
    hall_da_fama = "hall_da_fama"  # 1000+ referrals


class TierProgress(BaseModel):
    next_tier: Optional[InfluencerTier]
    referrals_needed: int
    progress_pct: int  # 0–100


class InfluencerStats(BaseModel):
    slug: Optional[str]
    referral_url: Optional[str]
    valid_referral_count: int
    total_referral_count: int
    tier: InfluencerTier
    tier_progress: TierProgress
    # Créditos estimados — exibição apenas. Pagamentos reais dependem de Fase 5.
    pending_credits_cents: int
    pending_credits_usd: str  # ex: "18.00"
    payment_per_referral_usd: str  # ex: "2.00"
    monthly_cap_usd: str           # ex: "100.00"


class LeaderboardEntry(BaseModel):
    rank: int
    slug: str
    first_name: str
    valid_referral_count: int
    tier: InfluencerTier


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_influencers: int
