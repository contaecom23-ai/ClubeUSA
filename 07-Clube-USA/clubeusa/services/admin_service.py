import os
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter

log = logging.getLogger("admin_service")

# "Cadastro válido" = phone verified via OTP (already enforced by auth flow)
# + status active + has performed at least one action (click, referral, or profile updated).
# Re-evaluated as product matures — see DECISOES.md #2026-10-16.
_VALID_SIGNUP_ACTIONS_MIN = 1

VALID_STATUSES = ("active", "inactive", "banned")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _decrypt(token: str) -> str:
    from utils.security import decrypt
    return decrypt(token)


# ============================================================
#  METRICAS
# ============================================================

def get_metrics() -> dict:
    sb = _supabase()
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    members = sb.table("members").select("plan,status,created_at").execute().data
    total       = len(members)
    active      = sum(1 for m in members if m["status"] == "active")
    vip         = sum(1 for m in members if m["plan"] == "vip")
    new_week    = sum(1 for m in members if m.get("created_at", "") >= week_ago)

    clicks_week = sb.table("clicks").select("id").gte("clicked_at", week_ago).execute().data

    deals = sb.table("deals").select("status,sent_at,category").execute().data
    pending       = sum(1 for d in deals if d["status"] == "pending")
    approved      = sum(1 for d in deals if d["status"] == "approved")
    sent_week     = sum(1 for d in deals if d["status"] == "sent" and d.get("sent_at", "") >= week_ago)

    alerts = sb.table("price_alerts").select("status,triggered_at").execute().data
    alerts_active   = sum(1 for a in alerts if a["status"] == "active")
    alerts_week     = sum(1 for a in alerts if a["status"] == "triggered" and (a.get("triggered_at") or "") >= week_ago)

    top_cat = ""
    if deals:
        cats = [d.get("category") for d in deals if d.get("category")]
        if cats:
            top_cat = Counter(cats).most_common(1)[0][0]

    return {
        "members":    {"total": total, "active": active, "vip": vip, "new_this_week": new_week},
        "deals":      {"pending": pending, "approved": approved, "sent_this_week": sent_week},
        "engagement": {"clicks_this_week": len(clicks_week), "top_category": top_cat},
        "alerts":     {"active": alerts_active, "triggered_this_week": alerts_week},
    }


# ============================================================
#  ANALYTICS (Fase 0.3)
# ============================================================

