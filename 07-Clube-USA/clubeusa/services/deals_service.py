"""
Deal feed service — Fase 1.1

Urgency layer on top of the existing deals table:
  - expired deals (expires_at <= NOW) are silently excluded from the feed
  - deals expiring within 24 h get is_urgent=True + expires_in_hours so the
    frontend can render a countdown badge
  - urgent deals bubble to the top of the feed; secondary sort is score DESC

Commission/payout logic is NOT here — see DECISOES.md D-006.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

log = logging.getLogger("deals_service")

_URGENCY_WINDOW_H = 24  # hours before expiry to show urgency badge


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def get_member_deals(
    plan: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Return active (non-expired) deals with urgency signals for a member.

    VIP members see approved+sent deals (up to 50); free members see only
    sent (up to 20). Expired deals are silently excluded. Urgent deals
    (expiring within 24 h) appear at the top.
    """
    if plan == "vip":
        status_filter = ["approved", "sent"]
        limit = min(limit, 50)
    else:
        status_filter = ["sent"]
        limit = min(limit, 20)

    # Fetch a small buffer so filtering expired rows still fills the page.
    fetch_limit = limit + 10

    sb = _supabase()
    query = (
        sb.table("deals")
        .select(
            "id,title,price_now,price_was,discount_pct,rating,reviews,"
            "score,score_label,price_context,image_url,affiliate_url,"
            "category,source,sent_at,expires_at"
        )
        .in_("status", status_filter)
        .order("score", desc=True)
        .limit(fetch_limit)
    )
    if category and category != "all":
        query = query.eq("category", category)

    rows = query.execute().data or []

    now = _now_utc()
    result = []

    for d in rows:
        expires_raw = d.get("expires_at")
        is_urgent = False
        expires_in_hours: Optional[float] = None

        if expires_raw:
            exp = _parse_ts(expires_raw)
            remaining = (exp - now).total_seconds() / 3600
            if remaining <= 0:
                continue  # expired — exclude from feed
            if remaining <= _URGENCY_WINDOW_H:
                is_urgent = True
                expires_in_hours = round(remaining, 1)

        d["is_urgent"] = is_urgent
        d["expires_in_hours"] = expires_in_hours
        result.append(d)

        if len(result) >= limit:
            break

    # Urgent deals first, then highest score
    result.sort(key=lambda x: (not x["is_urgent"], -(x.get("score") or 0)))
    return result
