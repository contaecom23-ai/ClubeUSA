# ============================================================
#  services/analytics_service.py — Clube USA
#  Fase 0.3: Analytics básico
#  - log_event(): registrar evento de membro na tabela events
#  - get_analytics(): funil de cadastro + crescimento diário
# ============================================================
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

log = logging.getLogger("analytics_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  LOG DE EVENTOS
# ============================================================

def log_event(member_id: str, event_type: str, metadata: dict | None = None) -> None:
    """Registra evento assíncrono na tabela events. Falha silenciosa para não bloquear fluxo."""
    try:
        sb = _supabase()
        sb.table("events").insert({
            "member_id":  member_id,
            "event_type": event_type,
            "metadata":   metadata or {},
        }).execute()
    except Exception as exc:
        log.warning("log_event falhou (não bloqueante): %s", exc)


# ============================================================
#  ANALYTICS
# ============================================================

def get_analytics() -> dict:
    sb = _supabase()
    now = datetime.now(timezone.utc)
    day30_ago = (now - timedelta(days=30)).isoformat()
    day7_ago  = (now - timedelta(days=7)).isoformat()

    # ── Membros (sem PII) ──────────────────────────────────────
    members = sb.table("members").select(
        "id,plan,status,email_enc,email_confirmed,total_clicks,"
        "referral_count,referred_by,created_at"
    ).is_("deleted_at", None).execute().data

    total = len(members)
    if total == 0:
        return _empty_analytics()

    with_email       = sum(1 for m in members if m.get("email_enc"))
    email_confirmed  = sum(1 for m in members if m.get("email_confirmed"))
    with_click       = sum(1 for m in members if (m.get("total_clicks") or 0) > 0)
    with_referral    = sum(1 for m in members if (m.get("referral_count") or 0) > 0)
    total_referrals  = sum(m.get("referral_count") or 0 for m in members)
    new_7d           = sum(1 for m in members if (m.get("created_at") or "") >= day7_ago)
    new_30d          = sum(1 for m in members if (m.get("created_at") or "") >= day30_ago)
    vip              = sum(1 for m in members if m.get("plan") == "vip")

    # ── Crescimento diário (últimos 30 dias) ──────────────────
    daily: dict[str, int] = defaultdict(int)
    for m in members:
        raw = m.get("created_at", "")
        if raw >= day30_ago:
            day_key = raw[:10]  # "YYYY-MM-DD"
            daily[day_key] += 1
    growth_30d = [{"date": d, "count": daily[d]} for d in sorted(daily)]

    # ── Funil ─────────────────────────────────────────────────
    funnel = {
        "registered":        total,
        "email_set":         with_email,
        "email_confirmed":   email_confirmed,
        "made_first_click":  with_click,
    }
    rates = {
        "email_set_pct":       _pct(with_email, total),
        "email_confirm_pct":   _pct(email_confirmed, with_email),
        "engagement_pct":      _pct(with_click, total),
    }

    # ── Referrals ─────────────────────────────────────────────
    referral_stats = {
        "members_who_referred":   with_referral,
        "total_referrals_made":   total_referrals,
        "avg_per_referrer":       round(total_referrals / with_referral, 2) if with_referral else 0,
        "members_via_referral":   sum(1 for m in members if m.get("referred_by")),
    }

    return {
        "as_of": now.isoformat(),
        "period": {"new_last_7d": new_7d, "new_last_30d": new_30d},
        "funnel": funnel,
        "funnel_rates": rates,
        "plan_distribution": {"free": total - vip, "vip": vip},
        "referrals": referral_stats,
        "growth_30d": growth_30d,
    }


def _pct(num: int, den: int) -> float:
    return round(num / den * 100, 1) if den else 0.0


def _empty_analytics() -> dict:
    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "period": {"new_last_7d": 0, "new_last_30d": 0},
        "funnel": {k: 0 for k in ("registered", "email_set", "email_confirmed", "made_first_click")},
        "funnel_rates": {k: 0.0 for k in ("email_set_pct", "email_confirm_pct", "engagement_pct")},
        "plan_distribution": {"free": 0, "vip": 0},
        "referrals": {"members_who_referred": 0, "total_referrals_made": 0, "avg_per_referrer": 0, "members_via_referral": 0},
        "growth_30d": [],
    }