def get_analytics() -> dict:
    """
    Analytics básico para o painel do dono.
    Usa dados já existentes — sem serviço externo.

    "Cadastro válido" (Fase 0.4 protótipo) =
        status='active' AND (total_clicks >= 1 OR referral_count >= 1)
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_ago    = (now - timedelta(days=7)).isoformat()
    month_ago   = (now - timedelta(days=30)).isoformat()

    # ---- Membros ----
    members = sb.table("members").select(
        "plan,status,language,referral_count,total_clicks,created_at,referred_by"
    ).is_("deleted_at", "null").execute().data

    total_members     = len(members)
    active_members    = sum(1 for m in members if m["status"] == "active")
    vip_members       = sum(1 for m in members if m["plan"] == "vip")
    new_today         = sum(1 for m in members if (m.get("created_at") or "") >= today_start)
    new_week          = sum(1 for m in members if (m.get("created_at") or "") >= week_ago)
    new_month         = sum(1 for m in members if (m.get("created_at") or "") >= month_ago)
    by_language       = Counter(m["language"] for m in members)
    via_referral      = sum(1 for m in members if m.get("referred_by"))

    # Valid signups: active + at least one engagement action
    valid_signups = sum(
        1 for m in members
        if m["status"] == "active"
        and (m.get("total_clicks", 0) >= _VALID_SIGNUP_ACTIONS_MIN
             or m.get("referral_count", 0) >= 1)
    )
    valid_pct = round(valid_signups / total_members * 100, 1) if total_members else 0

    # ---- Referrals ----
    referrals = sb.table("referrals").select(
        "referrer_id,status,created_at"
    ).execute().data

    total_referrals = len(referrals)
    referrals_week  = sum(1 for r in referrals if (r.get("created_at") or "") >= week_ago)

    # Top 5 referrers (anonymized: only member_id + count)
    ref_counter = Counter(r["referrer_id"] for r in referrals if r.get("referrer_id"))
    top_referrers = [{"member_id": mid, "count": cnt} for mid, cnt in ref_counter.most_common(5)]

    # ---- Clicks ----
    clicks_week = sb.table("clicks").select("id").gte("clicked_at", week_ago).execute().data
    clicks_month = sb.table("clicks").select("id").gte("clicked_at", month_ago).execute().data

    return {
        "generated_at": now.isoformat(),
        "members": {
            "total":          total_members,
            "active":         active_members,
            "vip":            vip_members,
            "new_today":      new_today,
            "new_this_week":  new_week,
            "new_this_month": new_month,
            "by_language":    dict(by_language),
            "via_referral":   via_referral,
        },
        "valid_signups": {
            "count":   valid_signups,
            "percent": valid_pct,
            "definition": "status=active AND (clicks>=1 OR referrals>=1)",
        },
        "referrals": {
            "total":          total_referrals,
            "this_week":      referrals_week,
            "top_referrers":  top_referrers,
        },
        "engagement": {
            "clicks_this_week":  len(clicks_week),
            "clicks_this_month": len(clicks_month),
        },
    }


# ============================================================
#  MEMBROS
# ============================================================

def list_members(
    plan: str = None,
    status: str = None,
    q: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    sb = _supabase()
    query = sb.table("members").select(
        "id,phone_enc,name_enc,email_enc,plan,status,points,level,"
        "referral_count,total_clicks,created_at,group_id"
    ).order("created_at", desc=True)
    if plan:
        query = query.eq("plan", plan)
    if status:
        query = query.eq("status", status)
    query = query.range(offset, offset + limit - 1)
    rows = query.execute().data
    result = []
    for m in rows:
        name  = _decrypt(m["name_enc"])  if m.get("name_enc")  else ""
        phone = _decrypt(m["phone_enc"]) if m.get("phone_enc") else ""
        if q and q.lower() not in name.lower() and q not in phone:
            continue
        result.append({**m, "name": name, "phone": phone})
    return result


def get_member(member_id: str) -> dict:
    sb = _supabase()
    rows = sb.table("members").select("*").eq("id", member_id).limit(1).execute().data
    if not rows:
        return {}
    row = rows[0]
    name  = _decrypt(row["name_enc"])  if row.get("name_enc")  else ""
    phone = _decrypt(row["phone_enc"]) if row.get("phone_enc") else ""
    email = _decrypt(row["email_enc"]) if row.get("email_enc") else ""
    return {**row, "name": name, "phone": phone, "email": email}


def set_member_status(member_id: str, status: str) -> bool:
    if status not in VALID_STATUSES:
        raise ValueError(f"Status inválido. Use: {', '.join(VALID_STATUSES)}")
    sb = _supabase()
    result = sb.table("members").update({"status": status}).eq("id", member_id).execute()
    return len(result.data) > 0


# ============================================================
#  DEALS
# ============================================================

def list_deals(status: str = None, limit: int = 200) -> list:
    sb = _supabase()
    query = sb.table("deals").select("*")
    if status:
        query = query.eq("status", status)
    return query.order("score", desc=True).limit(limit).execute().data


def approve_deal(deal_id: str) -> bool:
    sb = _supabase()
    result = sb.table("deals").update({"status": "approved"}).eq("id", deal_id).execute()
    return len(result.data) > 0


def reject_deal(deal_id: str) -> bool:
    sb = _supabase()
    result = sb.table("deals").update({"status": "rejected"}).eq("id", deal_id).execute()
    return len(result.data) > 0


# ============================================================
#  ALERTAS
# ============================================================

def list_admin_alerts() -> list:
    sb = _supabase()
    return (
        sb.table("price_alerts")
        .select("id,member_id,asin,product_title,target_type,target_value,status,created_at,triggered_at")
        .eq("status", "active")
        .order("created_at", desc=True)
        .execute()
        .data
    )
