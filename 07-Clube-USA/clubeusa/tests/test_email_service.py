import pytest
from unittest.mock import MagicMock, patch


def test_dev_mode_returns_true(monkeypatch):
    """In dev mode, emails are only logged — always returns True without SMTP."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    from services.email_service import send_confirmation_email
    assert send_confirmation_email("a@b.com", "Test User", "https://x.com/confirm/abc") is True


def test_prod_mode_no_smtp_config_returns_false(monkeypatch):
    """In prod without SMTP_HOST/USER configured, returns False without crashing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    from services.email_service import send_confirmation_email
    assert send_confirmation_email("a@b.com", "Test", "https://x.com/confirm/abc") is False


def test_prod_mode_smtp_connection_error_returns_false(monkeypatch):
    """In prod with SMTP configured but connection fails, returns False without crashing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_USER", "user@test.com")
    monkeypatch.setenv("SMTP_PASS", "password")
    monkeypatch.setenv("FROM_EMAIL", "noreply@test.com")
    from services.email_service import send_confirmation_email
    with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
        assert send_confirmation_email("a@b.com", "Test", "https://x.com/confirm/abc") is False


def test_prod_mode_smtp_success_returns_true(monkeypatch):
    """In prod with working SMTP, returns True and sends the email."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_USER", "user@test.com")
    monkeypatch.setenv("SMTP_PASS", "password")
    monkeypatch.setenv("FROM_EMAIL", "noreply@test.com")
    from services.email_service import send_confirmation_email
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    with patch("smtplib.SMTP", return_value=mock_smtp), \
         patch("ssl.create_default_context", return_value=MagicMock()):
        assert send_confirmation_email("a@b.com", "Test", "https://x.com/confirm/abc") is True


def test_multiword_name_doesnt_crash(monkeypatch):
    """Full name with spaces must not crash the first-name extraction in the email template."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    from services.email_service import send_confirmation_email
    assert send_confirmation_email("a@b.com", "Maria José Silva", "https://x.com/confirm/abc") is True
