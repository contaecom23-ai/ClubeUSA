from typing import Optional
from pydantic import BaseModel


class ReferralStatsResponse(BaseModel):
    slug: Optional[str]
    referral_url: Optional[str]
    signup_count: int
    click_count: int
