"""
Inmate Service - Business logic for inmate operations.

Handles booking number generation, validation, and orchestrates repository calls.
"""
from datetime import datetime
from typing import Optional, Tuple, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import InmateStatus, SecurityLevel
from src.modules.inmate.models import Inmate
from src.modules.inmate.repository import InmateRepository
from src.modules.inmate.dtos import InmateCreate, InmateUpdate, InmateResponse, InmateListResponse


class InmateServiceError(Exception):
    """Base exception for inmate service errors."""
    pass


class InmateNotFoundError(InmateServiceError):
    """Raised when an inmate is not found."""
    pass


class DuplicateBookingError(InmateServiceError):
    """Raised when trying to create a duplicate booking."""
    pass


class InmateService:
    """
    Service layer for Inmate operations.

    Encapsulates business logic including:
    - Auto-generation of booking numbers
    - Validation rules
    - Repository coordination
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = InmateRepository(session)

    async def create_inmate(
        self,
        data: InmateCreate,
        created_by: Optional[str] = None
    ) -> Inmate:
        """
        Create a new inmate during intake/booking.

        Auto-generates booking number in format: BDOCS-{year}-{5-digit-sequence}
        """
        # Generate booking number
        year = datetime.now().year
        sequence = await self.repository.get_next_booking_sequence(year)
        booking_number = f"BDOCS-{year}-{sequence:05d}"

        # Create inmate entity
        inmate = Inmate(
            booking_number=booking_number,
            nib_number=data.nib_number,
            first_name=data.first_name,
            middle_name=data.middle_name,
            last_name=data.last_name,
            aliases=data.aliases or [],
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            nationality=data.nationality,
            island_of_origin=data.island_of_origin,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            eye_color=data.eye_color,
            hair_color=data.hair_color,
            distinguishing_marks=data.distinguishing_marks,
            photo_url=data.photo_url,
            status=data.status,
            security_level=data.security_level,
            admission_date=data.admission_date or datetime.utcnow(),
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            emergency_contact_relationship=data.emergency_contact_relationship,
            inserted_by=created_by,
        )

        return await self.repository.create(inmate)

    async def update_inmate(
        self,
        inmate_id: UUID,
        data: InmateUpdate,
        updated_by: Optional[str] = None
    ) -> Inmate:
        """Update an existing inmate's information."""
        inmate = await self.repository.get_by_id(inmate_id)
        if not inmate:
            raise InmateNotFoundError(f"Inmate with ID {inmate_id} not found")

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inmate, field, value)

        inmate.updated_by = updated_by
        return await self.repository.update(inmate)

    async def get_inmate_by_id(self, inmate_id: UUID) -> Inmate:
        """Get inmate by UUID."""
        inmate = await self.repository.get_by_id(inmate_id)
        if not inmate or inmate.is_deleted:
            raise InmateNotFoundError(f"Inmate with ID {inmate_id} not found")
        return inmate

    async def get_inmate_by_booking_number(self, booking_number: str) -> Inmate:
        """Get inmate by booking number."""
        inmate = await self.repository.get_by_booking_number(booking_number)
        if not inmate:
            raise InmateNotFoundError(f"Inmate with booking number {booking_number} not found")
        return inmate

    async def search_inmates(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> InmateListResponse:
        """Search inmates by name or booking number."""
        skip = (page - 1) * page_size
        inmates, total = await self.repository.search_by_name(query, skip, page_size)

        return InmateListResponse(
            items=[InmateResponse.model_validate(i) for i in inmates],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )

    async def list_inmates(
        self,
        status: Optional[InmateStatus] = None,
        security_level: Optional[SecurityLevel] = None,
        page: int = 1,
        page_size: int = 20
    ) -> InmateListResponse:
        """List inmates with optional filters and pagination."""
        skip = (page - 1) * page_size
        inmates, total = await self.repository.list_with_filters(
            status=status,
            security_level=security_level,
            skip=skip,
            limit=page_size
        )

        return InmateListResponse(
            items=[InmateResponse.model_validate(i) for i in inmates],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )

    async def get_active_inmates(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> InmateListResponse:
        """Get inmates currently in custody."""
        skip = (page - 1) * page_size
        inmates, total = await self.repository.get_active_inmates(skip, page_size)

        return InmateListResponse(
            items=[InmateResponse.model_validate(i) for i in inmates],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )

    async def soft_delete_inmate(
        self,
        inmate_id: UUID,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Soft delete an inmate record (sets is_deleted=True)."""
        inmate = await self.repository.get_by_id(inmate_id)
        if not inmate:
            raise InmateNotFoundError(f"Inmate with ID {inmate_id} not found")

        inmate.is_deleted = True
        inmate.deleted_at = datetime.utcnow()
        inmate.deleted_by = deleted_by
        await self.repository.update(inmate)
        return True

    async def get_population_stats(self) -> dict:
        """Get basic population statistics."""
        remand_inmates, remand_total = await self.repository.get_by_status(
            InmateStatus.REMAND, limit=1
        )
        sentenced_inmates, sentenced_total = await self.repository.get_by_status(
            InmateStatus.SENTENCED, limit=1
        )

        total_active = remand_total + sentenced_total

        return {
            "total_active": total_active,
            "remand_count": remand_total,
            "sentenced_count": sentenced_total,
            "remand_percentage": round(remand_total / total_active * 100, 1) if total_active > 0 else 0,
        }
