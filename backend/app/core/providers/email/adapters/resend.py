from typing import Optional
import requests
import structlog

from app.core.providers.email.base import AbstractEmailProvider

logger = structlog.get_logger(__name__)

class ResendEmailProvider(AbstractEmailProvider):
    """
    Concrete Strategy Adapter for Resend HTTP API.
    """
    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str, base_url: str):
        self.api_key = api_key
        self.from_email = from_email
        self.base_url = base_url

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        if not self.api_key:
            logger.warning("resend_adapter.disabled", reason="RESEND_API_KEY is missing")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": f"Society Management System <{self.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        try:
            response = requests.post(self.RESEND_API_URL, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201):
                logger.info("resend_adapter.success", to=to_email, subject=subject, response=response.json())
                return True
            else:
                logger.error("resend_adapter.failed", to=to_email, status=response.status_code, response=response.text)
                return False
        except Exception as e:
            logger.exception("resend_adapter.error", to=to_email, error=str(e))
            return False

    def send_resident_verification_email(self, to_email: str, name: str, token: str) -> bool:
        verification_link = f"{self.base_url}/verify-email?token={token}"
        subject = "Verify Your Email - Society Management Platform"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2b6cb0;">Welcome to Society Management System!</h2>
            <p>Hi <strong>{name}</strong>,</p>
            <p>Thank you for registering. Please click the button below to verify your email address and activate your account:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #3182ce; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email Address</a>
            </div>
            <p style="color: #718096; font-size: 14px;">Or copy and paste this link in your browser: <br><a href="{verification_link}">{verification_link}</a></p>
            <hr style="border: none; border-top: 1px solid #edf2f7; margin: 20px 0;">
            <p style="color: #a0aec0; font-size: 12px;">This link will expire in 24 hours.</p>
        </div>
        """
        return self.send_email(to_email, subject, html_content)

    def send_admin_activation_email(self, to_email: str, name: str, society_name: str, token: str) -> bool:
        activation_link = f"{self.base_url}/activate?token={token}"
        subject = f"Activate Your Society Admin Account - {society_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2c5282;">Activate Admin Account - {society_name}</h2>
            <p>Hi <strong>{name}</strong>,</p>
            <p>Your Society Admin account for <strong>{society_name}</strong> has been provisioned.</p>
            <p>Please click the link below to set your password and complete your account setup:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{activation_link}" style="background-color: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Set Password & Activate</a>
            </div>
            <p style="color: #718096; font-size: 14px;">Direct Link: <a href="{activation_link}">{activation_link}</a></p>
            <hr style="border: none; border-top: 1px solid #edf2f7; margin: 20px 0;">
            <p style="color: #a0aec0; font-size: 12px;">For security, this token is valid for one-time activation.</p>
        </div>
        """
        return self.send_email(to_email, subject, html_content)

    def send_membership_approval_email(self, to_email: str, name: str, society_name: str, unit_number: str) -> bool:
        login_link = f"{self.base_url}/signin"
        subject = f"Membership Approved - {society_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #276749;">Membership Approved! 🎉</h2>
            <p>Hi <strong>{name}</strong>,</p>
            <p>Your membership request for <strong>Unit {unit_number}</strong> in <strong>{society_name}</strong> has been approved by the Society Committee!</p>
            <p>You can now sign in to your dashboard to view notices, maintenance bills, and visitor passes.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_link}" style="background-color: #38a169; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Go to Dashboard</a>
            </div>
        </div>
        """
        return self.send_email(to_email, subject, html_content)

    def send_membership_rejection_email(self, to_email: str, name: str, society_name: str, reason: Optional[str] = None) -> bool:
        subject = f"Membership Update - {society_name}"
        reason_text = f"<p><strong>Reason provided:</strong> {reason}</p>" if reason else ""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #9b2c2c;">Membership Request Update</h2>
            <p>Hi <strong>{name}</strong>,</p>
            <p>Your membership request for <strong>{society_name}</strong> was not approved by the Society Committee at this time.</p>
            {reason_text}
            <p>If you believe this is an error, please contact your society committee member directly.</p>
        </div>
        """
        return self.send_email(to_email, subject, html_content)

    def send_society_lead_confirmation(self, to_email: str, contact_name: str, org_name: str) -> bool:
        subject = f"Society Registration Request Received - {org_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2b6cb0;">Registration Request Received</h2>
            <p>Hi <strong>{contact_name}</strong>,</p>
            <p>Thank you for registering your interest in bringing <strong>{org_name}</strong> to our Society Management Platform.</p>
            <p>Our platform onboarding team will review your details and contact you shortly to set up your subscription and provision your society dashboard.</p>
            <hr style="border: none; border-top: 1px solid #edf2f7; margin: 20px 0;">
            <p style="color: #718096; font-size: 14px;">Society Management SaaS Team</p>
        </div>
        """
        return self.send_email(to_email, subject, html_content)
