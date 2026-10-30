# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais
#
#  Estrategia de envio (em ordem de preferencia):
#    1. RESEND_API_KEY definido -> Resend API (recomendado)
#    2. SMTP_HOST definido      -> SMTP generico
#    3. Nenhum                  -> log (modo dev, nao envia)
#
#  Seguranca: nunca loga corpo do email (evitar PII em logs).
# ============================================================

import os
import logging
import smtplib
import hashlib
import secrets
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

log = logging.getLogger("email_service")

_BASE_URL = os.environ.get("APP_BASE_URL", "https://clubeusa.com")
_FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@clubeusa.com")
_FROM_NAME = os.environ.get("FROM_NAME", "Clube USA")
_TOKEN_TTL_HOURS = 24


# ============================================================
#  Token
# ============================================================

def generate_email_verification_token() -> tuple[str, str, datetime]:
    """
    Retorna (token_plaintext, token_hash, expires_at).
    Armazene apenas token_hash no banco.
    """
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=_TOKEN_TTL_HOURS)
    return token, token_hash, expires_at


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================
#  Templates de email
# ============================================================

def _build_verification_email(name: str, verify_url: str, language: str) -> tuple[str, str, str]:
    """Retorna (subject, body_text, body_html)."""
    first = name.split()[0] if name else "membro"

    if language == "es":
        subject = "Confirma tu correo — Clube USA"
        text = (
            f"Hola {first},\n\n"
            f"Confirma tu correo electronico haciendo clic en el enlace a continuacion:\n\n"
            f"{verify_url}\n\n"
            f"El enlace expira en {_TOKEN_TTL_HOURS} horas.\n\n"
            f"Si no creaste una cuenta en Clube USA, ignora este mensaje.\n\n"
            f"— Equipo Clube USA"
        )
        html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
<h2 style="color:#1a56db">Clube USA</h2>
<p>Hola <strong>{first}</strong>,</p>
<p>Confirma tu correo electronico para activar tu cuenta:</p>
<p><a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#1a56db;color:white;text-decoration:none;border-radius:6px;font-weight:bold">Confirmar correo</a></p>
<p style="color:#666;font-size:13px">El enlace expira en {_TOKEN_TTL_HOURS} horas.</p>
<p style="color:#999;font-size:12px">Si no creaste una cuenta en Clube USA, ignora este mensaje.</p>
</body></html>"""
    else:
        subject = "Confirme seu email — Clube USA"
        text = (
            f"Ola {first},\n\n"
            f"Confirme seu email clicando no link abaixo:\n\n"
            f"{verify_url}\n\n"
            f"O link expira em {_TOKEN_TTL_HOURS} horas.\n\n"
            f"Se voce nao criou uma conta no Clube USA, ignore esta mensagem.\n\n"
            f"— Equipe Clube USA"
        )
        html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:24px">
<h2 style="color:#1a56db">Clube USA</h2>
<p>Ola <strong>{first}</strong>,</p>
<p>Confirme seu email para ativar sua conta:</p>
<p><a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#1a56db;color:white;text-decoration:none;border-radius:6px;font-weight:bold">Confirmar email</a></p>
<p style="color:#666;font-size:13px">O link expira em {_TOKEN_TTL_HOURS} horas.</p>
<p style="color:#999;font-size:12px">Se voce nao criou uma conta no Clube USA, ignore esta mensagem.</p>
</body></html>"""

    return subject, text, html


# ============================================================
#  Envio
# ============================================================

def send_verification_email(to_email: str, token: str, name: str = "", language: str = "pt") -> bool:
    """
    Envia email de verificacao. Retorna True se enviado (ou logado em dev).
    Nao lanca excecao — falha silenciosa com log de warning.
    """
    verify_url = f"{_BASE_URL}/auth/email/verify?token={token}"
    subject, body_text, body_html = _build_verification_email(name, verify_url, language)

    resend_key = os.environ.get("RESEND_API_KEY")
    smtp_host  = os.environ.get("SMTP_HOST")

    if resend_key:
        return _send_via_resend(to_email, subject, body_html, body_text, resend_key)
    elif smtp_host:
        return _send_via_smtp(to_email, subject, body_html, body_text)
    else:
        log.warning(
            "[DEV] Email nao enviado (sem RESEND_API_KEY ou SMTP_HOST). "
            "Token seria enviado para: %s | URL: %s",
            to_email[:3] + "***",
            verify_url,
        )
        return True  # em dev, considera "enviado" para nao bloquear fluxo


def _send_via_resend(to_email: str, subject: str, html: str, text: str, api_key: str) -> bool:
    import urllib.request, json
    payload = json.dumps({
        "from":    f"{_FROM_NAME} <{_FROM_EMAIL}>",
        "to":      [to_email],
        "subject": subject,
        "html":    html,
        "text":    text,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                log.info("Email enviado via Resend para %s***", to_email[:3])
                return True
            log.warning("Resend retornou status %d", resp.status)
            return False
    except Exception as e:
        log.warning("Falha ao enviar via Resend: %s", e)
        return False


def _send_via_smtp(to_email: str, subject: str, html: str, text: str) -> bool:
    host  = os.environ["SMTP_HOST"]
    port  = int(os.environ.get("SMTP_PORT", "587"))
    user  = os.environ.get("SMTP_USER", _FROM_EMAIL)
    pwd   = os.environ.get("SMTP_PASSWORD", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{_FROM_NAME} <{_FROM_EMAIL}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, pwd)
            server.sendmail(_FROM_EMAIL, to_email, msg.as_string())
        log.info("Email enviado via SMTP para %s***", to_email[:3])
        return True
    except Exception as e:
        log.warning("Falha ao enviar via SMTP: %s", e)
        return False
