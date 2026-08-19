# api/routers/valid_registration.py
# Fase 0.4: endpoint de status de cadastro valido
#
# GET /api/v1/members/me/valid-status
#   Requer: Authorization: Bearer <token>
#   Retorna: breakdown de por que o cadastro e ou nao valido.
#
# Nota: email_confirmed e is_disposable_email dependem das migrations
#   email_confirmation_migration.sql (PR #54) e valid_registration_migration.sql.

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client
from api.deps import get_current_member

router = APIRouter(prefix="/members", tags=["cadastro-valido"])


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


class ValidStatusResponse(BaseModel):
    is_valid: bool
    email_confirmed: bool
    has_real_action: bool
    is_disposable_email: bool
    blocking_reason: str | None


@router.get("/me/valid-status", response_model=ValidStatusResponse)
def get_valid_status(member: dict = Depends(get_current_member)):
    member_id = member.get("member_id") or member.get("id") or member.get("sub")
    if not member_id:
        raise HTTPException(status_code=401, detail="Token invalido.")

    sb = _sb()
    result = (
        sb.table("members")
        .select("email_confirmed,is_disposable_email,total_clicks,referral_count")
        .eq("id", member_id)
        .is_("deleted_at", "null")
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    data = result.data
    email_confirmed: bool = bool(data.get("email_confirmed", False))
    is_disposable: bool = bool(data.get("is_disposable_email", False))
    has_real_action: bool = (
        (data.get("total_clicks") or 0) >= 1
        or (data.get("referral_count") or 0) >= 1
    )

    blocking_reason = None
    if not email_confirmed:
        blocking_reason = "Email nao confirmado. Verifique sua caixa de entrada."
    elif is_disposable:
        blocking_reason = "Email descartavel detectado. Use um email permanente."
    elif not has_real_action:
        blocking_reason = "Realize ao menos uma acao (clique em oferta, indicacao, etc.)."

    return ValidStatusResponse(
        is_valid=email_confirmed and not is_disposable and has_real_action,
        email_confirmed=email_confirmed,
        has_real_action=has_real_action,
        is_disposable_email=is_disposable,
        blocking_reason=blocking_reason,
    )
