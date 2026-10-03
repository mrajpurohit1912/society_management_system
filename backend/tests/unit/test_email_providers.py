from unittest.mock import patch, MagicMock
import pytest
from app.core.providers.email.adapters.smtp import SmtpEmailProvider
from app.core.providers.email.factory import EmailProviderFactory
from app.core.email_service import EmailService


def test_smtp_disabled_when_missing_credentials():
    provider = SmtpEmailProvider(
        host="smtp.gmail.com",
        port=587,
        user=None,
        password=None,
    )
    result = provider.send_email("test@example.com", "Subject", "<p>Body</p>")
    assert result is False


@patch("smtplib.SMTP")
def test_smtp_send_email_starttls_success(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_server

    provider = SmtpEmailProvider(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="app password with spaces",
        use_tls=True,
    )
    assert provider.password == "apppasswordwithspaces"

    result = provider.send_email("recipient@example.com", "Test Subject", "<p>Hello</p>")
    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("test@gmail.com", "apppasswordwithspaces")
    mock_server.send_message.assert_called_once()


@patch("smtplib.SMTP_SSL")
def test_smtp_send_email_ssl_success(mock_smtp_ssl_cls):
    mock_server = MagicMock()
    mock_smtp_ssl_cls.return_value.__enter__.return_value = mock_server

    provider = SmtpEmailProvider(
        host="smtp.gmail.com",
        port=465,
        user="test@gmail.com",
        password="password123",
        use_tls=False,
    )

    result = provider.send_email("recipient@example.com", "Test SSL", "<p>SSL</p>")
    assert result is True
    mock_server.login.assert_called_once_with("test@gmail.com", "password123")
    mock_server.send_message.assert_called_once()


@patch("smtplib.SMTP")
def test_smtp_send_email_exception_handling(mock_smtp_cls):
    mock_smtp_cls.side_effect = Exception("SMTP server down")

    provider = SmtpEmailProvider(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="password123",
    )

    result = provider.send_email("recipient@example.com", "Subject", "<p>Fail</p>")
    assert result is False


@patch("app.core.providers.email.adapters.smtp.SmtpEmailProvider.send_email")
def test_smtp_domain_notifications(mock_send):
    mock_send.return_value = True
    provider = SmtpEmailProvider(
        host="smtp.gmail.com",
        port=587,
        user="admin@gmail.com",
        password="secretpassword",
    )

    assert provider.send_resident_verification_email("res@example.com", "John", "token123") is True
    assert provider.send_admin_activation_email("admin@example.com", "Jane", "Green Valley", "token456") is True
    assert provider.send_membership_approval_email("res@example.com", "John", "Green Valley", "A-101") is True
    assert provider.send_membership_rejection_email("res@example.com", "John", "Green Valley", "Invalid ID") is True
    assert provider.send_society_lead_confirmation("lead@example.com", "Mark", "Palm Grove") is True
    assert mock_send.call_count == 5


def test_email_factory_resolution():
    smtp_provider = EmailProviderFactory.get_provider("smtp")
    assert isinstance(smtp_provider, SmtpEmailProvider)

    console_provider = EmailProviderFactory.get_provider("console")
    assert console_provider is not None

    unknown_provider = EmailProviderFactory.get_provider("nonexistent")
    assert unknown_provider is not None
