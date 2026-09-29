import os
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter

log = logging.getLogger("admin_service")

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

    members = sb.table("members").select(
        "plan,status,created_at,email_enc,email_confirmed_at"
    ).execute().data
    total       = len(members)
    active      = sum(1 for m in members if m["status"] == "active")
    vip         = sum(1 for m in members if m["plan"] == "vip")
    new_week    = sum(1 for m in members if m.get("created_at", "") >= week_ago)
    with_email  = sum(1 for m in members if m.get("email_enc"))
    confirmed   = sum(1 for m in members if m.get("email_confirmed_at"))
    confirm_rate = round(confirmed / with_email * 100, 1) if with_email > 0 else 0.0

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
        "members": {
            "total": total, "active": active, "vip": vip, "new_this_week": new_week,
            "email_confirmed": confirmed, "confirmation_rate": confirm_rate,
        },
        "deals":      {"pending": pending, "approved": approved, "sent_this_week": sent_week},
        "engagement": {"clicks_this_week": len(clicks_week), "top_category": top_cat},
        "alerts":     {"active": alerts_active, "triggered_this_week": alerts_week},
    }


# ============================================================
#  ANALYTICS — CRESCIMENTO E FUNIL
# ============================================================

def get_growth(days: int = 30) -> list:
    """
    Retorna contagem diária de cadastros dos últimos N dias.
    Resultado: [{"date": "YYYY-MM-DD", "count": N}, ...]
    """
    sb = _supabase()
    from_date = (datetime.now(timezone.utc).date() - timedelta(days=days - 1)).isoformat()
    rows = sb.table("members").select("created_at").gte("created_at", from_date).execute().data

    counts: dict = {}
    for r in rows:
        d = (r.get("created_at") or "")[:10]
        if d:
            counts[d] = counts.get(d, 0) + 1

    today = datetime.now(timezone.utc).date()
    result = []
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()
        result.append({"date": d, "count": counts.get(d, 0)})
    return result


def get_funnel() -> dict:
    """
    Funil de cadastro: registrado → email fornecido → confirmado → engajado.
    Retorna contagens absolutas e taxas de conversão.
    """
    sb = _supabase()
    members = sb.table("members").select(
        "email_enc,email_confirmed_at,total_clicks,referred_by"
    ).execute().data

    total         = len(members)
    with_email    = sum(1 for m in members if m.get("email_enc"))
    email_conf    = sum(1 for m in members if m.get("email_confirmed_at"))
    engaged       = sum(1 for m in members if (m.get("total_clicks") or 0) > 0)
    via_referral  = sum(1 for m in members if m.get("referred_by"))

    return {
        "registered":        total,
        "email_provided":    with_email,
        "email_confirmed":   email_conf,
        "engaged":           engaged,
        "via_referral":      via_referral,
        "confirmation_rate": round(email_conf  / with_email * 100, 1) if with_email  > 0 else 0.0,
        "engagement_rate":   round(engaged     / total      * 100, 1) if total       > 0 else 0.0,
        "referral_rate":     round(via_referral / total     * 100, 1) if total       > 0 else 0.0,
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
