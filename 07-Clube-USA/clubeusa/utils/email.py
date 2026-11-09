# ============================================================
#  utils/email.py — Clube USA
#  Envio de email via SMTP (qualquer provedor: SendGrid, SES,
#  Resend, Mailgun, Gmail SMTP, etc.)
#
#  Env vars obrigatorias em producao:
#    SMTP_HOST        ex: smtp.sendgrid.net
#    SMTP_PORT        ex: 587
#    SMTP_USER        ex: apikey  (SendGrid) | seu_email (Gmail)
#    SMTP_PASSWORD    ex: SG.xxx  (SendGrid) | app-password (Gmail)
#    SMTP_FROM        ex: noreply@clubeusa.com
#    APP_URL          ex: https://clubeusa.com
#
#  Em dev (sem SMTP configurado), o token e logado no console.
# ============================================================

import os
import hashlib
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email")


def _hash_token(raw_token: str) -> str:
    """SHA-256 do token bruto — unico valor armazenado no banco."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def hash_token(raw_token: str) -> str:
    return _hash_token(raw_token)


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_PASSWORD"))


def _build_verification_email(to_email: str, verify_url: str) -> MIMEMultipart:
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    smtp_from = os.environ.get("SMTP_FROM", "noreply@clubeusa.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Clube USA — Confirme seu email"
    msg["From"] = f"Clube USA <{smtp_from}>"
    msg["To"] = to_email

    text_body = (
        "Clube USA\n\n"
        "Clique no link abaixo para confirmar seu email:\n\n"
        f"{verify_url}\n\n"
        "O link expira em 1 hora.\n"
        "Se voce nao solicitou isso, ignore este email.\n\n"
        f"-- Clube USA | {app_url}"
    )

    html_body = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:8px;padding:32px">
    <h2 style="color:#1a1a2e;margin-top:0">Confirme seu email</h2>
    <p style="color:#444;line-height:1.6">
      Olá! Clique no botão abaixo para confirmar seu email no <strong>Clube USA</strong>.
    </p>
    <div style="text-align:center;margin:28px 0">
      <a href="{verify_url}"
         style="background:#1a73e8;color:#fff;padding:14px 32px;border-radius:6px;
                text-decoration:none;font-weight:bold;font-size:16px;display:inline-block">
        Confirmar Email
      </a>
    </div>
    <p style="color:#888;font-size:13px">
      Link válido por 1 hora.<br>
      Se você não solicitou isso, ignore este email com segurança.
    </p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="color:#aaa;font-size:12px;text-align:center">
      Clube USA · <a href="{app_url}" style="color:#aaa">{app_url}</a>
    </p>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_verification_email(to_email: str, raw_token: str) -> bool:
    """
    Envia email de verificacao.
    Retorna True se enviado (ou logado em dev), False em erro.

    URL do link: APP_URL/auth/email/verify?token=RAW_TOKEN
    """
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    verify_url = f"{app_url}/auth/email/verify?token={raw_token}"

    if not _smtp_configured():
        log.info(f"[DEV] Email verification link para {to_email}: {verify_url}")
        return True

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASSWORD"]

    try:
        msg = _build_verification_email(to_email, verify_url)
        context = ssl.create_default_context()

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        log.info(f"Email de verificacao enviado para {to_email[:3]}***")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de verificacao: {e}")
        return False
