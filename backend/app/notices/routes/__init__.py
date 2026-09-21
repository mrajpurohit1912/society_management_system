from fastapi import APIRouter
from app.notices.routes.notices import router as notices_router

router = APIRouter()
router.include_router(notices_router)

__all__ = ["router"]
