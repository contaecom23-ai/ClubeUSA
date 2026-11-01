# ============================================================
#  api/routers/auth_email.py — Clube USA
#  Fase 0.1: endpoints de confirmação de email
#
#  POST /auth/email/verify-request  — envia email de confirmação (auth)
#  POST /auth/email/verify           — confirma token (público)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from deps import get_current_member

router = APIRouter(prefix="/auth/email", tags=["auth-email"])


class EmailVerifyRequest(BaseModel):
    email: str


class EmailConfirmRequest(BaseModel):
    token: str


@router.post("/verify-request")
async def request_email_verification(
    body: EmailVerifyRequest,
    member: dict = Depends(get_current_member),
):
    """
    Envia (ou loga em dev) um link de confirmação de email.
    Requer autenticação — o membro informa o email a confirmar.
    Rate-limit herdado do middleware global (5 req/min por IP para /auth*).
    """
    from services.email_service import request_email_verification as svc
    try:
        return svc(member["sub"], body.email)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger("auth_email").error(f"Erro ao enviar confirmação: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar email. Tente novamente.")


@router.post("/verify")
async def confirm_email(body: EmailConfirmRequest):
    """
    Confirma token de verificação de email.
    Endpoint público (sem autenticação) — o link enviado por email aponta aqui.
    Token é single-use com TTL de 24h.
    """
    from services.email_service import confirm_email_token
    try:
        return confirm_email_token(body.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
