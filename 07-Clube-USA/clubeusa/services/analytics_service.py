"""
analytics_service.py — Fase 0.3

Tracking server-side de eventos. Nunca bloqueia o fluxo principal
(exceções são silenciadas — analytics failure ≠ request failure).
"""

import logging
import os
from typing import Optional

log = logging.getLogger("analytics")


def track(
    event_type: str,
    member_id: Optional[str] = None,
    properties: Optional[dict] = None,
    ip_hash: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Registra um evento no banco. Nunca lança exceção."""
    try:
        from supabase import create_client
        sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
        sb.table("analytics_events").insert({
            "member_id":  member_id,
            "event_type": event_type,
            "properties": properties or {},
            "ip_hash":    ip_hash,
            "session_id": session_id,
        }).execute()
    except Exception as e:
        log.debug(f"analytics.track silenced: {e}")


def get_admin_stats() -> dict:
    """Agrega métricas básicas para o painel admin."""
    from supabase import create_client
    from datetime import datetime, timedelta, timezone

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    now = datetime.now(timezone.utc)
    d7  = (now - timedelta(days=7)).isoformat()
    d30 = (now - timedelta(days=30)).isoformat()

    total = sb.table("members").select("id", count="exact").execute()
    new7  = sb.table("members").select("id", count="exact").gte("created_at", d7).execute()
    new30 = sb.table("members").select("id", count="exact").gte("created_at", d30).execute()

    # Membros com ao menos 1 evento nos últimos 7 dias
    active7_res = sb.rpc("count_active_members_7d", {}).execute()
    active7 = active7_res.data if active7_res.data is not None else 0

    # Contagem por tipo de evento nos últimos 30 dias
    events_res = sb.table("analytics_events") \
        .select("event_type") \
        .gte("created_at", d30) \
        .execute()
    event_counts: dict = {}
    for row in (events_res.data or []):
        et = row["event_type"]
        event_counts[et] = event_counts.get(et, 0) + 1

    top_events = sorted(
        [{"event": k, "count": v} for k, v in event_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    # Novos membros por dia nos últimos 14 dias
    daily_res = sb.rpc("members_per_day_14d", {}).execute()

    return {
        "total_members":      total.count or 0,
        "new_members_7d":     new7.count or 0,
        "new_members_30d":    new30.count or 0,
        "active_members_7d":  active7,
        "top_events_30d":     top_events,
        "new_members_by_day": daily_res.data or [],
    }


def get_validation_status(member_id: str) -> dict:
    """
    Retorna o status de 'cadastro válido' de um membro (Fase 0.4).
    Critério: email confirmado (se fornecido) + ≥1 ação real.
    Ação real = clique em deal OU produto rastreado.
    """
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Dados do membro
    res = sb.table("members").select(
        "email_hash, email_confirmed, created_at"
    ).eq("id", member_id).execute()

    if not res.data:
        return {"is_valid": False, "reason": "Membro não encontrado."}

    member = res.data[0]
    has_email     = bool(member.get("email_hash"))
    email_confirmed = bool(member.get("email_confirmed", False))

    # Contagem de ações reais
    clicks_res = sb.table("clicks").select("id", count="exact") \
        .eq("member_id", member_id).execute()
    tracked_res = sb.table("analytics_events").select("id", count="exact") \
        .eq("member_id", member_id) \
        .in_("event_type", ["product.tracked", "deal.clicked"]).execute()

    actions_count = (clicks_res.count or 0) + (tracked_res.count or 0)
    has_real_action = actions_count >= 1

    # Critério de cadastro válido
    if has_email and not email_confirmed:
        reason = "Email ainda não confirmado."
        is_valid = False
    elif not has_real_action:
        reason = "Nenhuma ação real registrada ainda (clique em deal ou produto rastreado)."
        is_valid = False
    else:
        reason = "Cadastro válido."
        is_valid = True

    return {
        "email_confirmed":  email_confirmed,
        "has_email":        has_email,
        "has_real_action":  has_real_action,
        "actions_count":    actions_count,
        "is_valid":         is_valid,
        "reason":           reason,
    }
