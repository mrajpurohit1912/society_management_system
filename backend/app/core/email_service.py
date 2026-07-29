from app.core.providers.email import AbstractEmailProvider, EmailProviderFactory

# Clean Facade forwarding calls to the configured AbstractEmailProvider via EmailProviderFactory
class EmailService:
    @classmethod
    def get_instance(cls) -> AbstractEmailProvider:
        return EmailProviderFactory.get_provider()

    @classmethod
    def send_resident_verification_email(cls, to_email: str, name: str, token: str) -> bool:
        return cls.get_instance().send_resident_verification_email(to_email, name, token)

    @classmethod
    def send_admin_activation_email(cls, to_email: str, name: str, society_name: str, token: str) -> bool:
        return cls.get_instance().send_admin_activation_email(to_email, name, society_name, token)

    @classmethod
    def send_membership_approval_email(cls, to_email: str, name: str, society_name: str, unit_number: str) -> bool:
        return cls.get_instance().send_membership_approval_email(to_email, name, society_name, unit_number)

    @classmethod
    def send_membership_rejection_email(cls, to_email: str, name: str, society_name: str, reason: str = None) -> bool:
        return cls.get_instance().send_membership_rejection_email(to_email, name, society_name, reason)

    @classmethod
    def send_society_lead_confirmation(cls, to_email: str, contact_name: str, org_name: str) -> bool:
        return cls.get_instance().send_society_lead_confirmation(to_email, contact_name, org_name)
