# services/analytics_service.py — Fase 0.3: metricas de funil e crescimento
import os
from datetime import datetime, timedelta, timezone


def _sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_funnel() -> dict:
    """
    Funil de conversao:
      visitas (clicks tabela) → cadastros (members) → vip (members com plan=vip)
    """
    sb = _sb()
    
    total_members = sb.table("members").select("id", count="exact").execute()
    vip_members   = sb.table("members").select("id", count="exact").eq("plan", "vip").execute()
    total_clicks  = sb.table("clicks").select("id", count="exact").execute()
    active_members = sb.table("members").select("id", count="exact").eq("status", "active").execute()

    members_count = total_members.count or 0
    vip_count     = vip_members.count or 0
    clicks_count  = total_clicks.count or 0
    active_count  = active_members.count or 0

    return {
        "total_members":   members_count,
        "active_members":  active_count,
        "vip_members":     vip_count,
        "total_clicks":    clicks_count,
        "vip_conversion":  round(vip_count / members_count * 100, 1) if members_count else 0,
        "engagement_rate": round(active_count / members_count * 100, 1) if members_count else 0,
    }


def get_growth(days: int = 30) -> list:
    """
    Novos membros por dia nos ultimos N dias.
    Retorna lista de {date, new_members}.
    """
    sb = _sb()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = sb.table("members").select(
        "created_at"
    ).gte("created_at", since).order("created_at").execute()

    # Agrega por dia
    counts: dict = {}
    for row in (result.data or []):
        day = row["created_at"][:10]  # YYYY-MM-DD
        counts[day] = counts.get(day, 0) + 1

    # Preenche dias sem cadastro com zero
    growth = []
    for i in range(days):
        day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        growth.append({"date": day, "new_members": counts.get(day, 0)})

    return growth


def get_top_referrers(limit: int = 10) -> list:
    """
    Top membros por numero de indicacoes confirmadas.
    """
    sb = _sb()
    result = sb.table("members").select(
        "id,referral_count,points,level"
    ).gt("referral_count", 0).order("referral_count", desc=True).limit(limit).execute()

    return [
        {
            "member_id":      row["id"],
            "referral_count": row["referral_count"],
            "points":         row["points"],
            "level":          row["level"],
        }
        for row in (result.data or [])
    ]


def get_engagement(days: int = 7) -> dict:
    """
    Metricas de engajamento dos ultimos N dias:
    - logins (auth.login em audit_logs)
    - cliques em deals
    """
    sb = _sb()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    logins = sb.table("audit_logs").select(
        "id", count="exact"
    ).eq("action", "auth.login").gte("created_at", since).execute()

    clicks = sb.table("clicks").select(
        "id", count="exact"
    ).gte("created_at", since).execute()

    referrals_period = sb.table("referrals").select(
        "id", count="exact"
    ).gte("created_at", since).execute()

    return {
        "period_days":      days,
        "logins":           logins.count or 0,
        "deal_clicks":      clicks.count or 0,
        "new_referrals":    referrals_period.count or 0,
    }
