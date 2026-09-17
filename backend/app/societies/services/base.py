"""
Base service abstraction for society management services.
Provides common database session and repository access.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.societies import services as services_pkg


class BaseSocietyService:
    """Base domain service providing database session and repository access."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = services_pkg.SocietyRepository(db)
