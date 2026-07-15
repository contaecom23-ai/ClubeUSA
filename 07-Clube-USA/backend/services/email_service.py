import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings):
        self.settings = settings

    async def send_confirmation_email(self, to: str, full_name: str, confirm_url: str) -> None:
        if not self.settings.smtp_host:
            logger.warning(
                "[EMAIL NÃO ENVIADO — configure SMTP_HOST]\nPara: %s\nLink: %s",
                to,
                confirm_url,
            )
            return

        try:
            import aiosmtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Confirme seu email — Clube USA"
            msg["From"] = self.settings.email_from
            msg["To"] = to

            html_body = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a">
  <h2 style="color:#1a56db">Bem-vindo ao Clube USA, {full_name}!</h2>
  <p>Obrigado por se cadastrar. Clique no botão abaixo para confirmar seu email:</p>
  <a href="{confirm_url}"
     style="display:inline-block;background:#1a56db;color:#fff;padding:12px 28px;
            border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
    Confirmar Email
  </a>
  <p style="color:#666;font-size:12px;margin-top:24px">
    Link válido por 24 horas.<br>
    Se não foi você, ignore este email.
  </p>
</body>
</html>"""

            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user or None,
                password=self.settings.smtp_password or None,
                start_tls=True,
            )
            logger.info("Email de confirmação enviado para %s", to)

        except Exception as exc:
            # Falha no email não impede o cadastro — usuário pode reenviar depois
            logger.error("Falha ao enviar email para %s: %s", to, exc)
