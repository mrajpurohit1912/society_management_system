from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.notices.repository import NoticeRepository
from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository


class BaseNoticeService:
    """
    Base service injecting repositories for the notices & communications domain.
    """

    def __init__(
        self,
        db: AsyncSession,
        notice_repo: Optional[NoticeRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.db = db
        self.notice_repo = notice_repo or NoticeRepository(db)
        self.society_repo = society_repo or SocietyRepository(db)
        self.user_repo = user_repo or UserRepository(db)
