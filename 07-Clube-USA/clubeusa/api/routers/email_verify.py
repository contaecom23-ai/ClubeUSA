# ============================================================
#  routers/email_verify.py — Fase 0.1
#  Verificacao de email por link (token 24h, rate-limited 3/h)
# ============================================================

import os
from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member

router = APIRouter(prefix="/auth/email", tags=["email"])


@router.post("/request")
async def request_email_verification(member: dict = Depends(get_current_member)):
    """
    Solicita link de verificacao de email (rate-limit: 3 por hora).
    Requer autenticacao (JWT). Email deve estar cadastrado no perfil.
    """
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    result = (
        sb.table("members")
        .select("email_enc,email_hash,email_verified")
        .eq("id", member["sub"])
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404)

    m = result.data[0]

    if not m.get("email_enc"):
        raise HTTPException(
            status_code=400,
            detail="Nenhum email cadastrado. Atualize seu perfil primeiro."
        )

    if m.get("email_verified"):
        return {"ok": True, "already_verified": True, "message": "Email ja verificado."}

    from services.email_service import request_verification
    try:
        return request_verification(member["sub"], m["email_enc"])
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/verify")
async def verify_email(token: str = ""):
    """
    Verifica email via token recebido por email.
    Rota publica (sem auth): chamada pelo link no email.
    """
    if not token or len(token) > 64:
        raise HTTPException(status_code=400, detail="Token inválido ou ausente.")

    from services.email_service import verify_email_token
    try:
        return verify_email_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def email_verification_status(member: dict = Depends(get_current_member)):
    """Retorna se o email do membro esta verificado."""
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    result = (
        sb.table("members")
        .select("email_hash,email_verified")
        .eq("id", member["sub"])
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404)

    m = result.data[0]
    return {
        "has_email":     bool(m.get("email_hash")),
        "email_verified": bool(m.get("email_verified")),
    }
