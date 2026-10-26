# ============================================================
#  services/analytics_service.py — Clube USA
#  Analytics basico: crescimento, funil, engajamento, referrals
#  Fase 0.3
# ============================================================

import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

log = logging.getLogger("analytics_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _date_key(iso_str: str) -> str:
    """Extrai YYYY-MM-DD de uma string ISO 8601."""
    if not iso_str:
        return ""
    return iso_str[:10]


# ============================================================
#  CRESCIMENTO — novos membros por dia
# ============================================================

def get_growth(days: int = 30) -> dict:
    """
    Retorna series diaria de novos cadastros e total acumulado
    nos ultimos N dias (max 90).
    """
    days = max(1, min(days, 90))
    sb = _supabase()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows = sb.table("members").select("created_at").gte("created_at", since).execute().data or []

    daily: dict = defaultdict(int)
    for r in rows:
        key = _date_key(r.get("created_at", ""))
        if key:
            daily[key] += 1

    # Preenche dias sem cadastro com zero para series continua
    series = []
    base = datetime.now(timezone.utc).date()
    cumulative = 0
    for i in range(days - 1, -1, -1):
        d = (base - timedelta(days=i)).isoformat()
        count = daily.get(d, 0)
        cumulative += count
        series.append({"date": d, "new_members": count, "cumulative": cumulative})

    total_in_period = sum(daily.values())
    return {
        "period_days": days,
        "total_in_period": total_in_period,
        "series": series,
    }


# ============================================================
#  FUNIL — taxa de conversao em cada etapa
# ============================================================

def get_funnel() -> dict:
    """
    Funil de conversao:
      cadastrados → email fornecido → email confirmado → ≥1 clique
    """
    sb = _supabase()

    members = sb.table("members").select(
        "id,email_enc,email_confirmed,status"
    ).execute().data or []

    total = len(members)
    active = sum(1 for m in members if m.get("status") == "active")
    with_email = sum(1 for m in members if m.get("email_enc"))
    email_confirmed = sum(1 for m in members if m.get("email_confirmed"))

    # Membros com pelo menos 1 clique
    clicks_raw = sb.table("clicks").select("member_id").execute().data or []
    members_with_clicks = len({r["member_id"] for r in clicks_raw})

    def pct(part: int, whole: int) -> float:
        return round(part / whole * 100, 1) if whole else 0.0

    return {
        "total_registered": total,
        "active": active,
        "email_provided": with_email,
        "email_confirmed": email_confirmed,
        "members_with_clicks": members_with_clicks,
        "rates": {
            "email_provided_pct":   pct(with_email, total),
            "email_confirmed_pct":  pct(email_confirmed, with_email),
            "clicked_pct":          pct(members_with_clicks, total),
            "active_pct":           pct(active, total),
        },
    }


# ============================================================
#  ENGAJAMENTO — cliques por dia
# ============================================================

def get_engagement(days: int = 30) -> dict:
    """
    Retorna serie diaria de cliques e top 5 categorias de deals
    nos ultimos N dias (max 90).
    """
    days = max(1, min(days, 90))
    sb = _supabase()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    clicks = sb.table("clicks").select("clicked_at,deal_id").gte("clicked_at", since).execute().data or []

    daily_clicks: dict = defaultdict(int)
    for c in clicks:
        key = _date_key(c.get("clicked_at", ""))
        if key:
            daily_clicks[key] += 1

    series = []
    base = datetime.now(timezone.utc).date()
    for i in range(days - 1, -1, -1):
        d = (base - timedelta(days=i)).isoformat()
        series.append({"date": d, "clicks": daily_clicks.get(d, 0)})

    # Top categorias via deals
    deal_ids = list({c["deal_id"] for c in clicks if c.get("deal_id")})
    top_categories: list = []
    if deal_ids:
        deals_raw = sb.table("deals").select("id,category").in_("id", deal_ids[:200]).execute().data or []
        cat_map = {d["id"]: d.get("category", "unknown") for d in deals_raw}
        cat_counts: dict = defaultdict(int)
        for c in clicks:
            cat = cat_map.get(c.get("deal_id", ""), "unknown")
            cat_counts[cat] += 1
        top_categories = [
            {"category": cat, "clicks": cnt}
            for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1])[:5]
        ]

    return {
        "period_days": days,
        "total_clicks": len(clicks),
        "series": series,
        "top_categories": top_categories,
    }


# ============================================================
#  REFERRALS — performance do programa de indicacao
# ============================================================

def get_referral_stats() -> dict:
    """Performance do programa de indicacao."""
    sb = _supabase()

    referrals = sb.table("referrals").select("referrer_id,status").execute().data or []
    total_referrals = len(referrals)
    confirmed = sum(1 for r in referrals if r.get("status") == "confirmed")
    unique_referrers = len({r["referrer_id"] for r in referrals})

    # Total de membros para calcular taxa de adocao (% que indicou alguem)
    total_members_row = sb.table("members").select("id", count="exact").execute()
    total_members = total_members_row.count or 0

    # Top 5 indicadores (anonimizado — apenas contagem)
    from collections import Counter
    counts = Counter(r["referrer_id"] for r in referrals)
    top_referrers = [
        {"rank": i + 1, "referrals_count": cnt}
        for i, (_, cnt) in enumerate(counts.most_common(5))
    ]

    def pct(part: int, whole: int) -> float:
        return round(part / whole * 100, 1) if whole else 0.0

    return {
        "total_referrals": total_referrals,
        "confirmed_referrals": confirmed,
        "unique_referrers": unique_referrers,
        "referrer_adoption_pct": pct(unique_referrers, total_members),
        "confirmation_rate_pct": pct(confirmed, total_referrals),
        "top_referrers": top_referrers,
    }


# ============================================================
#  GEOGRAFICO — distribuicao por estado
# ============================================================

def get_geographic_breakdown() -> dict:
    """Top 10 estados por numero de membros."""
    sb = _supabase()
    rows = sb.table("members").select("state").execute().data or []

    from collections import Counter
    counts = Counter(r.get("state") or "unknown" for r in rows)
    top = [
        {"state": state, "members": cnt}
        for state, cnt in counts.most_common(10)
    ]
    return {
        "total_members": len(rows),
        "top_states": top,
    }


# ============================================================
#  OVERVIEW — resumo unificado para o dashboard
# ============================================================

def get_overview() -> dict:
    """
    Snapshot completo: crescimento (7d), funil, engajamento (7d),
    referrals e top estados. Usado pelo dashboard admin.
    """
    growth7   = get_growth(7)
    funnel    = get_funnel()
    engage7   = get_engagement(7)
    referrals = get_referral_stats()
    geo       = get_geographic_breakdown()

    return {
        "growth_7d":   growth7,
        "funnel":      funnel,
        "engagement_7d": engage7,
        "referrals":   referrals,
        "geographic":  geo,
    }
