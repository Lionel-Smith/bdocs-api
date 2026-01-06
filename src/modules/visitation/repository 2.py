"""
Visitation Repository - Data access layer for visitation management.

Handles database operations for ApprovedVisitor, VisitSchedule, and VisitLog entities.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.visitation.models import ApprovedVisitor, VisitSchedule, VisitLog
from src.common.enums import (
    Relationship, CheckStatus, VisitType, VisitStatus
)


class ApprovedVisitorRepository:
    """Repository for ApprovedVisitor operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, visitor: ApprovedVisitor) -> ApprovedVisitor:
        """Create a new visitor record."""
        self.session.add(visitor)
        await self.session.flush()
        await self.session.refresh(visitor)
        return visitor

    async def get_by_id(self, visitor_id: UUID) -> Optional[ApprovedVisitor]:
        """Get visitor by ID."""
        result = await self.session.execute(
            select(ApprovedVisitor)
            .where(and_(
                ApprovedVisitor.id == visitor_id,
                ApprovedVisitor.is_deleted == False
            ))
            .options(
                selectinload(ApprovedVisitor.inmate),
                selectinload(ApprovedVisitor.approver)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        approved_only: bool = False,
        active_only: bool = True
    ) -> List[ApprovedVisitor]:
        """Get all visitors registered for an inmate."""
        query = select(ApprovedVisitor).where(and_(
            ApprovedVisitor.inmate_id == inmate_id,
            ApprovedVisitor.is_deleted == False
        ))

        if approved_only:
            query = query.where(ApprovedVisitor.is_approved == True)
        if active_only:
            query = query.where(ApprovedVisitor.is_active == True)

        query = query.order_by(ApprovedVisitor.last_name, ApprovedVisitor.first_name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        check_status: Optional[CheckStatus] = None,
        is_approved: Optional[bool] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ApprovedVisitor]:
        """Get all visitors with optional filters."""
        query = select(ApprovedVisitor).where(ApprovedVisitor.is_deleted == False)

        if check_status:
            query = query.where(ApprovedVisitor.background_check_status == check_status)
        if is_approved is not None:
            query = query.where(ApprovedVisitor.is_approved == is_approved)
        if is_active is not None:
            query = query.where(ApprovedVisitor.is_active == is_active)

        query = query.options(selectinload(ApprovedVisitor.inmate))
        query = query.order_by(ApprovedVisitor.last_name, ApprovedVisitor.first_name)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approval(self) -> List[ApprovedVisitor]:
        """Get visitors pending background check approval."""
        result = await self.session.execute(
            select(ApprovedVisitor)
            .where(and_(
                ApprovedVisitor.background_check_status == CheckStatus.PENDING,
                ApprovedVisitor.is_deleted == False,
                ApprovedVisitor.is_active == True
            ))
            .options(selectinload(ApprovedVisitor.inmate))
            .order_by(ApprovedVisitor.inserted_date)
        )
        return list(result.scalars().all())

    async def update(self, visitor: ApprovedVisitor) -> ApprovedVisitor:
        """Update a visitor record."""
        await self.session.flush()
        await self.session.refresh(visitor)
        return visitor

    async def soft_delete(self, visitor: ApprovedVisitor) -> ApprovedVisitor:
        """Soft delete a visitor record."""
        visitor.is_deleted = True
        visitor.deleted_at = datetime.utcnow()
        visitor.is_active = False
        await self.session.flush()
        return visitor

    async def count(
        self,
        is_approved: Optional[bool] = None,
        is_active: Optional[bool] = None,
        check_status: Optional[CheckStatus] = None
    ) -> int:
        """Count visitors with optional filters."""
        query = select(func.count(ApprovedVisitor.id)).where(
            ApprovedVisitor.is_deleted == False
        )

        if is_approved is not None:
            query = query.where(ApprovedVisitor.is_approved == is_approved)
        if is_active is not None:
            query = query.where(ApprovedVisitor.is_active == is_active)
        if check_status:
            query = query.where(ApprovedVisitor.background_check_status == check_status)

        result = await self.session.execute(query)
        return result.scalar() or 0


class VisitScheduleRepository:
    """Repository for VisitSchedule operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, schedule: VisitSchedule) -> VisitSchedule:
        """Create a new visit schedule."""
        self.session.add(schedule)
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def get_by_id(self, schedule_id: UUID) -> Optional[VisitSchedule]:
        """Get visit schedule by ID."""
        result = await self.session.execute(
            select(VisitSchedule)
            .where(VisitSchedule.id == schedule_id)
            .options(
                selectinload(VisitSchedule.inmate),
                selectinload(VisitSchedule.visitor),
                selectinload(VisitSchedule.creator),
                selectinload(VisitSchedule.visit_log)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date(
        self,
        visit_date: date,
        status: Optional[VisitStatus] = None,
        visit_type: Optional[VisitType] = None
    ) -> List[VisitSchedule]:
        """Get all visits scheduled for a date."""
        query = select(VisitSchedule).where(VisitSchedule.scheduled_date == visit_date)

        if status:
            query = query.where(VisitSchedule.status == status)
        if visit_type:
            query = query.where(VisitSchedule.visit_type == visit_type)

        query = query.options(
            selectinload(VisitSchedule.inmate),
            selectinload(VisitSchedule.visitor),
            selectinload(VisitSchedule.visit_log)
        )
        query = query.order_by(VisitSchedule.scheduled_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[VisitSchedule]:
        """Get visits for an inmate."""
        query = select(VisitSchedule).where(VisitSchedule.inmate_id == inmate_id)

        if start_date:
            query = query.where(VisitSchedule.scheduled_date >= start_date)
        if end_date:
            query = query.where(VisitSchedule.scheduled_date <= end_date)

        query = query.options(selectinload(VisitSchedule.visitor))
        query = query.order_by(VisitSchedule.scheduled_date.desc(), VisitSchedule.scheduled_time)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_visitor(
        self,
        visitor_id: UUID,
        upcoming_only: bool = False
    ) -> List[VisitSchedule]:
        """Get visits for a visitor."""
        query = select(VisitSchedule).where(VisitSchedule.visitor_id == visitor_id)

        if upcoming_only:
            today = date.today()
            query = query.where(and_(
                VisitSchedule.scheduled_date >= today,
                VisitSchedule.status == VisitStatus.SCHEDULED
            ))

        query = query.options(selectinload(VisitSchedule.inmate))
        query = query.order_by(VisitSchedule.scheduled_date, VisitSchedule.scheduled_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def check_conflict(
        self,
        inmate_id: UUID,
        visit_date: date,
        start_time: time,
        duration_minutes: int,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if there's a conflicting visit for the inmate.

        Returns True if a conflict exists.
        """
        # Calculate end time
        start_dt = datetime.combine(visit_date, start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.time()

        query = select(VisitSchedule).where(and_(
            VisitSchedule.inmate_id == inmate_id,
            VisitSchedule.scheduled_date == visit_date,
            VisitSchedule.status.in_([VisitStatus.SCHEDULED, VisitStatus.CHECKED_IN, VisitStatus.IN_PROGRESS])
        ))

        if exclude_id:
            query = query.where(VisitSchedule.id != exclude_id)

        result = await self.session.execute(query)
        existing_visits = list(result.scalars().all())

        for visit in existing_visits:
            visit_start = visit.scheduled_time
            visit_end_dt = datetime.combine(visit_date, visit_start) + timedelta(minutes=visit.duration_minutes)
            visit_end = visit_end_dt.time()

            # Check for overlap
            if not (end_time <= visit_start or start_time >= visit_end):
                return True

        return False

    async def update(self, schedule: VisitSchedule) -> VisitSchedule:
        """Update a visit schedule."""
        await self.session.flush()
        await self.session.refresh(schedule)
        return schedule

    async def delete(self, schedule: VisitSchedule) -> None:
        """Hard delete a visit schedule."""
        await self.session.delete(schedule)
        await self.session.flush()

    async def count_by_date(
        self,
        visit_date: date,
        status: Optional[VisitStatus] = None
    ) -> int:
        """Count visits for a date."""
        query = select(func.count(VisitSchedule.id)).where(
            VisitSchedule.scheduled_date == visit_date
        )

        if status:
            query = query.where(VisitSchedule.status == status)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_status(self, visit_date: date) -> dict:
        """Get visit counts by status for a date."""
        result = await self.session.execute(
            select(VisitSchedule.status, func.count(VisitSchedule.id))
            .where(VisitSchedule.scheduled_date == visit_date)
            .group_by(VisitSchedule.status)
        )
        return {row[0].value: row[1] for row in result.all()}


class VisitLogRepository:
    """Repository for VisitLog operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: VisitLog) -> VisitLog:
        """Create a new visit log."""
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: UUID) -> Optional[VisitLog]:
        """Get visit log by ID."""
        result = await self.session.execute(
            select(VisitLog)
            .where(VisitLog.id == log_id)
            .options(
                selectinload(VisitLog.visit_schedule),
                selectinload(VisitLog.processor),
                selectinload(VisitLog.incident)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_schedule(self, schedule_id: UUID) -> Optional[VisitLog]:
        """Get visit log by schedule ID."""
        result = await self.session.execute(
            select(VisitLog)
            .where(VisitLog.visit_schedule_id == schedule_id)
            .options(selectinload(VisitLog.processor))
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[VisitLog]:
        """Get visit logs for a date range."""
        result = await self.session.execute(
            select(VisitLog)
            .where(and_(
                VisitLog.checked_in_at >= start_date,
                VisitLog.checked_in_at <= end_date
            ))
            .options(
                selectinload(VisitLog.visit_schedule),
                selectinload(VisitLog.processor)
            )
            .order_by(VisitLog.checked_in_at)
        )
        return list(result.scalars().all())

    async def update(self, log: VisitLog) -> VisitLog:
        """Update a visit log."""
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def count_contraband_incidents(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count visits where contraband was found."""
        result = await self.session.execute(
            select(func.count(VisitLog.id))
            .where(and_(
                VisitLog.checked_in_at >= start_date,
                VisitLog.checked_in_at <= end_date,
                VisitLog.contraband_found == True
            ))
        )
        return result.scalar() or 0

    async def count_searched_today(self, today: date) -> int:
        """Count visitors searched today."""
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        result = await self.session.execute(
            select(func.count(VisitLog.id))
            .where(and_(
                VisitLog.checked_in_at >= start,
                VisitLog.checked_in_at <= end,
                VisitLog.visitor_searched == True
            ))
        )
        return result.scalar() or 0

    async def get_average_duration(self, visit_date: date) -> float:
        """Get average visit duration for a date."""
        start = datetime.combine(visit_date, time.min)
        end = datetime.combine(visit_date, time.max)

        result = await self.session.execute(
            select(VisitLog)
            .where(and_(
                VisitLog.checked_in_at >= start,
                VisitLog.checked_in_at <= end,
                VisitLog.checked_out_at.isnot(None)
            ))
        )
        logs = list(result.scalars().all())

        if not logs:
            return 0.0

        total_duration = sum(
            (log.checked_out_at - log.checked_in_at).total_seconds() / 60
            for log in logs if log.checked_out_at
        )
        return round(total_duration / len(logs), 1)
