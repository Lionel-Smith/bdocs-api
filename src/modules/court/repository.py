"""
Court Repository - Data access layer for court cases and appearances.

Provides specialized queries for:
- Cases by inmate, status, court type
- Appearances by date range, upcoming
- Case-appearance relationships
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import CourtType, CaseStatus, AppearanceType, AppearanceOutcome
from src.modules.court.models import CourtCase, CourtAppearance


class CourtCaseRepository(AsyncBaseRepository[CourtCase]):
    """Repository for CourtCase entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CourtCase, session)

    async def get_by_case_number(self, case_number: str) -> Optional[CourtCase]:
        """Get court case by case number."""
        query = select(CourtCase).where(
            CourtCase.case_number == case_number.upper(),
            CourtCase.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[CourtCase]:
        """Get all cases for an inmate."""
        query = select(CourtCase).where(CourtCase.inmate_id == inmate_id)

        if not include_deleted:
            query = query.where(CourtCase.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtCase.filing_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: CaseStatus,
        include_deleted: bool = False
    ) -> List[CourtCase]:
        """Get cases by status."""
        query = select(CourtCase).where(CourtCase.status == status.value)

        if not include_deleted:
            query = query.where(CourtCase.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtCase.filing_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_court_type(
        self,
        court_type: CourtType,
        include_deleted: bool = False
    ) -> List[CourtCase]:
        """Get cases by court type."""
        query = select(CourtCase).where(CourtCase.court_type == court_type.value)

        if not include_deleted:
            query = query.where(CourtCase.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtCase.filing_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_cases(self, inmate_id: Optional[UUID] = None) -> List[CourtCase]:
        """Get active cases, optionally filtered by inmate."""
        query = select(CourtCase).where(
            CourtCase.status.in_([CaseStatus.PENDING.value, CaseStatus.ACTIVE.value]),
            CourtCase.is_deleted == False  # noqa: E712
        )

        if inmate_id:
            query = query.where(CourtCase.inmate_id == inmate_id)

        query = query.order_by(CourtCase.filing_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_inmate_and_status(
        self,
        inmate_id: UUID,
        status: Optional[CaseStatus] = None
    ) -> int:
        """Count cases for an inmate, optionally by status."""
        query = select(func.count()).select_from(CourtCase).where(
            CourtCase.inmate_id == inmate_id,
            CourtCase.is_deleted == False  # noqa: E712
        )

        if status:
            query = query.where(CourtCase.status == status.value)

        result = await self.session.execute(query)
        return result.scalar() or 0


class CourtAppearanceRepository(AsyncBaseRepository[CourtAppearance]):
    """Repository for CourtAppearance entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CourtAppearance, session)

    async def get_by_case(
        self,
        court_case_id: UUID,
        include_deleted: bool = False
    ) -> List[CourtAppearance]:
        """Get all appearances for a court case."""
        query = select(CourtAppearance).where(
            CourtAppearance.court_case_id == court_case_id
        )

        if not include_deleted:
            query = query.where(CourtAppearance.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtAppearance.appearance_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[CourtAppearance]:
        """Get all appearances for an inmate."""
        query = select(CourtAppearance).where(
            CourtAppearance.inmate_id == inmate_id
        )

        if not include_deleted:
            query = query.where(CourtAppearance.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtAppearance.appearance_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_appearances(
        self,
        days_ahead: int = 7,
        inmate_id: Optional[UUID] = None
    ) -> List[CourtAppearance]:
        """Get upcoming appearances (no outcome yet)."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        query = select(CourtAppearance).where(
            CourtAppearance.appearance_date >= now,
            CourtAppearance.appearance_date <= end_date,
            CourtAppearance.outcome == None,  # noqa: E711
            CourtAppearance.is_deleted == False  # noqa: E712
        )

        if inmate_id:
            query = query.where(CourtAppearance.inmate_id == inmate_id)

        query = query.order_by(CourtAppearance.appearance_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
        include_deleted: bool = False
    ) -> List[CourtAppearance]:
        """Get appearances within a date range."""
        query = select(CourtAppearance).where(
            CourtAppearance.appearance_date >= from_date,
            CourtAppearance.appearance_date <= to_date
        )

        if not include_deleted:
            query = query.where(CourtAppearance.is_deleted == False)  # noqa: E712

        query = query.order_by(CourtAppearance.appearance_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_appearances_for_date(
        self,
        target_date: date
    ) -> List[CourtAppearance]:
        """Get all appearances for a specific date."""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        query = select(CourtAppearance).where(
            CourtAppearance.appearance_date >= start_of_day,
            CourtAppearance.appearance_date <= end_of_day,
            CourtAppearance.is_deleted == False  # noqa: E712
        ).order_by(CourtAppearance.appearance_date.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_upcoming(self, inmate_id: Optional[UUID] = None) -> int:
        """Count upcoming appearances without outcomes."""
        query = select(func.count()).select_from(CourtAppearance).where(
            CourtAppearance.appearance_date >= datetime.utcnow(),
            CourtAppearance.outcome == None,  # noqa: E711
            CourtAppearance.is_deleted == False  # noqa: E712
        )

        if inmate_id:
            query = query.where(CourtAppearance.inmate_id == inmate_id)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_by_movement(self, movement_id: UUID) -> Optional[CourtAppearance]:
        """Get appearance linked to a movement."""
        query = select(CourtAppearance).where(
            CourtAppearance.movement_id == movement_id,
            CourtAppearance.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
