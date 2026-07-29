from abc import ABC, abstractmethod
from typing import Optional

class AbstractEmailProvider(ABC):
    """
    Abstract Port Interface for Email Notification Providers.
    Fulfills the Dependency Inversion Principle (DIP).
    """

    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Raw email delivery contract."""
        pass

    @abstractmethod
    def send_resident_verification_email(self, to_email: str, name: str, token: str) -> bool:
        """Domain notification for resident verification."""
        pass

    @abstractmethod
    def send_admin_activation_email(self, to_email: str, name: str, society_name: str, token: str) -> bool:
        """Domain notification for admin set-password activation."""
        pass

    @abstractmethod
    def send_membership_approval_email(self, to_email: str, name: str, society_name: str, unit_number: str) -> bool:
        """Domain notification for resident membership approval."""
        pass

    @abstractmethod
    def send_membership_rejection_email(self, to_email: str, name: str, society_name: str, reason: Optional[str] = None) -> bool:
        """Domain notification for resident membership rejection."""
        pass

    @abstractmethod
    def send_society_lead_confirmation(self, to_email: str, contact_name: str, org_name: str) -> bool:
        """Domain notification for public lead submission receipt."""
        pass
