"""
Movement Repository - Data access layer for movement tracking.

Provides specialized queries for:
- Movements by inmate
- Movements by status
- Movements by date range
- Daily movement reports
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import MovementType, MovementStatus
from src.modules.movement.models import Movement


class MovementRepository(AsyncBaseRepository[Movement]):
    """Repository for Movement entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Movement, session)

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[Movement]:
        """Get all movements for an inmate."""
        query = select(Movement).where(Movement.inmate_id == inmate_id)

        if not include_deleted:
            query = query.where(Movement.is_deleted == False)  # noqa: E712

        query = query.order_by(Movement.scheduled_time.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: MovementStatus,
        include_deleted: bool = False
    ) -> List[Movement]:
        """Get all movements with a specific status."""
        query = select(Movement).where(Movement.status == status.value)

        if not include_deleted:
            query = query.where(Movement.is_deleted == False)  # noqa: E712

        query = query.order_by(Movement.scheduled_time.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scheduled_movements(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Movement]:
        """Get scheduled movements within a date range."""
        query = select(Movement).where(
            Movement.status == MovementStatus.SCHEDULED.value,
            Movement.is_deleted == False  # noqa: E712
        )

        if from_date:
            query = query.where(Movement.scheduled_time >= from_date)
        if to_date:
            query = query.where(Movement.scheduled_time <= to_date)

        query = query.order_by(Movement.scheduled_time.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_in_progress_movements(self) -> List[Movement]:
        """Get all movements currently in progress."""
        query = select(Movement).where(
            Movement.status == MovementStatus.IN_PROGRESS.value,
            Movement.is_deleted == False  # noqa: E712
        ).order_by(Movement.departure_time.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_movements_for_date(self, target_date: date) -> List[Movement]:
        """Get all movements scheduled for a specific date."""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        query = select(Movement).where(
            Movement.scheduled_time >= start_of_day,
            Movement.scheduled_time <= end_of_day,
            Movement.is_deleted == False  # noqa: E712
        ).order_by(Movement.scheduled_time.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_movements_by_type(
        self,
        movement_type: MovementType,
        include_deleted: bool = False
    ) -> List[Movement]:
        """Get all movements of a specific type."""
        query = select(Movement).where(Movement.movement_type == movement_type.value)

        if not include_deleted:
            query = query.where(Movement.is_deleted == False)  # noqa: E712

        query = query.order_by(Movement.scheduled_time.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_filtered_movements(
        self,
        inmate_id: Optional[UUID] = None,
        movement_type: Optional[MovementType] = None,
        status: Optional[MovementStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        escort_officer_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Movement]:
        """Get movements with multiple filters."""
        conditions = [Movement.is_deleted == False]  # noqa: E712

        if inmate_id:
            conditions.append(Movement.inmate_id == inmate_id)
        if movement_type:
            conditions.append(Movement.movement_type == movement_type.value)
        if status:
            conditions.append(Movement.status == status.value)
        if from_date:
            conditions.append(Movement.scheduled_time >= from_date)
        if to_date:
            conditions.append(Movement.scheduled_time <= to_date)
        if escort_officer_id:
            conditions.append(Movement.escort_officer_id == escort_officer_id)

        query = select(Movement).where(and_(*conditions))
        query = query.order_by(Movement.scheduled_time.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, inmate_id: Optional[UUID] = None) -> dict:
        """Count movements by status, optionally filtered by inmate."""
        result = {}
        for status in MovementStatus:
            query = select(func.count()).select_from(Movement).where(
                Movement.status == status.value,
                Movement.is_deleted == False  # noqa: E712
            )
            if inmate_id:
                query = query.where(Movement.inmate_id == inmate_id)

            count = await self.session.execute(query)
            result[status.value] = count.scalar() or 0

        return result

    async def count_by_type_for_date(self, target_date: date) -> dict:
        """Count movements by type for a specific date."""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        result = {}
        for movement_type in MovementType:
            query = select(func.count()).select_from(Movement).where(
                Movement.movement_type == movement_type.value,
                Movement.scheduled_time >= start_of_day,
                Movement.scheduled_time <= end_of_day,
                Movement.is_deleted == False  # noqa: E712
            )
            count = await self.session.execute(query)
            result[movement_type.value] = count.scalar() or 0

        return result

    async def has_active_movement(self, inmate_id: UUID) -> bool:
        """Check if inmate has an active (scheduled or in-progress) movement."""
        query = select(func.count()).select_from(Movement).where(
            Movement.inmate_id == inmate_id,
            Movement.status.in_([MovementStatus.SCHEDULED.value, MovementStatus.IN_PROGRESS.value]),
            Movement.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
