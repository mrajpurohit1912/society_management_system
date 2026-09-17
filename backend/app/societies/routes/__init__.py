"""
Societies Routes Sub-Package.
Combines sub-domain routers into the central societies APIRouter.
"""

from fastapi import APIRouter

# Backward compatibility exports for tests and legacy callers
from app.societies.services import (
    SocietyService,
    BuildingService,
    FloorService,
    UnitService,
    ResidentService,
    VehicleService,
    BulkProvisionService,
    MembershipService,
)

from app.societies.routes.memberships import router as memberships_router
from app.societies.routes.societies import router as societies_crud_router
from app.societies.routes.buildings import router as buildings_router
from app.societies.routes.units import router as units_router
from app.societies.routes.residents import router as residents_router

router = APIRouter(tags=["Society & Membership Management"])

# Mount sub-routers in order
router.include_router(memberships_router)
router.include_router(societies_crud_router)
router.include_router(buildings_router)
router.include_router(units_router)
router.include_router(residents_router)

__all__ = [
    "router",
    "SocietyService",
    "BuildingService",
    "FloorService",
    "UnitService",
    "ResidentService",
    "VehicleService",
    "BulkProvisionService",
    "MembershipService",
]
