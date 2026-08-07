import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import get_settings


def send_confirmation_email(to_email: str, confirmation_url: str) -> None:
    s = get_settings()

    if not s.EMAIL_ENABLED:
        # Desenvolvimento: loga o link sem expor em resposta HTTP
        print(f"[DEV] Confirmação de email para {to_email}: {confirmation_url}", file=sys.stderr)
        return

    body_html = f"""
    <html><body>
    <h2>Bem-vindo ao Clube USA!</h2>
    <p>Clique no link abaixo para confirmar seu email:</p>
    <p><a href="{confirmation_url}">{confirmation_url}</a></p>
    <p>O link expira em 24 horas.</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"] = s.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(s.SMTP_USER, s.SMTP_PASSWORD)
            server.sendmail(s.SMTP_FROM, [to_email], msg.as_string())
    except Exception as e:
        # Loga erro sem expor credenciais ou dados do usuário
        print(f"[ERROR] Falha ao enviar email de confirmação: {type(e).__name__}", file=sys.stderr)
        raise
