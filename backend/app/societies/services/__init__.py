"""
Societies Domain Services Sub-Package.
Exports all domain services and repositories with backward compatibility.
"""

from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository

from app.societies.services.base import BaseSocietyService
from app.societies.services.society_service import SocietyService
from app.societies.services.building_service import BuildingService
from app.societies.services.floor_service import FloorService
from app.societies.services.unit_service import UnitService
from app.societies.services.resident_service import ResidentService
from app.societies.services.vehicle_service import VehicleService
from app.societies.services.bulk_provision_service import BulkProvisionService
from app.societies.services.membership_service import MembershipService

__all__ = [
    "BaseSocietyService",
    "SocietyService",
    "BuildingService",
    "FloorService",
    "UnitService",
    "ResidentService",
    "VehicleService",
    "BulkProvisionService",
    "MembershipService",
    "SocietyRepository",
    "UserRepository",
]
