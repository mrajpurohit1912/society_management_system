from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.complaints.repository import ComplaintRepository
from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository


class BaseComplaintService:
    """
    Base service injecting repositories for the complaints & helpdesk domain.
    """

    def __init__(
        self,
        db: AsyncSession,
        complaint_repo: Optional[ComplaintRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.db = db
        self.complaint_repo = complaint_repo or ComplaintRepository(db)
        self.society_repo = society_repo or SocietyRepository(db)
        self.user_repo = user_repo or UserRepository(db)
