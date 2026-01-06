"""
Housing Repository - Data access layer for housing operations.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import SecurityLevel
from src.modules.housing.models import HousingUnit, Classification, HousingAssignment
from src.modules.inmate.models import Inmate


class HousingUnitRepository:
    """Repository for HousingUnit operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, include_inactive: bool = False) -> List[HousingUnit]:
        """Get all housing units."""
        query = select(HousingUnit)
        if not include_inactive:
            query = query.where(HousingUnit.is_active == True)  # noqa: E712
        query = query.order_by(HousingUnit.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, unit_id: UUID) -> Optional[HousingUnit]:
        """Get housing unit by ID."""
        result = await self.session.execute(
            select(HousingUnit).where(HousingUnit.id == unit_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[HousingUnit]:
        """Get housing unit by code."""
        result = await self.session.execute(
            select(HousingUnit).where(HousingUnit.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def create(self, unit: HousingUnit) -> HousingUnit:
        """Create a new housing unit."""
        self.session.add(unit)
        await self.session.flush()
        await self.session.refresh(unit)
        return unit

    async def update(self, unit: HousingUnit) -> HousingUnit:
        """Update housing unit."""
        await self.session.flush()
        await self.session.refresh(unit)
        return unit

    async def get_overcrowded(self) -> List[HousingUnit]:
        """Get all overcrowded units."""
        result = await self.session.execute(
            select(HousingUnit).where(
                and_(
                    HousingUnit.is_active == True,  # noqa: E712
                    HousingUnit.current_occupancy > HousingUnit.capacity
                )
            ).order_by(HousingUnit.code)
        )
        return list(result.scalars().all())

    async def get_by_security_level(self, level: SecurityLevel) -> List[HousingUnit]:
        """Get units by security level."""
        result = await self.session.execute(
            select(HousingUnit).where(
                and_(
                    HousingUnit.security_level == level,
                    HousingUnit.is_active == True  # noqa: E712
                )
            ).order_by(HousingUnit.code)
        )
        return list(result.scalars().all())

    async def increment_occupancy(self, unit_id: UUID) -> None:
        """Increment unit occupancy count."""
        await self.session.execute(
            update(HousingUnit)
            .where(HousingUnit.id == unit_id)
            .values(current_occupancy=HousingUnit.current_occupancy + 1)
        )

    async def decrement_occupancy(self, unit_id: UUID) -> None:
        """Decrement unit occupancy count."""
        await self.session.execute(
            update(HousingUnit)
            .where(HousingUnit.id == unit_id)
            .values(current_occupancy=func.greatest(0, HousingUnit.current_occupancy - 1))
        )

    async def get_facility_stats(self) -> dict:
        """Get facility-wide statistics."""
        result = await self.session.execute(
            select(
                func.sum(HousingUnit.capacity).label('total_capacity'),
                func.sum(HousingUnit.current_occupancy).label('total_population')
            ).where(HousingUnit.is_active == True)  # noqa: E712
        )
        row = result.one()
        return {
            'total_capacity': row.total_capacity or 0,
            'total_population': row.total_population or 0
        }


class ClassificationRepository:
    """Repository for Classification operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, classification: Classification) -> Classification:
        """Create new classification."""
        # Mark previous classifications as not current
        await self.session.execute(
            update(Classification)
            .where(
                and_(
                    Classification.inmate_id == classification.inmate_id,
                    Classification.is_current == True  # noqa: E712
                )
            )
            .values(is_current=False)
        )

        self.session.add(classification)
        await self.session.flush()
        await self.session.refresh(classification)
        return classification

    async def get_by_id(self, classification_id: UUID) -> Optional[Classification]:
        """Get classification by ID."""
        result = await self.session.execute(
            select(Classification).where(
                and_(
                    Classification.id == classification_id,
                    Classification.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_current_for_inmate(self, inmate_id: UUID) -> Optional[Classification]:
        """Get current classification for an inmate."""
        result = await self.session.execute(
            select(Classification).where(
                and_(
                    Classification.inmate_id == inmate_id,
                    Classification.is_current == True,  # noqa: E712
                    Classification.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_history_for_inmate(self, inmate_id: UUID) -> List[Classification]:
        """Get all classifications for an inmate."""
        result = await self.session.execute(
            select(Classification).where(
                and_(
                    Classification.inmate_id == inmate_id,
                    Classification.is_deleted == False  # noqa: E712
                )
            ).order_by(Classification.classification_date.desc())
        )
        return list(result.scalars().all())

    async def get_pending_reviews(self, before_date) -> List[Classification]:
        """Get classifications with pending reviews."""
        result = await self.session.execute(
            select(Classification).where(
                and_(
                    Classification.review_date <= before_date,
                    Classification.is_current == True,  # noqa: E712
                    Classification.is_deleted == False  # noqa: E712
                )
            ).order_by(Classification.review_date)
        )
        return list(result.scalars().all())


class HousingAssignmentRepository:
    """Repository for HousingAssignment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, assignment: HousingAssignment) -> HousingAssignment:
        """Create new housing assignment."""
        # End previous current assignment
        await self.session.execute(
            update(HousingAssignment)
            .where(
                and_(
                    HousingAssignment.inmate_id == assignment.inmate_id,
                    HousingAssignment.is_current == True  # noqa: E712
                )
            )
            .values(is_current=False, end_date=datetime.utcnow())
        )

        self.session.add(assignment)
        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment

    async def get_by_id(self, assignment_id: UUID) -> Optional[HousingAssignment]:
        """Get assignment by ID."""
        result = await self.session.execute(
            select(HousingAssignment).where(
                and_(
                    HousingAssignment.id == assignment_id,
                    HousingAssignment.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_current_for_inmate(self, inmate_id: UUID) -> Optional[HousingAssignment]:
        """Get current housing assignment for an inmate."""
        result = await self.session.execute(
            select(HousingAssignment).where(
                and_(
                    HousingAssignment.inmate_id == inmate_id,
                    HousingAssignment.is_current == True,  # noqa: E712
                    HousingAssignment.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_history_for_inmate(self, inmate_id: UUID) -> List[HousingAssignment]:
        """Get all housing assignments for an inmate."""
        result = await self.session.execute(
            select(HousingAssignment).where(
                and_(
                    HousingAssignment.inmate_id == inmate_id,
                    HousingAssignment.is_deleted == False  # noqa: E712
                )
            ).order_by(HousingAssignment.assigned_date.desc())
        )
        return list(result.scalars().all())

    async def get_inmates_in_unit(self, unit_id: UUID) -> List[HousingAssignment]:
        """Get all current assignments for a housing unit."""
        result = await self.session.execute(
            select(HousingAssignment).where(
                and_(
                    HousingAssignment.housing_unit_id == unit_id,
                    HousingAssignment.is_current == True,  # noqa: E712
                    HousingAssignment.is_deleted == False  # noqa: E712
                )
            ).order_by(HousingAssignment.cell_number, HousingAssignment.bed_number)
        )
        return list(result.scalars().all())

    async def end_assignment(
        self,
        assignment_id: UUID,
        reason: Optional[str] = None
    ) -> Optional[HousingAssignment]:
        """End a housing assignment."""
        assignment = await self.get_by_id(assignment_id)
        if not assignment or not assignment.is_current:
            return None

        assignment.is_current = False
        assignment.end_date = datetime.utcnow()
        if reason:
            assignment.reason = reason

        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment

    async def update(self, assignment: HousingAssignment) -> HousingAssignment:
        """Update assignment."""
        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment
