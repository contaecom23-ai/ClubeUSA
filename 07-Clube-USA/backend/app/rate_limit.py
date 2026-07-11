"""
Rate limiting via the auth_rate_limit table in Supabase.
Simple sliding-window counter — good enough for 1k-10k users; upgrade to Redis for 100k+.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from supabase import Client


def check_rate_limit(
    db: Client,
    key: str,
    action: str,
    max_attempts: int,
    window_seconds: int,
) -> None:
    """
    Insert an attempt record and check if the count in the window exceeds max_attempts.
    Raises HTTP 429 if over limit.
    """
    now = datetime.now(tz=timezone.utc)
    window_start = (now - timedelta(seconds=window_seconds)).isoformat()

    # Count recent attempts within the window
    count_result = db.table("auth_rate_limit") \
        .select("id", count="exact") \
        .eq("key", key) \
        .eq("action", action) \
        .gte("attempted_at", window_start) \
        .execute()

    count = count_result.count or 0

    if count >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Please wait before trying again.",
            headers={"Retry-After": str(window_seconds)},
        )

    # Record this attempt
    db.table("auth_rate_limit").insert({
        "key": key,
        "action": action,
        "attempted_at": now.isoformat(),
    }).execute()
