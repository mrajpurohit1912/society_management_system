from typing import Optional
import structlog

from app.core.providers.email.base import AbstractEmailProvider

logger = structlog.get_logger(__name__)

class SendGridEmailProvider(AbstractEmailProvider):
    """
    Concrete Strategy Adapter for SendGrid Integration.
    """
    def __init__(self, api_key: str, from_email: str, base_url: str):
        self.api_key = api_key
        self.from_email = from_email
        self.base_url = base_url

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        logger.info("sendgrid_adapter.send_email_stub", to=to_email, subject=subject)
        return True

    def send_resident_verification_email(self, to_email: str, name: str, token: str) -> bool:
        return self.send_email(to_email, "Verify Email", f"Token: {token}")

    def send_admin_activation_email(self, to_email: str, name: str, society_name: str, token: str) -> bool:
        return self.send_email(to_email, "Activate Admin", f"Token: {token}")

    def send_membership_approval_email(self, to_email: str, name: str, society_name: str, unit_number: str) -> bool:
        return self.send_email(to_email, "Membership Approved", f"Unit: {unit_number}")

    def send_membership_rejection_email(self, to_email: str, name: str, society_name: str, reason: Optional[str] = None) -> bool:
        return self.send_email(to_email, "Membership Rejected", f"Reason: {reason}")

    def send_society_lead_confirmation(self, to_email: str, contact_name: str, org_name: str) -> bool:
        return self.send_email(to_email, "Lead Received", f"Org: {org_name}")
