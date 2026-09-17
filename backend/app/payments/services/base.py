from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.repository import PaymentRepository
from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository


class BasePaymentService:
    """
    Base service providing dependency-injected repositories to payments domain services.
    """

    def __init__(
        self,
        db: AsyncSession,
        payment_repo: Optional[PaymentRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.db = db
        self.payment_repo = payment_repo or PaymentRepository(db)
        self.society_repo = society_repo or SocietyRepository(db)
        self.user_repo = user_repo or UserRepository(db)
