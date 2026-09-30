# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails via SMTP generico
#
#  Variaveis de ambiente necessarias:
#    SMTP_HOST    — ex: smtp.sendgrid.net ou smtp.resend.com
#    SMTP_PORT    — ex: 587 (TLS) ou 465 (SSL)
#    SMTP_USER    — usuario SMTP
#    SMTP_PASS    — senha/API key SMTP
#    SMTP_FROM    — ex: "Clube USA <noreply@clubeusa.com>"
#    APP_URL      — ex: https://clubeusa.com
# ============================================================

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

_SMTP_CONFIGURED = bool(
    os.environ.get("SMTP_HOST") and
    os.environ.get("SMTP_USER") and
    os.environ.get("SMTP_PASS")
)


def _smtp_enabled() -> bool:
    return bool(
        os.environ.get("SMTP_HOST") and
        os.environ.get("SMTP_USER") and
        os.environ.get("SMTP_PASS")
    )


def send_confirmation_email(email: str, token: str, language: str = "pt") -> bool:
    """
    Envia email de confirmacao de cadastro.
    Retorna True se enviado, False se SMTP nao configurado (dev).
    Nao lanca excecao — falha nao deve bloquear o cadastro.
    """
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    confirm_url = f"{app_url}/auth/confirm-email?token={token}"

    subjects = {
        "pt": "Confirme seu email — Clube USA",
        "es": "Confirma tu email — Club USA",
    }
    html_bodies = {
        "pt": f"""
<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 20px; color: #222;">
  <div style="text-align:center; margin-bottom: 24px;">
    <h1 style="color: #009739; font-size: 24px; margin: 0;">&#127465;&#127479; Clube USA</h1>
    <p style="color: #666; font-size: 14px; margin: 4px 0 0;">A plataforma do imigrante brasileiro nos EUA</p>
  </div>
  <h2 style="font-size: 20px;">Confirme seu email</h2>
  <p>Olá! Clique no botão abaixo para confirmar seu email e ativar todas as funcionalidades da sua conta.</p>
  <div style="text-align:center; margin: 32px 0;">
    <a href="{confirm_url}"
       style="background:#009739; color:#fff; padding:14px 32px; border-radius:8px;
              text-decoration:none; font-size:16px; font-weight:bold;">
      Confirmar email
    </a>
  </div>
  <p style="font-size: 13px; color: #666;">
    O link expira em 48 horas. Se você não criou uma conta no Clube USA, ignore este email.
  </p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
  <p style="font-size: 12px; color: #999; text-align: center;">
    Clube USA · <a href="{app_url}" style="color:#009739;">clubeusa.com</a>
  </p>
</body>
</html>
""",
        "es": f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 20px; color: #222;">
  <div style="text-align:center; margin-bottom: 24px;">
    <h1 style="color: #009739; font-size: 24px; margin: 0;">&#127465;&#127479; Club USA</h1>
    <p style="color: #666; font-size: 14px; margin: 4px 0 0;">La plataforma del inmigrante brasileño en EE.UU.</p>
  </div>
  <h2 style="font-size: 20px;">Confirma tu email</h2>
  <p>¡Hola! Haz clic en el botón de abajo para confirmar tu email y activar todas las funcionalidades de tu cuenta.</p>
  <div style="text-align:center; margin: 32px 0;">
    <a href="{confirm_url}"
       style="background:#009739; color:#fff; padding:14px 32px; border-radius:8px;
              text-decoration:none; font-size:16px; font-weight:bold;">
      Confirmar email
    </a>
  </div>
  <p style="font-size: 13px; color: #666;">
    El enlace expira en 48 horas. Si no creaste una cuenta en Club USA, ignora este email.
  </p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
  <p style="font-size: 12px; color: #999; text-align: center;">
    Club USA · <a href="{app_url}" style="color:#009739;">clubeusa.com</a>
  </p>
</body>
</html>
""",
    }

    subject = subjects.get(language, subjects["pt"])
    html_body = html_bodies.get(language, html_bodies["pt"])

    if not _smtp_enabled():
        log.info(f"[DEV] Email de confirmacao para {email}: {confirm_url}")
        return False

    try:
        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ["SMTP_USER"]
        smtp_pass = os.environ["SMTP_PASS"]
        smtp_from = os.environ.get("SMTP_FROM", f"Clube USA <{smtp_user}>")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [email], msg.as_string())

        log.info(f"Email de confirmacao enviado para {email[:3]}***")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de confirmacao: {e}")
        return False
