from typing import Dict, Type, Optional
import structlog

from app.core.config import settings
from app.core.providers.email.base import AbstractEmailProvider
from app.core.providers.email.adapters.resend import ResendEmailProvider
from app.core.providers.email.adapters.console import ConsoleEmailProvider
from app.core.providers.email.adapters.sendgrid import SendGridEmailProvider

logger = structlog.get_logger(__name__)

class EmailProviderFactory:
    """
    Factory & Registry for resolving Email Strategy Adapters dynamically at runtime based on environment config.
    """
    _providers: Dict[str, Type[AbstractEmailProvider]] = {
        "resend": ResendEmailProvider,
        "console": ConsoleEmailProvider,
        "sendgrid": SendGridEmailProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> AbstractEmailProvider:
        target = (provider_name or settings.EMAIL_PROVIDER).lower()
        provider_cls = cls._providers.get(target)

        if not provider_cls:
            logger.warning("email_factory.unknown_provider", target=target, fallback="console")
            return ConsoleEmailProvider(base_url=settings.APP_BASE_URL)

        if target == "resend":
            return ResendEmailProvider(
                api_key=settings.RESEND_API_KEY,
                from_email=settings.EMAIL_FROM,
                base_url=settings.APP_BASE_URL
            )
        elif target == "sendgrid":
            return SendGridEmailProvider(
                api_key=settings.SENDGRID_API_KEY or "",
                from_email=settings.EMAIL_FROM,
                base_url=settings.APP_BASE_URL
            )
        else:
            return ConsoleEmailProvider(base_url=settings.APP_BASE_URL)
