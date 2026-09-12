# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais (confirmacao de email, etc.)
#
#  Configurar via env vars:
#    EMAIL_PROVIDER=log|resend|sendgrid   (default: log — apenas loga, nao envia)
#    EMAIL_FROM=noreply@clubeusa.com
#    EMAIL_FROM_NAME=Clube USA
#    RESEND_API_KEY=re_xxxxx             (se EMAIL_PROVIDER=resend)
#    SENDGRID_API_KEY=SG.xxxxx           (se EMAIL_PROVIDER=sendgrid)
#
#  Para ativar em producao:
#    1. Escolha o provedor (ver DECISOES.md D-001)
#    2. Configure as env vars no Render
#    3. Verifique o dominio remetente no painel do provedor
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

EMAIL_PROVIDER  = os.environ.get("EMAIL_PROVIDER", "log")
EMAIL_FROM      = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Clube USA")


def generate_confirm_token() -> tuple:
    """
    Gera token seguro de confirmacao de email.
    Retorna (token: str, expires_at: datetime) — validade de 24h.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return token, expires_at


def send_confirmation_email(
    to_email: str,
    member_name: str,
    confirm_url: str,
    language: str = "pt",
) -> bool:
    """
    Envia email de confirmacao de endereco.

    Em dev (EMAIL_PROVIDER=log): loga o link, nao envia.
    Em prod: usa Resend ou SendGrid conforme EMAIL_PROVIDER.

    Retorna True se enviado/logado, False se falhou.
    Nunca levanta excecao — erros sao logados e retorna False.
    """
    subject, body = _build_confirm_email(member_name, confirm_url, language)

    if EMAIL_PROVIDER == "log":
        log.info(
            "[EMAIL-DEV] Para=%s Assunto=%r | Link: %s",
            to_email, subject, confirm_url,
        )
        return True

    if EMAIL_PROVIDER == "resend":
        return _send_resend(to_email, subject, body)

    if EMAIL_PROVIDER == "sendgrid":
        return _send_sendgrid(to_email, subject, body)

    log.warning("EMAIL_PROVIDER '%s' nao suportado. Email nao enviado.", EMAIL_PROVIDER)
    return False


# ============================================================
#  BUILDERS
# ============================================================

def _build_confirm_email(member_name: str, confirm_url: str, language: str) -> tuple:
    greeting = f", {member_name}" if member_name else ""

    if language == "es":
        subject = "Confirma tu correo — Club USA"
        body = (
            f"¡Hola{greeting}!\n\n"
            "Para confirmar tu correo en Club USA, haz clic aquí:\n\n"
            f"{confirm_url}\n\n"
            "El enlace expira en 24 horas.\n\n"
            "Si no te registraste en Club USA, ignora este mensaje.\n\n"
            "— Club USA"
        )
    else:
        subject = "Confirme seu email — Clube USA"
        body = (
            f"Olá{greeting}!\n\n"
            "Para confirmar seu email no Clube USA, clique aqui:\n\n"
            f"{confirm_url}\n\n"
            "O link expira em 24 horas.\n\n"
            "Se você não se cadastrou no Clube USA, ignore este email.\n\n"
            "— Clube USA"
        )
    return subject, body


# ============================================================
#  PROVEDORES
# ============================================================

def _send_resend(to_email: str, subject: str, body: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        log.warning("RESEND_API_KEY nao configurada. Email nao enviado.")
        return False
    try:
        import requests
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from":    f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
                "to":      [to_email],
                "subject": subject,
                "text":    body,
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Email enviado via Resend para %s", to_email)
        return True
    except Exception as e:
        log.error("Erro Resend ao enviar para %s: %s", to_email, e)
        return False


def _send_sendgrid(to_email: str, subject: str, body: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        log.warning("SENDGRID_API_KEY nao configurada. Email nao enviado.")
        return False
    try:
        import requests
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from":    {"email": EMAIL_FROM, "name": EMAIL_FROM_NAME},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Email enviado via SendGrid para %s", to_email)
        return True
    except Exception as e:
        log.error("Erro SendGrid ao enviar para %s: %s", to_email, e)
        return False
