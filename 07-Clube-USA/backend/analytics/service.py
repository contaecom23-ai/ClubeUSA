import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from supabase import Client
from validation.service import count_valid_registrations_approx

logger = logging.getLogger(__name__)

VALID_EVENT_TYPES = frozenset({
    "user.registered",
    "user.logged_in",
    "referral.converted",
    "registration.blocked",  # tentativa bloqueada por anti-fraude (email descartável etc)
})


def track_event(
    supabase: Client,
    event_type: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Registra evento de analytics. Fire-and-forget: nunca lança exceção."""
    if event_type not in VALID_EVENT_TYPES:
        logger.warning("track_event: tipo desconhecido '%s' ignorado", event_type)
        return
    try:
        row: dict = {"event_type": event_type, "metadata": metadata or {}}
        if user_id:
            row["user_id"] = user_id
        supabase.table("analytics_events").insert(row).execute()
    except Exception as exc:
        logger.error("track_event falhou event_type=%s: %s", event_type, type(exc).__name__)


def _count_events(supabase: Client, event_type: str, since_iso: str) -> int:
    try:
        res = (
            supabase.table("analytics_events")
            .select("id", count="exact")
            .eq("event_type", event_type)
            .gte("occurred_at", since_iso)
            .execute()
        )
        return res.count or 0
    except Exception as exc:
        logger.error("_count_events event_type=%s: %s", event_type, type(exc).__name__)
        return 0


def get_summary(supabase: Client) -> dict:
    """Agrega métricas para o dashboard de admin."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    since_7d = (now - timedelta(days=7)).isoformat()
    since_30d = (now - timedelta(days=30)).isoformat()

    signups_today = _count_events(supabase, "user.registered", today_start)
    signups_7d = _count_events(supabase, "user.registered", since_7d)
    signups_30d = _count_events(supabase, "user.registered", since_30d)
    logins_today = _count_events(supabase, "user.logged_in", today_start)
    logins_7d = _count_events(supabase, "user.logged_in", since_7d)
    conversions_7d = _count_events(supabase, "referral.converted", since_7d)

    clicks_7d = 0
    try:
        res = (
            supabase.table("referral_clicks")
            .select("id", count="exact")
            .gte("clicked_at", since_7d)
            .execute()
        )
        clicks_7d = res.count or 0
    except Exception as exc:
        logger.error("referral_clicks count: %s", type(exc).__name__)

    conversion_rate = round(conversions_7d / clicks_7d, 4) if clicks_7d > 0 else 0.0

    # Breakdown diário — agrega por data em Python; simples e correto para ≤1k eventos/dia
    daily_counts: dict = defaultdict(int)
    try:
        res = (
            supabase.table("analytics_events")
            .select("occurred_at")
            .eq("event_type", "user.registered")
            .gte("occurred_at", since_30d)
            .execute()
        )
        for row in (res.data or []):
            daily_counts[row["occurred_at"][:10]] += 1
    except Exception as exc:
        logger.error("daily_signups query: %s", type(exc).__name__)

    daily_list = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).date().isoformat()
        daily_list.append({"date": day, "count": daily_counts.get(day, 0)})

    valid_registrations_approx = count_valid_registrations_approx(supabase)

    return {
        "signups_today": signups_today,
        "signups_last_7d": signups_7d,
        "signups_last_30d": signups_30d,
        "logins_today": logins_today,
        "logins_last_7d": logins_7d,
        "referral_clicks_last_7d": clicks_7d,
        "referral_conversions_last_7d": conversions_7d,
        "referral_conversion_rate": conversion_rate,
        "daily_signups_last_30d": daily_list,
        "valid_registrations_approx": valid_registrations_approx,
    }
