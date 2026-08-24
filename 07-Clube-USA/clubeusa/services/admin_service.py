import os
import logging
from datetime import datetime, date, timedelta, timezone
from collections import Counter, defaultdict

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


def get_analytics(days: int = 30) -> dict:
    """
    Série temporal de métricas chave para os últimos N dias.
    Consulta tabelas existentes — sem schema extra (ok até ~100k membros).
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()

    # ---- cadastros por dia ----
    members_raw = sb.table("members").select("created_at,referred_by,state,plan").execute().data

    reg_by_day: dict = defaultdict(int)
    ref_by_day: dict = defaultdict(int)
    total_with_referrer = 0
    state_counter: Counter = Counter()
    plan_counter: Counter = Counter()

    for m in members_raw:
        created = m.get("created_at", "")
        if created >= since:
            day = created[:10]
            reg_by_day[day] += 1
            if m.get("referred_by"):
                ref_by_day[day] += 1
        if m.get("referred_by"):
            total_with_referrer += 1
        if m.get("state"):
            state_counter[m["state"]] += 1
        plan_counter[m.get("plan", "free")] += 1

    total_members = len(members_raw)
    referral_rate = round(total_with_referrer / total_members * 100, 1) if total_members else 0.0

    # ---- logins por dia (via audit_logs) ----
    login_raw = (
        sb.table("audit_logs")
        .select("created_at")
        .eq("action", "member.login")
        .gte("created_at", since)
        .execute()
        .data
    )
    login_by_day: dict = defaultdict(int)
    for row in login_raw:
        day = (row.get("created_at") or "")[:10]
        if day:
            login_by_day[day] += 1

    # ---- referrals confirmados por dia ----
    refs_raw = (
        sb.table("referrals")
        .select("created_at")
        .gte("created_at", since)
        .execute()
        .data
    )
    referrals_by_day: dict = defaultdict(int)
    for row in refs_raw:
        day = (row.get("created_at") or "")[:10]
        if day:
            referrals_by_day[day] += 1

    # ---- preenche série completa de datas (sem lacunas) ----
    date_series = [
        (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days - 1, -1, -1)
    ]
    registrations_series = [
        {"date": d, "count": reg_by_day.get(d, 0)} for d in date_series
    ]
    logins_series = [
        {"date": d, "count": login_by_day.get(d, 0)} for d in date_series
    ]
    referrals_series = [
        {"date": d, "count": referrals_by_day.get(d, 0)} for d in date_series
    ]

    return {
        "period_days":         days,
        "total_members":       total_members,
        "referral_rate_pct":   referral_rate,
        "plan_distribution":   dict(plan_counter),
        "top_states":          state_counter.most_common(5),
        "registrations_by_day": registrations_series,
        "logins_by_day":        logins_series,
        "referrals_by_day":     referrals_series,
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
