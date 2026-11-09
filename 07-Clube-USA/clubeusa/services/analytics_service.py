# ============================================================
#  services/analytics_service.py — Clube USA
#  Analytics básico — sem PII, dados agregados e anonimizados
#
#  Implementado em Python para MVP; quando members > 10k,
#  migrar as queries de série temporal para RPCs Postgres.
# ============================================================

import os
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

log = logging.getLogger("analytics_service")

_MIN_GROUP_SIZE = 3  # estados/categorias com menos que isso vão em "outros"


def _sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _today_utc() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _date_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# ============================================================
#  OVERVIEW — snapshot ampliado
# ============================================================

def get_overview() -> dict:
    """
    Métricas de alto nível para o painel admin.
    Estende o get_metrics() do admin_service com dados de funil.
    """
    sb = _sb()
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    members = sb.table("members").select(
        "plan,status,created_at,email_confirmed,total_clicks"
    ).execute().data or []

    total        = len(members)
    active       = sum(1 for m in members if m["status"] == "active")
    vip          = sum(1 for m in members if m["plan"] == "vip")
    new_7d       = sum(1 for m in members if (m.get("created_at") or "") >= week_ago)
    new_30d      = sum(1 for m in members if (m.get("created_at") or "") >= month_ago)
    with_email   = sum(1 for m in members if m.get("email_confirmed"))
    with_clicks  = sum(1 for m in members if (m.get("total_clicks") or 0) > 0)

    clicks_7d = sb.table("clicks").select("id").gte("clicked_at", week_ago).execute().data or []

    deals = sb.table("deals").select("status,sent_at,category").execute().data or []
    pending    = sum(1 for d in deals if d["status"] == "pending")
    approved   = sum(1 for d in deals if d["status"] == "approved")
    sent_7d    = sum(1 for d in deals if d["status"] == "sent" and (d.get("sent_at") or "") >= week_ago)

    referrals = sb.table("referrals").select("id,status").execute().data or []
    total_referrals = len(referrals)
    confirmed_ref   = sum(1 for r in referrals if r["status"] == "confirmed")

    top_cat = ""
    if deals:
        cats = [d.get("category") for d in deals if d.get("category")]
        if cats:
            top_cat = Counter(cats).most_common(1)[0][0]

    return {
        "members": {
            "total":       total,
            "active":      active,
            "vip":         vip,
            "new_7d":      new_7d,
            "new_30d":     new_30d,
        },
        "funnel": {
            "registered":     total,
            "email_confirmed": with_email,
            "has_activity":   with_clicks,
            "email_rate_pct": round(with_email / total * 100, 1) if total else 0,
            "activity_rate_pct": round(with_clicks / total * 100, 1) if total else 0,
        },
        "deals": {
            "pending":    pending,
            "approved":   approved,
            "sent_7d":    sent_7d,
            "top_category": top_cat,
        },
        "engagement": {
            "clicks_7d": len(clicks_7d),
        },
        "referrals": {
            "total":     total_referrals,
            "confirmed": confirmed_ref,
            "conversion_rate_pct": round(confirmed_ref / total_referrals * 100, 1) if total_referrals else 0,
        },
    }


# ============================================================
#  SÉRIE TEMPORAL — cadastros e cliques por dia
# ============================================================

def get_registrations_by_day(days: int = 30) -> list[dict]:
    """
    Retorna lista de {date, count} com cadastros por dia nos últimos `days` dias.
    """
    days = min(max(days, 1), 90)
    since = (_today_utc() - timedelta(days=days - 1)).isoformat()

    rows = (
        _sb().table("members")
        .select("created_at")
        .gte("created_at", since)
        .execute()
        .data or []
    )

    counter: dict[str, int] = defaultdict(int)
    for r in rows:
        d = (r.get("created_at") or "")[:10]
        if d:
            counter[d] += 1

    return _fill_time_series(counter, days)


def get_clicks_by_day(days: int = 30) -> list[dict]:
    """
    Retorna lista de {date, count} com cliques por dia nos últimos `days` dias.
    """
    days = min(max(days, 1), 90)
    since = (_today_utc() - timedelta(days=days - 1)).isoformat()

    rows = (
        _sb().table("clicks")
        .select("clicked_at")
        .gte("clicked_at", since)
        .execute()
        .data or []
    )

    counter: dict[str, int] = defaultdict(int)
    for r in rows:
        d = (r.get("clicked_at") or "")[:10]
        if d:
            counter[d] += 1

    return _fill_time_series(counter, days)


def _fill_time_series(counter: dict, days: int) -> list[dict]:
    """Preenche datas sem dados com count=0 para séries contínuas."""
    today = _today_utc()
    result = []
    for i in range(days - 1, -1, -1):
        d = _date_str(today - timedelta(days=i))
        result.append({"date": d, "count": counter.get(d, 0)})
    return result


