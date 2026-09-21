from fastapi import APIRouter
from app.visitors.routes.passes import router as passes_router
from app.visitors.routes.gatekeeper import router as gatekeeper_router

router = APIRouter()
router.include_router(passes_router)
router.include_router(gatekeeper_router)

__all__ = ["router"]
