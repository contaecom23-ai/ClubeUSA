"""
utils/email_sender.py — Abstração de envio de email para Clube USA

Modos suportados (ordem de prioridade):
  1. SENDGRID_API_KEY configurado  → SendGrid HTTP API
  2. SMTP_HOST configurado          → SMTP padrão (Gmail, Zoho, SES SMTP, etc.)
  3. Nenhuma das anteriores         → modo dev (loga OTP no console, nao envia)

Variaveis de ambiente:
  SENDGRID_API_KEY    — chave do SendGrid (preferida por nao precisar de SMTP)
  SENDGRID_FROM_EMAIL — remetente (default: noreply@clubeusa.com)
  SMTP_HOST           — ex: smtp.gmail.com
  SMTP_PORT           — default 587
  SMTP_USER           — usuario SMTP
  SMTP_PASS           — senha SMTP
  SMTP_FROM_EMAIL     — remetente (default: SMTP_USER)
  ENVIRONMENT         — "production" ativa envio real; qualquer outro loga apenas

Nota: nenhuma credencial default. Se ENVIRONMENT=production mas sem credenciais,
a funcao levanta EnvironmentError (nao envia silenciosamente).
"""

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

log = logging.getLogger("email_sender")

_ENV = os.environ.get("ENVIRONMENT", "development")


# ============================================================
#  TEMPLATES
# ============================================================

def _html_otp(otp: str, name: Optional[str] = None) -> str:
    greeting = f"Olá{', ' + name if name else ''}!"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;text-align:center">
    <img src="https://clubeusa.com/assets/logo.png" alt="Clube USA" width="120"
         style="margin-bottom:24px" onerror="this.style.display='none'">
    <h2 style="color:#1a1a2e;margin-bottom:8px">Confirme seu email</h2>
    <p style="color:#555;margin-bottom:24px">{greeting}<br>
       Use o código abaixo para confirmar seu endereço de email no Clube USA.</p>
    <div style="background:#f0f4ff;border-radius:8px;padding:20px;margin:24px 0;
                font-size:36px;font-weight:bold;letter-spacing:8px;color:#2563eb">
      {otp}
    </div>
    <p style="color:#888;font-size:12px">Válido por 24 horas. Não compartilhe este código.</p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="color:#aaa;font-size:11px">Clube USA • Para imigrantes brasileiros nos EUA</p>
  </div>
</body>
</html>
"""


def _text_otp(otp: str, name: Optional[str] = None) -> str:
    greeting = f"Olá{', ' + name if name else ''}!"
    return (
        f"{greeting}\n\n"
        f"Use o código abaixo para confirmar seu email no Clube USA:\n\n"
        f"  {otp}\n\n"
        "Válido por 24 horas. Não compartilhe este código.\n\n"
        "-- Clube USA"
    )


# ============================================================
#  ENVIO
# ============================================================

def send_email_otp(to_email: str, otp: str, name: Optional[str] = None) -> None:
    """
    Envia OTP de confirmação de email.
    Em modo dev (ENVIRONMENT != 'production'), apenas loga.
    Raises EnvironmentError se producao sem credenciais configuradas.
    """
    if _ENV != "production":
        log.info(f"[DEV] OTP de email para {to_email}: {otp}")
        return

    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    smtp_host    = os.environ.get("SMTP_HOST")

    if sendgrid_key:
        _send_via_sendgrid(to_email, otp, name, sendgrid_key)
    elif smtp_host:
        _send_via_smtp(to_email, otp, name)
    else:
        raise EnvironmentError(
            "Producao: configure SENDGRID_API_KEY ou SMTP_HOST para envio de email."
        )


def _send_via_sendgrid(to_email: str, otp: str, name: Optional[str], api_key: str) -> None:
    import urllib.request
    import json

    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@clubeusa.com")
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": "Clube USA"},
        "subject": f"Código de confirmação: {otp} — Clube USA",
        "content": [
            {"type": "text/plain", "value": _text_otp(otp, name)},
            {"type": "text/html",  "value": _html_otp(otp, name)},
        ],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        if resp.status not in (200, 202):
            raise RuntimeError(f"SendGrid retornou {resp.status}")
    log.info(f"OTP enviado via SendGrid para {to_email[:3]}***")


def _send_via_smtp(to_email: str, otp: str, name: Optional[str]) -> None:
    host      = os.environ["SMTP_HOST"]
    port      = int(os.environ.get("SMTP_PORT", "587"))
    user      = os.environ["SMTP_USER"]
    password  = os.environ["SMTP_PASS"]
    from_addr = os.environ.get("SMTP_FROM_EMAIL", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Código de confirmação: {otp} — Clube USA"
    msg["From"]    = f"Clube USA <{from_addr}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(_text_otp(otp, name), "plain", "utf-8"))
    msg.attach(MIMEText(_html_otp(otp, name), "html",  "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=10) as server:
        server.ehlo()
        server.starttls(context=ctx)
        server.login(user, password)
        server.sendmail(from_addr, to_email, msg.as_string())
    log.info(f"OTP enviado via SMTP para {to_email[:3]}***")
