# utils/email.py — Clube USA
# Envio de email transacional.
# Em dev (sem SMTP_HOST): loga o conteudo em vez de enviar.
# Em prod: usa SMTP com TLS. Troque por SendGrid/Postmark ajustando o _send().

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email")

APP_URL   = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_NAME = "Clube USA"
FROM_ADDR = os.environ.get("FROM_EMAIL", "noreply@clubeusa.com")


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST"))


def _send(to: str, subject: str, html: str, text: str) -> None:
    if not _smtp_configured():
        log.info(
            "[EMAIL-DEV] Para: %s | Assunto: %s\n%s",
            to, subject, text,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{FROM_NAME} <{FROM_ADDR}>"
    msg["To"]      = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    pwd  = os.environ.get("SMTP_PASS", "")

    with smtplib.SMTP(host, port, timeout=10) as s:
        s.ehlo()
        s.starttls()
        if user:
            s.login(user, pwd)
        s.sendmail(FROM_ADDR, [to], msg.as_bytes())


def send_confirmation_email(to_email: str, name: str, token: str) -> None:
    confirm_url = f"{APP_URL}/auth/confirm-email/{token}"
    first = name.split()[0] if name else "amigo(a)"

    subject = "Confirme seu email — Clube USA"

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
  <div style="max-width:480px;margin:auto;background:#fff;border-radius:8px;padding:32px">
    <h2 style="color:#1a73e8">Clube USA</h2>
    <p>Olá, <strong>{first}</strong>!</p>
    <p>Obrigado por se cadastrar. Confirme seu email clicando no botão abaixo:</p>
    <p style="text-align:center;margin:32px 0">
      <a href="{confirm_url}"
         style="background:#1a73e8;color:#fff;padding:14px 28px;border-radius:6px;
                text-decoration:none;font-weight:bold">
        Confirmar email
      </a>
    </p>
    <p style="color:#888;font-size:12px">
      Link válido por 24 horas. Se você não criou esta conta, ignore este email.
    </p>
    <hr style="border:none;border-top:1px solid #eee">
    <p style="color:#aaa;font-size:11px">Clube USA · Para imigrantes brasileiros nos EUA</p>
  </div>
</body>
</html>"""

    text = (
        f"Olá, {first}!\n\n"
        f"Confirme seu email acessando:\n{confirm_url}\n\n"
        f"Link válido por 24 horas.\n\n"
        f"— Clube USA"
    )

    try:
        _send(to_email, subject, html, text)
    except Exception as e:
        # Nunca bloqueia o cadastro por falha de email
        log.error("Falha ao enviar email de confirmacao para %s: %s", to_email[:3] + "***", e)
