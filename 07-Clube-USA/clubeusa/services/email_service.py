# ============================================================
#  services/email_service.py — Clube USA
#  Abstração de envio de email
#
#  Dev: loga o link (sem envio real)
#  Prod: usa SMTP configurado (SendGrid, SES, Resend, qualquer)
#
#  Variáveis de ambiente necessárias em produção:
#    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS
#    FROM_EMAIL (default noreply@clubeusa.com)
# ============================================================

import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")


def send_confirmation_email(to_email: str, member_name: str, confirm_url: str) -> bool:
    """
    Envia email de confirmação de cadastro.
    Retorna True se enviado (ou se em dev), False se erro em prod.
    """
    name = member_name or "membro"

    if os.environ.get("ENVIRONMENT", "development") != "production":
        log.info("[DEV] Email de confirmacao para %s | URL: %s", to_email, confirm_url)
        return True

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_email = os.environ.get("FROM_EMAIL", "noreply@clubeusa.com")

    if not all([smtp_host, smtp_user, smtp_pass]):
        log.error("SMTP nao configurado — email de confirmacao nao enviado para %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"]    = from_email
    msg["To"]      = to_email

    text = (
        f"Clube USA\n\nOlá {name}!\n\n"
        f"Confirme seu email clicando no link abaixo:\n{confirm_url}\n\n"
        "Link válido por 24 horas.\n"
        "Se você não criou uma conta, ignore este email."
    )
    html = _build_html(name, confirm_url)

    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html",  "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(smtp_user, smtp_pass)
            s.sendmail(from_email, [to_email], msg.as_string())
        log.info("Email de confirmacao enviado para %s", to_email)
        return True
    except Exception as exc:
        log.error("Falha ao enviar email de confirmacao para %s: %s", to_email, exc)
        return False


def _build_html(name: str, url: str) -> str:
    safe_url  = url.replace("&", "&amp;").replace('"', "&quot;")
    safe_name = name.replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:Arial,sans-serif;background:#f9fafb;margin:0;padding:32px 16px">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <table width="480" style="background:#fff;border-radius:12px;padding:40px;box-shadow:0 1px 6px rgba(0,0,0,.08)">
        <tr><td>
          <h1 style="color:#1a56db;margin:0 0 8px">Clube USA</h1>
          <p style="color:#374151">Olá {safe_name},</p>
          <p style="color:#374151">Clique no botão abaixo para confirmar seu endereço de email:</p>
          <p style="text-align:center;margin:28px 0">
            <a href="{safe_url}"
               style="background:#1a56db;color:#fff;padding:14px 28px;text-decoration:none;border-radius:8px;display:inline-block;font-weight:bold">
              Confirmar Email
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px">
            Link válido por 24 horas.<br>
            Se você não criou uma conta no Clube USA, ignore este email.
          </p>
          <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
          <p style="color:#9ca3af;font-size:12px;text-align:center">
            Clube USA — A plataforma do imigrante brasileiro nos EUA
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