# ============================================================
#  FUNIL DE CONVERSÃO
# ============================================================

def get_funnel() -> dict:
    """
    Funil completo:
      Cadastrados → Email confirmado → Primeira ação (clique) → VIP
    """
    sb = _sb()

    members = sb.table("members").select(
        "id,plan,email_confirmed,total_clicks,created_at"
    ).execute().data or []

    total        = len(members)
    confirmed    = sum(1 for m in members if m.get("email_confirmed"))
    has_action   = sum(1 for m in members if (m.get("total_clicks") or 0) > 0)
    is_vip       = sum(1 for m in members if m["plan"] == "vip")

    def _pct(num, denom):
        return round(num / denom * 100, 1) if denom else 0

    return {
        "steps": [
            {
                "step":  "Cadastrados",
                "count": total,
                "rate":  100.0,
            },
            {
                "step":  "Email confirmado",
                "count": confirmed,
                "rate":  _pct(confirmed, total),
            },
            {
                "step":  "Primeira ação (clique)",
                "count": has_action,
                "rate":  _pct(has_action, total),
            },
            {
                "step":  "VIP",
                "count": is_vip,
                "rate":  _pct(is_vip, total),
            },
        ]
    }


# ============================================================
#  TOP DEALS
# ============================================================

def get_top_deals(limit: int = 10) -> list[dict]:
    """
    Retorna os deals com mais cliques. Sem PII.
    """
    limit = min(max(limit, 1), 50)
    sb = _sb()

    clicks_rows = sb.table("clicks").select("deal_id").execute().data or []
    deal_clicks: Counter = Counter(r["deal_id"] for r in clicks_rows)

    if not deal_clicks:
        return []

    top_ids = [deal_id for deal_id, _ in deal_clicks.most_common(limit)]

    deals = (
        sb.table("deals")
        .select("id,title,category,price_now,discount_pct,score,status,sent_at")
        .in_("id", top_ids)
        .execute()
        .data or []
    )

    deals_by_id = {d["id"]: d for d in deals}
    result = []
    for deal_id, count in deal_clicks.most_common(limit):
        deal = deals_by_id.get(deal_id)
        if not deal:
            continue
        result.append({
            "deal_id":      deal["id"],
            "title":        deal["title"],
            "category":     deal.get("category"),
            "price_now":    float(deal.get("price_now") or 0),
            "discount_pct": deal.get("discount_pct"),
            "score":        float(deal.get("score") or 0),
            "status":       deal.get("status"),
            "clicks":       count,
        })
    return result


# ============================================================
#  DISTRIBUIÇÃO GEOGRÁFICA E POR CATEGORIA
# ============================================================

def get_members_by_state(limit: int = 20) -> list[dict]:
    """
    Contagem de membros por estado (top `limit`).
    Estados com < _MIN_GROUP_SIZE são agrupados em "outros".
    """
    limit = min(max(limit, 1), 50)
    rows = _sb().table("members").select("state").execute().data or []

    counter: Counter = Counter(
        (r.get("state") or "").strip() or "não informado"
        for r in rows
    )

    result = []
    others = 0
    for state, count in counter.most_common():
        if count < _MIN_GROUP_SIZE or len(result) >= limit:
            others += count
        else:
            result.append({"state": state, "count": count})

    if others:
        result.append({"state": "outros", "count": others})

    return result


def get_members_by_category() -> list[dict]:
    """
    Distribuição de membros por categoria de interesse.
    Um membro com várias categorias conta em cada uma.
    """
    rows = _sb().table("members").select("categories").execute().data or []

    counter: Counter = Counter()
    for r in rows:
        for cat in (r.get("categories") or []):
            if cat:
                counter[cat] += 1

    return [{"category": cat, "count": cnt} for cat, cnt in counter.most_common()]


# ============================================================
#  REFERRALS
# ============================================================

def get_referral_stats() -> dict:
    """
    Estatísticas do programa de indicações, sem identificar membros individualmente.
    """
    sb = _sb()

    referrals = sb.table("referrals").select(
        "referrer_id,status,created_at"
    ).execute().data or []

    total     = len(referrals)
    confirmed = sum(1 for r in referrals if r["status"] == "confirmed")
    pending   = sum(1 for r in referrals if r["status"] == "pending")

    # Distribuição: quantos indicadores têm N indicações
    per_referrer: Counter = Counter(r["referrer_id"] for r in referrals if r["status"] == "confirmed")
    distribution = Counter(per_referrer.values())

    return {
        "total":     total,
        "confirmed": confirmed,
        "pending":   pending,
        "conversion_rate_pct": round(confirmed / total * 100, 1) if total else 0,
        "unique_referrers": len(per_referrer),
        "referrers_with_3plus": sum(1 for c in per_referrer.values() if c >= 3),
        "distribution": {
            str(k): v for k, v in sorted(distribution.items())
        },
    }
