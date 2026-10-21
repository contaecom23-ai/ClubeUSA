from typing import List
from pydantic import BaseModel


class DailyCount(BaseModel):
    date: str
    count: int


class AnalyticsSummary(BaseModel):
    signups_today: int
    signups_last_7d: int
    signups_last_30d: int
    logins_today: int
    logins_last_7d: int
    referral_clicks_last_7d: int
    referral_conversions_last_7d: int
    referral_conversion_rate: float
    daily_signups_last_30d: List[DailyCount]
