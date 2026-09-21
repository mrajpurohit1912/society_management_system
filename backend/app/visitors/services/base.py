from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.visitors.repository import VisitorRepository
from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository


class BaseVisitorService:
    """
    Base service providing dependency-injected repositories to visitor management services.
    """

    def __init__(
        self,
        db: AsyncSession,
        visitor_repo: Optional[VisitorRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.db = db
        self.visitor_repo = visitor_repo or VisitorRepository(db)
        self.society_repo = society_repo or SocietyRepository(db)
        self.user_repo = user_repo or UserRepository(db)
