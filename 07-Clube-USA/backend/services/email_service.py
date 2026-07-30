"""Email service stub.

In production, replace _send() with a real provider call.
See DECISOES.md for the provider decision (SendGrid / AWS SES / Resend).
"""
import logging

from core.config import settings

logger = logging.getLogger(__name__)


def send_confirmation_email(email: str, token: str) -> None:
    """Send the email-confirmation link.

    Production: plug in a real provider.
    Development: logs the link so you can confirm manually.
    """
    confirm_url = f"{settings.app_base_url}/api/v1/auth/confirm-email?token={token}"

    if settings.environment == "production":
        # TODO: replace with real provider (see DECISOES.md)
        logger.warning("Email service not configured — confirmation link NOT sent to %s", email)
        logger.warning("Confirm URL (do not log in production): %s", confirm_url)
    else:
        logger.info("DEV — confirmation link for %s: %s", email, confirm_url)
