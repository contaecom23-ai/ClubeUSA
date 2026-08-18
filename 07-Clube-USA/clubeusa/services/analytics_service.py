# services/analytics_service.py — Fase 0.3: Analytics básico
#
# Computa métricas de funil, crescimento e engajamento a partir das tabelas
# existentes (members, referrals, clicks, audit_logs).
# Não requer nova tabela — apenas um índice (analytics_migration.sql).
#
# Escala: adequado para 1k–10k usuários. Acima disso, get_growth() deve
# migrar para VIEW materializada ou agregação diária via cron (evitar
# full table scan em membros).

import os
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter

log = logging.getLogger("analytics_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_funnel(days: int = 30) -> dict:
    """
    Funil de conversão: registros → logins → referrals confirmados → VIP.
    Lê de members, referrals, audit_logs e clicks via service_role (sem RLS).
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    cutoff_7d  = (now - timedelta(days=7)).isoformat()
    cutoff_30d = (now - timedelta(days=30)).isoformat()

    members = sb.table("members").select(
        "id,plan,created_at,referred_by"
    ).is_("deleted_at", "null").execute().data

    total_reg = len(members)
    reg_7d    = sum(1 for m in members if (m.get("created_at") or "") >= cutoff_7d)
    reg_30d   = sum(1 for m in members if (m.get("created_at") or "") >= cutoff_30d)
    vip_count = sum(1 for m in members if m.get("plan") == "vip")

    referrals = sb.table("referrals").select("status").execute().data
    ref_confirmed = sum(1 for r in referrals if r["status"] == "confirmed")
    ref_pending   = sum(1 for r in referrals if r["status"] == "pending")
    ref_rate      = round(ref_confirmed / total_reg, 4) if total_reg else 0.0

    logins_7d = sb.table("audit_logs").select(
        "id", count="exact"
    ).eq("action", "member.login").gte("created_at", cutoff_7d).execute()
    login_count_7d = logins_7d.count or 0

    clicks_7d = sb.table("clicks").select(
        "id", count="exact"
    ).gte("clicked_at", cutoff_7d).execute()
    click_count_7d = clicks_7d.count or 0

    return {
        "funnel": {
            "registrations_total":           total_reg,
            "registrations_last_7d":         reg_7d,
            "registrations_last_30d":        reg_30d,
            "logins_last_7d":                login_count_7d,
            "referral_conversions_total":    ref_confirmed,
            "referral_conversions_pending":  ref_pending,
            "referral_conversion_rate":      ref_rate,
            "vip_subscribers":               vip_count,
            "deal_clicks_last_7d":           click_count_7d,
        }
    }


def get_growth(days: int = 30) -> list:
    """
    Registros diários dos últimos N dias.
    Retorna [{date: str, registrations: int}, ...] em ordem cronológica.
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).isoformat()

    members = sb.table("members").select("created_at").gte(
        "created_at", cutoff
    ).is_("deleted_at", "null").execute().data

    counts: dict = {}
    for m in members:
        day = (m.get("created_at") or "")[:10]
        if day:
            counts[day] = counts.get(day, 0) + 1

    return [
        {
            "date":          (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
            "registrations": counts.get(
                (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"), 0
            ),
        }
        for i in range(days)
    ]


def get_top_referrers(limit: int = 10) -> list:
    """Top referrers por contagem de indicações. Nome truncado para não expor PII."""
    sb = _supabase()
    rows = sb.table("members").select(
        "name_enc,referral_code,referral_count"
    ).gt("referral_count", 0).order("referral_count", desc=True).limit(limit).execute().data

    result = []
    for m in rows:
        try:
            from utils.security import decrypt
            name = decrypt(m["name_enc"]) if m.get("name_enc") else "—"
            name = (name[:27] + "...") if len(name) > 30 else name
        except Exception:
            name = "—"
        result.append({
            "referral_code":  m["referral_code"],
            "referral_count": m["referral_count"],
            "name":           name,
        })
    return result


def get_engagement(days: int = 7) -> dict:
    """
    Engajamento com deals: total de cliques + top 5 categorias.
    Nota: join manual (cliques → deals) limita-se a 100 deal IDs únicos;
    adequado para 1k usuários. Acima de 10k, mover para query nativa com join.
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).isoformat()

    clicks = sb.table("clicks").select("deal_id").gte("clicked_at", cutoff).execute().data
    if not clicks:
        return {"clicks_last_7d": 0, "top_categories": []}

    deal_ids = list({c["deal_id"] for c in clicks})
    deals = sb.table("deals").select("id,category").in_(
        "id", deal_ids[:100]
    ).execute().data

    cat_map = {d["id"]: d.get("category") or "other" for d in deals}
    cat_counts = Counter(
        cat_map.get(c["deal_id"], "other") for c in clicks if c["deal_id"] in cat_map
    )
    top_cats = [
        {"category": cat, "clicks": cnt}
        for cat, cnt in cat_counts.most_common(5)
    ]

    return {
        "clicks_last_7d": len(clicks),
        "top_categories": top_cats,
    }
