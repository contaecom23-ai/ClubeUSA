# ============================================================
#  routers/analytics.py — Clube USA
#  Analytics de cadastros: funil de conversao e crescimento diario
# ============================================================

import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from deps import require_admin

router = APIRouter(prefix="/admin/analytics", tags=["admin"])
log = logging.getLogger("analytics")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.get("/funnel")
async def analytics_funnel(_=Depends(require_admin)):
    """
    Funil de conversao:
    total_registered → com_email → email_confirmed → active_users
    """
    sb = _supabase()

    total_res    = sb.table("members").select("id", count="exact").is_("deleted_at", "null").execute()
    email_res    = sb.table("members").select("id", count="exact").not_.is_("email_enc", "null").is_("deleted_at", "null").execute()
    confirmed_res = sb.table("members").select("id", count="exact").eq("email_confirmed", True).is_("deleted_at", "null").execute()
    active_res   = sb.table("members").select("id", count="exact").eq("status", "active").is_("deleted_at", "null").execute()

    total      = total_res.count or 0
    with_email = email_res.count or 0
    confirmed  = confirmed_res.count or 0
    active     = active_res.count or 0

    # Cadastro valido = email confirmado + status ativo
    valid_res = (
        sb.table("members")
        .select("id", count="exact")
        .eq("email_confirmed", True)
        .eq("status", "active")
        .is_("deleted_at", "null")
        .execute()
    )
    valid = valid_res.count or 0

    def pct(num, denom):
        return round(num / denom * 100, 1) if denom else 0

    return {
        "total_registered":        total,
        "with_email":              with_email,
        "pct_with_email":          pct(with_email, total),
        "email_confirmed":         confirmed,
        "pct_email_confirmed":     pct(confirmed, with_email),
        "active_users":            active,
        "valid_registrations":     valid,
        "pct_valid_of_total":      pct(valid, total),
    }


@router.get("/growth")
async def analytics_growth(days: int = 30, _=Depends(require_admin)):
    """
    Crescimento diario de cadastros nos ultimos N dias (default 30).
    Tenta RPC get_daily_registrations; usa fallback Python se nao existir.
    """
    days = min(max(days, 1), 365)
    sb   = _supabase()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Tenta RPC (mais eficiente)
    try:
        res = sb.rpc("get_daily_registrations", {"p_since": since}).execute()
        if res.data is not None:
            return {"growth": res.data, "period_days": days, "source": "rpc"}
    except Exception as e:
        log.info(f"RPC get_daily_registrations indisponivel, usando fallback: {e}")

    # Fallback: agrega em Python
    all_res = (
        sb.table("members")
        .select("created_at")
        .gte("created_at", since)
        .is_("deleted_at", "null")
        .execute()
    )

    from collections import defaultdict
    daily: dict = defaultdict(int)
    for row in (all_res.data or []):
        date_str = row["created_at"][:10]  # "YYYY-MM-DD"
        daily[date_str] += 1

    growth = [{"date": d, "count": c} for d, c in sorted(daily.items())]
    return {"growth": growth, "period_days": days, "source": "fallback"}
