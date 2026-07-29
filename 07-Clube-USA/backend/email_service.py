import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor

from config import settings

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mailer")


def _send_smtp(to: str, subject: str, html: str) -> None:
    if not settings.smtp_host:
        logger.warning(
            "SMTP not configured — skipping email. to=%s subject=%s", to, subject
        )
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as srv:
        srv.ehlo()
        srv.starttls()
        srv.login(settings.smtp_user, settings.smtp_password)
        srv.sendmail(settings.email_from, [to], msg.as_string())
    logger.info("Email sent. to=%s subject=%s", to, subject)


def _fire_and_forget(to: str, subject: str, html: str) -> None:
    future = _executor.submit(_send_smtp, to, subject, html)
    future.add_done_callback(
        lambda f: logger.error("Email error: %s", f.exception()) if f.exception() else None
    )


def send_confirmation_email(to: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.app_url}/confirm-email.html?token={token}"
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:40px auto;padding:24px;
                       background:#f9fafb;border-radius:8px;">
      <div style="background:#fff;padding:32px;border-radius:8px;border:1px solid #e5e7eb;">
        <h1 style="color:#1a56db;margin-top:0;">Bem-vindo ao Clube USA! 🇧🇷</h1>
        <p style="color:#374151;">Olá <strong>{full_name}</strong>,</p>
        <p style="color:#374151;">Clique no botão abaixo para confirmar seu endereço de email
           e ativar sua conta:</p>
        <div style="text-align:center;margin:32px 0;">
          <a href="{confirm_url}"
             style="background:#1a56db;color:#fff;padding:14px 28px;border-radius:6px;
                    text-decoration:none;font-weight:bold;font-size:16px;display:inline-block;">
            Confirmar Email
          </a>
        </div>
        <p style="color:#6b7280;font-size:13px;">
          Este link expira em 24 horas.<br>
          Se você não criou uma conta no Clube USA, ignore este email.
        </p>
      </div>
    </body></html>
    """
    _fire_and_forget(to, "Confirme seu email — Clube USA", html)


def send_welcome_email(to: str, full_name: str) -> None:
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:40px auto;padding:24px;
                       background:#f9fafb;border-radius:8px;">
      <div style="background:#fff;padding:32px;border-radius:8px;border:1px solid #e5e7eb;">
        <h1 style="color:#1a56db;margin-top:0;">Email confirmado! ✅</h1>
        <p style="color:#374151;">Olá <strong>{full_name}</strong>,</p>
        <p style="color:#374151;">Sua conta no <strong>Clube USA</strong> está ativa.
           Agora você tem acesso a promoções, empregos, moradia e oportunidades
           para brasileiros nos EUA.</p>
        <div style="text-align:center;margin:32px 0;">
          <a href="{settings.app_url}/login.html"
             style="background:#1a56db;color:#fff;padding:14px 28px;border-radius:6px;
                    text-decoration:none;font-weight:bold;font-size:16px;display:inline-block;">
            Entrar na plataforma
          </a>
        </div>
      </div>
    </body></html>
    """
    _fire_and_forget(to, "Bem-vindo ao Clube USA! 🇧🇷", html)
