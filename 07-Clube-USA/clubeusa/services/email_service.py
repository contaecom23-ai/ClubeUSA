# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais (confirmação de conta, etc.)
#
#  Em dev (ENVIRONMENT != production): loga o link, não envia.
#  Em prod: usa SMTP via env vars (SMTP_HOST, SMTP_PORT,
#    SMTP_USER, SMTP_PASS, SMTP_FROM).
# ============================================================

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

_TEMPLATES = {
    "confirm_pt": {
        "subject": "Confirme seu email — Clube USA",
        "html": """\
<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden">
  <div style="background:#1a56db;padding:32px;text-align:center">
    <h1 style="color:#fff;margin:0;font-size:24px">Clube USA</h1>
  </div>
  <div style="padding:32px">
    <h2 style="margin-top:0;color:#111">Olá{name_part}!</h2>
    <p style="color:#444;line-height:1.6">
      Bem-vindo ao Clube USA! Para ativar sua conta e aproveitar todos os benefícios,
      confirme seu email clicando no botão abaixo.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{confirm_url}" style="background:#1a56db;color:#fff;text-decoration:none;
         padding:14px 32px;border-radius:6px;font-size:16px;font-weight:bold;display:inline-block">
        Confirmar Email
      </a>
    </div>
    <p style="color:#888;font-size:13px">
      Link válido por 48 horas. Se você não criou esta conta, ignore este email.
    </p>
    <p style="color:#888;font-size:12px">
      Ou cole este link no navegador:<br>
      <a href="{confirm_url}" style="color:#1a56db;word-break:break-all">{confirm_url}</a>
    </p>
  </div>
  <div style="background:#f5f5f5;padding:16px;text-align:center">
    <p style="color:#aaa;font-size:12px;margin:0">© Clube USA — Para imigrantes brasileiros nos EUA</p>
  </div>
</div>
</body>
</html>""",
    },
    "confirm_es": {
        "subject": "Confirma tu email — Club USA",
        "html": """\
<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden">
  <div style="background:#1a56db;padding:32px;text-align:center">
    <h1 style="color:#fff;margin:0;font-size:24px">Club USA</h1>
  </div>
  <div style="padding:32px">
    <h2 style="margin-top:0;color:#111">¡Hola{name_part}!</h2>
    <p style="color:#444;line-height:1.6">
      ¡Bienvenido a Club USA! Para activar tu cuenta y disfrutar todos los beneficios,
      confirma tu email haciendo clic en el botón de abajo.
    </p>
    <div style="text-align:center;margin:32px 0">
      <a href="{confirm_url}" style="background:#1a56db;color:#fff;text-decoration:none;
         padding:14px 32px;border-radius:6px;font-size:16px;font-weight:bold;display:inline-block">
        Confirmar Email
      </a>
    </div>
    <p style="color:#888;font-size:13px">
      Enlace válido por 48 horas. Si no creaste esta cuenta, ignora este email.
    </p>
    <p style="color:#888;font-size:12px">
      O pega este enlace en tu navegador:<br>
      <a href="{confirm_url}" style="color:#1a56db;word-break:break-all">{confirm_url}</a>
    </p>
  </div>
  <div style="background:#f5f5f5;padding:16px;text-align:center">
    <p style="color:#aaa;font-size:12px;margin:0">© Club USA — Para inmigrantes brasileños en los EE.UU.</p>
  </div>
</div>
</body>
</html>""",
    },
}


def send_confirmation_email(
    email: str, token: str, name: str = "", language: str = "pt"
) -> bool:
    """
    Envia email de confirmação de conta.

    Returns True on success (or dev mode), False on SMTP failure.
    Dev mode: imprime o link no log, não envia.
    """
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    confirm_url = f"{app_url}/verificar-email?token={token}"
    name_part = f" {name.strip()}" if name and name.strip() else ""

    tmpl_key = f"confirm_{language}" if language in ("pt", "es") else "confirm_pt"
    tmpl = _TEMPLATES[tmpl_key]
    subject = tmpl["subject"]
    body_html = tmpl["html"].format(confirm_url=confirm_url, name_part=name_part)

    if os.environ.get("ENVIRONMENT", "development") != "production":
        log.info("[DEV] Confirmação de email para %s***  →  %s", email[:4], confirm_url)
        return True

    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        log.warning("SMTP não configurado — email de confirmação não enviado para %s***", email[:4])
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = smtp_from
        msg["To"]      = email
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [email], msg.as_string())

        log.info("Email de confirmação enviado para %s***", email[:4])
        return True
    except Exception as exc:
        log.error("Falha ao enviar email de confirmação para %s***: %s", email[:4], exc)
        return False
