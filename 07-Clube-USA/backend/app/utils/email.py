import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger(__name__)


def _build_confirmation_html(full_name: str, confirm_url: str) -> str:
    name = full_name or "Bem-vindo"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Confirme seu email — Clube USA</title></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #0055a5;">🇧🇷 Clube USA</h1>
  </div>
  <h2>Olá, {name}!</h2>
  <p>Obrigado por se cadastrar no <strong>Clube USA</strong> — a plataforma para brasileiros nos EUA.</p>
  <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
  <div style="text-align: center; margin: 30px 0;">
    <a href="{confirm_url}"
       style="background-color: #0055a5; color: white; padding: 14px 28px;
              text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold;">
      Confirmar meu email
    </a>
  </div>
  <p style="color: #666; font-size: 14px;">
    Este link expira em 24 horas. Se você não criou uma conta, pode ignorar este email.
  </p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
  <p style="color: #999; font-size: 12px; text-align: center;">
    Clube USA · Conectando brasileiros nos EUA
  </p>
</body>
</html>
"""


def send_confirmation_email(to_email: str, full_name: str, token: str) -> bool:
    """
    Envia email de confirmação. Retorna True se enviado, False caso SMTP não configurado.
    Em desenvolvimento sem SMTP configurado, loga o link no console (para testes locais).
    """
    confirm_url = f"{settings.FRONTEND_URL}/confirm-email.html?token={token}"

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning(
            "[EMAIL DESABILITADO] Link de confirmação para %s: %s",
            to_email,
            confirm_url,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = to_email

    text_body = (
        f"Olá {full_name}!\n\n"
        "Confirme seu email acessando o link abaixo:\n"
        f"{confirm_url}\n\n"
        "O link expira em 24 horas.\n\n— Clube USA"
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(_build_confirmation_html(full_name, confirm_url), "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        logger.info("Email de confirmação enviado para %s", to_email)
        return True
    except Exception as exc:
        logger.error("Falha ao enviar email para %s: %s", to_email, exc)
        return False
