# ============================================================
#  api/routers/valid_registration.py — Clube USA
#  Fase 0.4: cadastro válido + anti-fraude (monitoramento)
# ============================================================

import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member, require_admin

router = APIRouter(tags=["valid-registration"])


@router.get("/member/valid-status")
async def get_valid_status(member: dict = Depends(get_current_member)):
    """
    Retorna se este membro tem um 'cadastro válido' (Fase 0.4).
    Definição: telefone verificado via OTP + ao menos 1 clique registrado.
    Usado pelo programa de influenciadores para contar indicações válidas.
    """
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    result = (
        sb.table("members")
        .select("total_clicks,referral_count,email_enc,created_at")
        .eq("id", member["sub"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")

    m = result.data[0]
    is_valid = m["total_clicks"] >= 1

    return {
        "is_valid_registration": is_valid,
        "total_clicks":          m["total_clicks"],
        "referral_count":        m["referral_count"],
        "has_email":             bool(m.get("email_enc")),
        "validation_criteria":   "phone_verified=true AND total_clicks>=1",
    }


@router.get("/admin/valid-registrations")
async def admin_valid_registrations(_: dict = Depends(require_admin)):
    """
    Relatório de cadastros válidos vs. total — fraud monitoring.
    'cadastro válido' = phone_verified + total_clicks >= 1.
    """
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    total_res = sb.table("members").select("id", count="exact").execute()
    valid_res  = (
        sb.table("members")
        .select("id", count="exact")
        .gt("total_clicks", 0)
        .execute()
    )

    total = total_res.count or 0
    valid = valid_res.count or 0

    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_res = (
        sb.table("members")
        .select("id", count="exact")
        .gte("created_at", cutoff_24h)
        .execute()
    )
    recent_valid_res = (
        sb.table("members")
        .select("id", count="exact")
        .gte("created_at", cutoff_24h)
        .gt("total_clicks", 0)
        .execute()
    )

    recent       = recent_res.count or 0
    recent_valid = recent_valid_res.count or 0
    recent_ghost  = recent - recent_valid

    return {
        "total_registrations":    total,
        "valid_registrations":    valid,
        "invalid_registrations":  total - valid,
        "validation_rate_pct":    round(valid / max(total, 1) * 100, 1),
        "last_24h_registrations": recent,
        "last_24h_valid":         recent_valid,
        "last_24h_ghost":         recent_ghost,
        "fraud_alert":            recent_ghost > 10,
        "criteria":               "phone_verified=true AND total_clicks>=1",
    }
