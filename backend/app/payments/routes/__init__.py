from fastapi import APIRouter
from app.payments.routes.invoices import router as invoices_router
from app.payments.routes.transactions import router as transactions_router

router = APIRouter()
router.include_router(invoices_router)
router.include_router(transactions_router)

__all__ = ["router"]
