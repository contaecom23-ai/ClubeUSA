# api/routers/auth_email.py — Clube USA  Fase 0.1
# Endpoints de confirmacao de email.
#
# Rotas:
#   POST /auth/email/request-confirmation  — reenvia link (autenticado)
#   GET  /auth/email/confirm/{token}       — confirma email via link (publico)
#   GET  /auth/email/status                — status de confirmacao (autenticado)
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from supabase import create_client

from deps import get_current_member

log = logging.getLogger("auth_email")
router = APIRouter(prefix="/auth/email", tags=["auth"])


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.get("/status")
async def email_status(member: dict = Depends(get_current_member)):
    """Retorna se o email do membro autenticado esta confirmado."""
    sb = _sb()
    result = sb.table("members").select(
        "email_confirmed_at"
    ).eq("id", member["sub"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")
    m = result.data[0]
    return {
        "confirmed":          bool(m.get("email_confirmed_at")),
        "email_confirmed_at": m.get("email_confirmed_at"),
    }


@router.post("/request-confirmation")
async def request_email_confirmation(member: dict = Depends(get_current_member)):
    """Envia (ou reenvia) link de confirmacao para o email do membro autenticado."""
    from utils.security import decrypt
    sb = _sb()
    result = sb.table("members").select(
        "id,email_enc,name_enc,email_confirmed_at"
    ).eq("id", member["sub"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Membro nao encontrado.")

    m = result.data[0]

    if m.get("email_confirmed_at"):
        return {"message": "Email ja confirmado.", "confirmed": True}

    if not m.get("email_enc"):
        raise HTTPException(
            status_code=400,
            detail="Nenhum email cadastrado. Atualize seu perfil com um email.",
        )

    email = decrypt(m["email_enc"])
    name  = decrypt(m["name_enc"]) if m.get("name_enc") else None

    from services.email_service import send_confirmation_email
    sent = send_confirmation_email(member["sub"], email, name)

    if not sent:
        raise HTTPException(
            status_code=503,
            detail="Falha ao enviar email. Tente novamente em alguns minutos.",
        )

    return {"message": "Email de confirmacao enviado. Verifique sua caixa de entrada.", "confirmed": False}


@router.get("/confirm/{token}", include_in_schema=False)
async def confirm_email(token: str):
    """Confirma email via token do link. Redireciona para o painel."""
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")

    if not token or len(token) > 128:
        return HTMLResponse(_error_html(app_url, "Link invalido."), status_code=400)

    from services.email_service import verify_confirmation_token
    member_id = verify_confirmation_token(token)

    if not member_id:
        return HTMLResponse(
            _error_html(app_url, "Link invalido ou expirado. Solicite um novo email de confirmacao."),
            status_code=400,
        )

    log.info(f"Email confirmado — membro {member_id}")
    return RedirectResponse(url=f"{app_url}/painel?email_confirmed=1", status_code=302)


def _error_html(app_url: str, msg: str) -> str:
    return (
        '<!DOCTYPE html><html lang="pt-BR">'
        '<body style="font-family:sans-serif;text-align:center;padding:48px">'
        '<h2 style="color:#e53e3e">Erro</h2>'
        f'<p>{msg}</p>'
        f'<a href="{app_url}" style="color:#1a56db">Voltar para o Clube USA</a>'
        '</body></html>'
    )
