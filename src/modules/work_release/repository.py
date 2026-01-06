"""
Work Release Repository - Data access layer for work release operations.

Three repository classes for separation of concerns:
- WorkReleaseEmployerRepository: Employer CRUD and approval queries
- WorkReleaseAssignmentRepository: Assignment lifecycle management
- WorkReleaseLogRepository: Daily departure/return logging

Key queries:
- Active assignments by status
- Unresolved logs (departed but not returned)
- Daily activity reports
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.work_release.models import (
    WorkReleaseEmployer,
    WorkReleaseAssignment,
    WorkReleaseLog
)
from src.common.enums import WorkReleaseStatus, LogStatus


class WorkReleaseEmployerRepository:
    """Repository for work release employer operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, employer: WorkReleaseEmployer) -> WorkReleaseEmployer:
        """Create a new employer."""
        self.session.add(employer)
        await self.session.flush()
        return employer

    async def get_by_id(self, employer_id: UUID) -> Optional[WorkReleaseEmployer]:
        """Get employer by ID."""
        query = select(WorkReleaseEmployer).where(
            WorkReleaseEmployer.id == employer_id,
            WorkReleaseEmployer.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        approved_only: bool = False,
        active_only: bool = False
    ) -> List[WorkReleaseEmployer]:
        """Get all employers with optional filters."""
        query = select(WorkReleaseEmployer).where(
            WorkReleaseEmployer.is_deleted == False
        )

        if approved_only:
            query = query.where(WorkReleaseEmployer.is_approved == True)

        if active_only:
            query = query.where(WorkReleaseEmployer.is_active == True)

        query = query.order_by(WorkReleaseEmployer.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_accepting_inmates(self) -> List[WorkReleaseEmployer]:
        """Get employers that can currently accept new inmates."""
        today = date.today()
        query = select(WorkReleaseEmployer).where(
            WorkReleaseEmployer.is_deleted == False,
            WorkReleaseEmployer.is_approved == True,
            WorkReleaseEmployer.is_active == True,
            WorkReleaseEmployer.mou_signed == True,
            or_(
                WorkReleaseEmployer.mou_expiry_date == None,
                WorkReleaseEmployer.mou_expiry_date > today
            )
        ).order_by(WorkReleaseEmployer.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, employer: WorkReleaseEmployer) -> WorkReleaseEmployer:
        """Update an employer."""
        await self.session.flush()
        return employer

    async def soft_delete(self, employer: WorkReleaseEmployer) -> bool:
        """Soft delete an employer."""
        employer.is_deleted = True
        employer.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def count_by_approval_status(self) -> dict:
        """Count employers by approval status."""
        query = select(
            WorkReleaseEmployer.is_approved,
            func.count(WorkReleaseEmployer.id)
        ).where(
            WorkReleaseEmployer.is_deleted == False
        ).group_by(WorkReleaseEmployer.is_approved)

        result = await self.session.execute(query)
        counts = {row[0]: row[1] for row in result.all()}
        return {
            'approved': counts.get(True, 0),
            'pending': counts.get(False, 0),
            'total': sum(counts.values())
        }


class WorkReleaseAssignmentRepository:
    """Repository for work release assignment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, assignment: WorkReleaseAssignment) -> WorkReleaseAssignment:
        """Create a new assignment."""
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get_by_id(
        self,
        assignment_id: UUID,
        include_employer: bool = True
    ) -> Optional[WorkReleaseAssignment]:
        """Get assignment by ID with optional employer details."""
        query = select(WorkReleaseAssignment).where(
            WorkReleaseAssignment.id == assignment_id,
            WorkReleaseAssignment.is_deleted == False
        )

        if include_employer:
            query = query.options(selectinload(WorkReleaseAssignment.employer))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        active_only: bool = False
    ) -> List[WorkReleaseAssignment]:
        """Get assignments for an inmate."""
        query = select(WorkReleaseAssignment).where(
            WorkReleaseAssignment.inmate_id == inmate_id,
            WorkReleaseAssignment.is_deleted == False
        ).options(selectinload(WorkReleaseAssignment.employer))

        if active_only:
            query = query.where(
                WorkReleaseAssignment.status == WorkReleaseStatus.ACTIVE.value
            )

        query = query.order_by(WorkReleaseAssignment.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_assignment(
        self,
        inmate_id: UUID
    ) -> Optional[WorkReleaseAssignment]:
        """Get the current active assignment for an inmate."""
        query = select(WorkReleaseAssignment).where(
            WorkReleaseAssignment.inmate_id == inmate_id,
            WorkReleaseAssignment.status == WorkReleaseStatus.ACTIVE.value,
            WorkReleaseAssignment.is_deleted == False
        ).options(selectinload(WorkReleaseAssignment.employer))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_employer(
        self,
        employer_id: UUID,
        active_only: bool = False
    ) -> List[WorkReleaseAssignment]:
        """Get assignments for an employer."""
        query = select(WorkReleaseAssignment).where(
            WorkReleaseAssignment.employer_id == employer_id,
            WorkReleaseAssignment.is_deleted == False
        ).options(selectinload(WorkReleaseAssignment.inmate))

        if active_only:
            query = query.where(
                WorkReleaseAssignment.status == WorkReleaseStatus.ACTIVE.value
            )

        query = query.order_by(WorkReleaseAssignment.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[WorkReleaseAssignment]:
        """Get all assignments with a specific status."""
        query = select(WorkReleaseAssignment).where(
            WorkReleaseAssignment.status == status,
            WorkReleaseAssignment.is_deleted == False
        ).options(
            selectinload(WorkReleaseAssignment.employer),
            selectinload(WorkReleaseAssignment.inmate)
        ).order_by(WorkReleaseAssignment.start_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approval(self) -> List[WorkReleaseAssignment]:
        """Get assignments pending approval."""
        return await self.get_by_status(WorkReleaseStatus.PENDING_APPROVAL.value)

    async def get_all_active(self) -> List[WorkReleaseAssignment]:
        """Get all active work release assignments."""
        return await self.get_by_status(WorkReleaseStatus.ACTIVE.value)

    async def update(self, assignment: WorkReleaseAssignment) -> WorkReleaseAssignment:
        """Update an assignment."""
        await self.session.flush()
        return assignment

    async def soft_delete(self, assignment: WorkReleaseAssignment) -> bool:
        """Soft delete an assignment."""
        assignment.is_deleted = True
        assignment.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def count_by_status(self) -> dict:
        """Count assignments by status."""
        query = select(
            WorkReleaseAssignment.status,
            func.count(WorkReleaseAssignment.id)
        ).where(
            WorkReleaseAssignment.is_deleted == False
        ).group_by(WorkReleaseAssignment.status)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}


class WorkReleaseLogRepository:
    """Repository for work release log operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: WorkReleaseLog) -> WorkReleaseLog:
        """Create a new log entry."""
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_by_id(self, log_id: UUID) -> Optional[WorkReleaseLog]:
        """Get log by ID."""
        query = select(WorkReleaseLog).where(WorkReleaseLog.id == log_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_assignment_and_date(
        self,
        assignment_id: UUID,
        log_date: date
    ) -> Optional[WorkReleaseLog]:
        """Get log for a specific assignment and date (unique constraint)."""
        query = select(WorkReleaseLog).where(
            WorkReleaseLog.assignment_id == assignment_id,
            WorkReleaseLog.log_date == log_date
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_assignment(
        self,
        assignment_id: UUID,
        limit: Optional[int] = None
    ) -> List[WorkReleaseLog]:
        """Get logs for an assignment."""
        query = select(WorkReleaseLog).where(
            WorkReleaseLog.assignment_id == assignment_id
        ).order_by(WorkReleaseLog.log_date.desc())

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date(self, log_date: date) -> List[WorkReleaseLog]:
        """Get all logs for a specific date."""
        query = select(WorkReleaseLog).where(
            WorkReleaseLog.log_date == log_date
        ).options(
            selectinload(WorkReleaseLog.assignment).selectinload(WorkReleaseAssignment.inmate),
            selectinload(WorkReleaseLog.assignment).selectinload(WorkReleaseAssignment.employer)
        ).order_by(WorkReleaseLog.departure_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unresolved(self, as_of_date: Optional[date] = None) -> List[WorkReleaseLog]:
        """
        Get logs where inmate departed but hasn't returned.

        CRITICAL: These represent potential security concerns.
        """
        if as_of_date is None:
            as_of_date = date.today()

        query = select(WorkReleaseLog).where(
            WorkReleaseLog.status == LogStatus.DEPARTED.value,
            WorkReleaseLog.log_date <= as_of_date
        ).options(
            selectinload(WorkReleaseLog.assignment).selectinload(WorkReleaseAssignment.inmate),
            selectinload(WorkReleaseLog.assignment).selectinload(WorkReleaseAssignment.employer)
        ).order_by(WorkReleaseLog.log_date, WorkReleaseLog.departure_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status_and_date_range(
        self,
        status: str,
        start_date: date,
        end_date: date
    ) -> List[WorkReleaseLog]:
        """Get logs by status within a date range."""
        query = select(WorkReleaseLog).where(
            WorkReleaseLog.status == status,
            WorkReleaseLog.log_date >= start_date,
            WorkReleaseLog.log_date <= end_date
        ).order_by(WorkReleaseLog.log_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_late_returns(
        self,
        start_date: date,
        end_date: date
    ) -> List[WorkReleaseLog]:
        """Get late return logs within a date range."""
        return await self.get_by_status_and_date_range(
            LogStatus.RETURNED_LATE.value,
            start_date,
            end_date
        )

    async def get_no_shows(
        self,
        start_date: date,
        end_date: date
    ) -> List[WorkReleaseLog]:
        """Get no-show logs within a date range."""
        return await self.get_by_status_and_date_range(
            LogStatus.DID_NOT_RETURN.value,
            start_date,
            end_date
        )

    async def update(self, log: WorkReleaseLog) -> WorkReleaseLog:
        """Update a log entry."""
        await self.session.flush()
        return log

    async def count_by_status_for_date(self, log_date: date) -> dict:
        """Count logs by status for a specific date."""
        query = select(
            WorkReleaseLog.status,
            func.count(WorkReleaseLog.id)
        ).where(
            WorkReleaseLog.log_date == log_date
        ).group_by(WorkReleaseLog.status)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_status_for_month(self, year: int, month: int) -> dict:
        """Count logs by status for a specific month."""
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        query = select(
            WorkReleaseLog.status,
            func.count(WorkReleaseLog.id)
        ).where(
            WorkReleaseLog.log_date >= start_date,
            WorkReleaseLog.log_date <= end_date
        ).group_by(WorkReleaseLog.status)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}
