from typing import Optional
import structlog

from app.core.providers.email.base import AbstractEmailProvider

logger = structlog.get_logger(__name__)

class ConsoleEmailProvider(AbstractEmailProvider):
    """
    Concrete Strategy Adapter for Local Offline Testing & Console Logging.
    """
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        logger.info("console_adapter.email_logged", to=to_email, subject=subject)
        return True

    def send_resident_verification_email(self, to_email: str, name: str, token: str) -> bool:
        link = f"{self.base_url}/verify-email?token={token}"
        logger.info("console_adapter.verification_email", to=to_email, verification_link=link)
        return True

    def send_admin_activation_email(self, to_email: str, name: str, society_name: str, token: str) -> bool:
        link = f"{self.base_url}/activate?token={token}"
        logger.info("console_adapter.admin_activation", to=to_email, activation_link=link)
        return True

    def send_membership_approval_email(self, to_email: str, name: str, society_name: str, unit_number: str) -> bool:
        logger.info("console_adapter.membership_approved", to=to_email, society=society_name, unit=unit_number)
        return True

    def send_membership_rejection_email(self, to_email: str, name: str, society_name: str, reason: Optional[str] = None) -> bool:
        logger.info("console_adapter.membership_rejected", to=to_email, society=society_name, reason=reason)
        return True

    def send_society_lead_confirmation(self, to_email: str, contact_name: str, org_name: str) -> bool:
        logger.info("console_adapter.lead_confirmation", to=to_email, org=org_name)
        return True
