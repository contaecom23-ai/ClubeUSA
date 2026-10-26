# ============================================================
#  services/analytics_service.py — Clube USA
#  Fase 0.3: Analytics básico
#
#  Computa métricas de funil, crescimento e engajamento a partir das
#  tabelas existentes (members, referrals, clicks, audit_logs, events).
#
#  Escala: adequado para 1k–10k usuários. Acima disso, get_growth() deve
#  migrar para VIEW materializada ou agregação diária via cron.
# ============================================================
import os
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

log = logging.getLogger("analytics_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _pct(num: int, den: int) -> float:
    return round(num / den * 100, 1) if den else 0.0


# ============================================================
#  LOG DE EVENTOS
# ============================================================

def log_event(member_id: str, event_type: str, metadata: dict | None = None) -> None:
    """Registra evento na tabela events. Falha silenciosa para não bloquear fluxo principal."""
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
#  FUNIL — conversão completa com logins e referrals
# ============================================================

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
        "id,plan,status,email_enc,email_confirmed,total_clicks,referral_count,referred_by,created_at"
    ).is_("deleted_at", "null").execute().data

    total_reg  = len(members)
    reg_7d     = sum(1 for m in members if (m.get("created_at") or "") >= cutoff_7d)
    reg_30d    = sum(1 for m in members if (m.get("created_at") or "") >= cutoff_30d)
    vip_count  = sum(1 for m in members if m.get("plan") == "vip")
    with_email = sum(1 for m in members if m.get("email_enc"))
    confirmed  = sum(1 for m in members if m.get("email_confirmed"))
    with_click = sum(1 for m in members if (m.get("total_clicks") or 0) > 0)

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
            "registrations_total":          total_reg,
            "registrations_last_7d":        reg_7d,
            "registrations_last_30d":       reg_30d,
            "logins_last_7d":               login_count_7d,
            "email_set":                    with_email,
            "email_confirmed":              confirmed,
            "email_confirmed_pct":          _pct(confirmed, with_email),
            "made_first_click":             with_click,
            "engagement_pct":               _pct(with_click, total_reg),
            "referral_conversions_total":   ref_confirmed,
            "referral_conversions_pending": ref_pending,
            "referral_conversion_rate":     ref_rate,
            "vip_subscribers":              vip_count,
            "deal_clicks_last_7d":          click_count_7d,
        }
    }


# ============================================================
#  CRESCIMENTO — registros diários
# ============================================================

def get_growth(days: int = 30) -> list:
    """
    Registros diários dos últimos N dias.
    Retorna [{date, registrations}, ...] em ordem cronológica — inclui dias com zero.
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).isoformat()

    members = sb.table("members").select("created_at").gte(
        "created_at", cutoff
    ).is_("deleted_at", "null").execute().data

    counts: dict = defaultdict(int)
    for m in members:
        day = (m.get("created_at") or "")[:10]
        if day:
            counts[day] += 1

    return [
        {
            "date":          (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
            "registrations": counts.get(
                (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"), 0
            ),
        }
        for i in range(days)
    ]


# ============================================================
#  TOP REFERRERS — melhores indicadores
# ============================================================

def get_top_referrers(limit: int = 10) -> list:
    """Top referrers por contagem de indicações. Nome truncado para não expor PII completo."""
    sb = _supabase()
    rows = sb.table("members").select(
        "name_enc,referral_code,referral_count"
    ).gt("referral_count", 0).order("referral_count", desc=True).limit(limit).execute().data

    result = []
    for m in rows:
        name = "—"
        if m.get("name_enc"):
            try:
                from utils.security import decrypt
                raw = decrypt(m["name_enc"])
                name = (raw[:27] + "...") if len(raw) > 30 else raw
            except Exception:
                pass
        result.append({
            "referral_code":  m["referral_code"],
            "referral_count": m["referral_count"],
            "name":           name,
        })
    return result


# ============================================================
#  ENGAJAMENTO — cliques e categorias
# ============================================================

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


# ============================================================
#  REFERRALS — stats agregados do programa de indicação
# ============================================================

def get_referral_stats() -> dict:
    """Performance agregada do programa de indicação."""
    sb = _supabase()

    referrals = sb.table("referrals").select("referrer_id,status").execute().data or []
    total_referrals = len(referrals)
    confirmed = sum(1 for r in referrals if r.get("status") == "confirmed")
    unique_referrers = len({r["referrer_id"] for r in referrals})

    total_members_row = sb.table("members").select("id", count="exact").execute()
    total_members = total_members_row.count or 0

    counts = Counter(r["referrer_id"] for r in referrals)
    top_referrers = [
        {"rank": i + 1, "referrals_count": cnt}
        for i, (_, cnt) in enumerate(counts.most_common(5))
    ]

    return {
        "total_referrals":       total_referrals,
        "confirmed_referrals":   confirmed,
        "unique_referrers":      unique_referrers,
        "referrer_adoption_pct": _pct(unique_referrers, total_members),
        "confirmation_rate_pct": _pct(confirmed, total_referrals),
        "top_referrers":         top_referrers,
    }


# ============================================================
#  GEOGRAFICO — distribuição por estado
# ============================================================

def get_geographic_breakdown() -> dict:
    """Top 10 estados por número de membros."""
    sb = _supabase()
    rows = sb.table("members").select("state").execute().data or []

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
#  OVERVIEW — snapshot completo para o dashboard
# ============================================================

def get_overview() -> dict:
    """Snapshot completo: funil + crescimento 30d + top referrers + engajamento."""
    now = datetime.now(timezone.utc)
    return {
        "as_of":        now.isoformat(),
        "funnel":       get_funnel()["funnel"],
        "growth_30d":   get_growth(days=30),
        "top_referrers": get_top_referrers(limit=10),
        "engagement":   get_engagement(days=7),
        "geographic":   get_geographic_breakdown(),
    }
