# ============================================================
#  api/routers/email_verification.py — Clube USA
#  Endpoints de confirmacao de email
#
#  POST /auth/email/verify/request  — requer auth; solicita envio
#  GET  /auth/email/verify/{token}  — publico; confirma o token
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from deps import get_current_member

router = APIRouter(tags=["auth"])


@router.post("/auth/email/verify/request", status_code=202)
async def request_email_verification(member: dict = Depends(get_current_member)):
    """
    Envia (ou reloga em dev) link de confirmacao de email para o membro autenticado.
    - Requer que o membro tenha um email cadastrado.
    - Max 3 solicitacoes por 24h.
    - Nao bloqueia acesso; email confirmado da +100 pontos.
    """
    from services.email_verification_service import request_email_verification as svc
    try:
        return svc(member["sub"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/email/verify/{token}", response_class=HTMLResponse, include_in_schema=False)
async def confirm_email_verification(token: str):
    """
    Endpoint publico clicavel do email de confirmacao.
    Retorna HTML simples (sem JS) compativel com qualquer cliente de email.
    """
    from services.email_verification_service import confirm_email_verification as svc

    try:
        result = svc(token)
    except ValueError as e:
        return _page(
            success=False,
            title="Link invalido",
            message=str(e),
        )

    if result.get("already_verified"):
        return _page(
            success=True,
            title="Email ja confirmado",
            message="Seu email ja estava confirmado. Nenhuma acao necessaria.",
            points=None,
        )

    return _page(
        success=True,
        title="Email confirmado!",
        message="Seu email foi verificado com sucesso.",
        points=result.get("points_awarded"),
    )


def _page(success: bool, title: str, message: str, points: int = None) -> str:
    color = "#22c55e" if success else "#ef4444"
    icon  = "✓" if success else "✕"
    points_html = (
        f'<p style="color:#f59e0b;font-weight:600;">+{points} pontos creditados!</p>'
        if points else ""
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Clube USA — {title}</title>
  <style>
    body{{margin:0;font-family:system-ui,sans-serif;background:#0f172a;
         display:flex;align-items:center;justify-content:center;min-height:100vh}}
    .card{{background:#1e293b;border-radius:16px;padding:40px 32px;max-width:400px;
           width:90%;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.4)}}
    .icon{{font-size:56px;color:{color};margin-bottom:16px}}
    h1{{color:#f1f5f9;font-size:24px;margin:0 0 12px}}
    p{{color:#94a3b8;margin:0 0 8px;line-height:1.5}}
    a{{display:inline-block;margin-top:24px;padding:12px 28px;background:#3b82f6;
       color:#fff;border-radius:8px;text-decoration:none;font-weight:600}}
    a:hover{{background:#2563eb}}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{title}</h1>
    <p>{message}</p>
    {points_html}
    <a href="/">Ir para o Clube USA</a>
  </div>
</body>
</html>"""
