from fastapi import APIRouter
from app.complaints.routes.complaints import router as complaints_router

router = APIRouter()
router.include_router(complaints_router)

__all__ = ["router"]
