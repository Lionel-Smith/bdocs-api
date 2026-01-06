"""
Programme Repository - Data access layer for programmes.

Provides specialized queries for:
- Programmes by category, status, active status
- Sessions by date, status, upcoming
- Enrollments by inmate, programme, status
- Statistics and reporting
"""
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import ProgrammeCategory, SessionStatus, EnrollmentStatus
from src.modules.programme.models import Programme, ProgrammeSession, ProgrammeEnrollment


class ProgrammeRepository(AsyncBaseRepository[Programme]):
    """Repository for Programme entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Programme, session)

    async def get_by_code(self, code: str) -> Optional[Programme]:
        """Get programme by code."""
        query = select(Programme).where(
            Programme.code == code.upper(),
            Programme.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active(self) -> List[Programme]:
        """Get all active programmes."""
        query = select(Programme).where(
            Programme.is_active == True,  # noqa: E712
            Programme.is_deleted == False  # noqa: E712
        ).order_by(Programme.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category: ProgrammeCategory,
        active_only: bool = True
    ) -> List[Programme]:
        """Get programmes by category."""
        query = select(Programme).where(
            Programme.category == category.value,
            Programme.is_deleted == False  # noqa: E712
        )
        if active_only:
            query = query.where(Programme.is_active == True)  # noqa: E712
        query = query.order_by(Programme.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_capacity(self) -> List[Programme]:
        """Get active programmes that have available capacity."""
        # Subquery to count active enrollments per programme
        enrollment_count = (
            select(
                ProgrammeEnrollment.programme_id,
                func.count(ProgrammeEnrollment.id).label('count')
            )
            .where(
                ProgrammeEnrollment.status.in_([
                    EnrollmentStatus.ENROLLED.value,
                    EnrollmentStatus.ACTIVE.value
                ]),
                ProgrammeEnrollment.is_deleted == False  # noqa: E712
            )
            .group_by(ProgrammeEnrollment.programme_id)
            .subquery()
        )

        query = (
            select(Programme)
            .outerjoin(enrollment_count, Programme.id == enrollment_count.c.programme_id)
            .where(
                Programme.is_active == True,  # noqa: E712
                Programme.is_deleted == False,  # noqa: E712
                or_(
                    enrollment_count.c.count.is_(None),
                    enrollment_count.c.count < Programme.max_participants
                )
            )
            .order_by(Programme.name)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_category(self, active_only: bool = True) -> dict:
        """Count programmes by category."""
        result = {}
        for category in ProgrammeCategory:
            query = select(func.count()).select_from(Programme).where(
                Programme.category == category.value,
                Programme.is_deleted == False  # noqa: E712
            )
            if active_only:
                query = query.where(Programme.is_active == True)  # noqa: E712
            count = await self.session.execute(query)
            result[category.value] = count.scalar() or 0
        return result

    async def get_enrollment_count(self, programme_id: UUID) -> int:
        """Get count of active enrollments for a programme."""
        query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.programme_id == programme_id,
            ProgrammeEnrollment.status.in_([
                EnrollmentStatus.ENROLLED.value,
                EnrollmentStatus.ACTIVE.value
            ]),
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0


class ProgrammeSessionRepository(AsyncBaseRepository[ProgrammeSession]):
    """Repository for ProgrammeSession entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ProgrammeSession, session)

    async def get_by_programme(
        self,
        programme_id: UUID,
        status: Optional[SessionStatus] = None
    ) -> List[ProgrammeSession]:
        """Get sessions for a programme."""
        query = select(ProgrammeSession).where(
            ProgrammeSession.programme_id == programme_id
        )
        if status:
            query = query.where(ProgrammeSession.status == status.value)
        query = query.order_by(ProgrammeSession.session_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        programme_id: Optional[UUID] = None,
        days: int = 7
    ) -> List[ProgrammeSession]:
        """Get upcoming scheduled sessions."""
        future_date = date.today() + timedelta(days=days)
        query = select(ProgrammeSession).where(
            ProgrammeSession.status == SessionStatus.SCHEDULED.value,
            ProgrammeSession.session_date >= date.today(),
            ProgrammeSession.session_date <= future_date
        )
        if programme_id:
            query = query.where(ProgrammeSession.programme_id == programme_id)
        query = query.order_by(ProgrammeSession.session_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        programme_id: Optional[UUID] = None
    ) -> List[ProgrammeSession]:
        """Get sessions within a date range."""
        query = select(ProgrammeSession).where(
            ProgrammeSession.session_date >= start_date,
            ProgrammeSession.session_date <= end_date
        )
        if programme_id:
            query = query.where(ProgrammeSession.programme_id == programme_id)
        query = query.order_by(ProgrammeSession.session_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, programme_id: UUID) -> dict:
        """Count sessions by status for a programme."""
        result = {}
        for status in SessionStatus:
            query = select(func.count()).select_from(ProgrammeSession).where(
                ProgrammeSession.programme_id == programme_id,
                ProgrammeSession.status == status.value
            )
            count = await self.session.execute(query)
            result[status.value] = count.scalar() or 0
        return result


class ProgrammeEnrollmentRepository(AsyncBaseRepository[ProgrammeEnrollment]):
    """Repository for ProgrammeEnrollment entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ProgrammeEnrollment, session)

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[ProgrammeEnrollment]:
        """Get all enrollments for an inmate."""
        query = select(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id
        )
        if not include_deleted:
            query = query.where(ProgrammeEnrollment.is_deleted == False)  # noqa: E712
        query = query.order_by(ProgrammeEnrollment.enrolled_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_programme(
        self,
        programme_id: UUID,
        status: Optional[EnrollmentStatus] = None,
        include_deleted: bool = False
    ) -> List[ProgrammeEnrollment]:
        """Get enrollments for a programme."""
        query = select(ProgrammeEnrollment).where(
            ProgrammeEnrollment.programme_id == programme_id
        )
        if status:
            query = query.where(ProgrammeEnrollment.status == status.value)
        if not include_deleted:
            query = query.where(ProgrammeEnrollment.is_deleted == False)  # noqa: E712
        query = query.order_by(ProgrammeEnrollment.enrolled_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: EnrollmentStatus,
        include_deleted: bool = False
    ) -> List[ProgrammeEnrollment]:
        """Get enrollments by status."""
        query = select(ProgrammeEnrollment).where(
            ProgrammeEnrollment.status == status.value
        )
        if not include_deleted:
            query = query.where(ProgrammeEnrollment.is_deleted == False)  # noqa: E712
        query = query.order_by(ProgrammeEnrollment.enrolled_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_enrollment(
        self,
        programme_id: UUID,
        inmate_id: UUID
    ) -> Optional[ProgrammeEnrollment]:
        """Get active enrollment for an inmate in a programme."""
        query = select(ProgrammeEnrollment).where(
            ProgrammeEnrollment.programme_id == programme_id,
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.status.in_([
                EnrollmentStatus.ENROLLED.value,
                EnrollmentStatus.ACTIVE.value
            ]),
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_status(self, programme_id: Optional[UUID] = None) -> dict:
        """Count enrollments by status."""
        result = {}
        for status in EnrollmentStatus:
            query = select(func.count()).select_from(ProgrammeEnrollment).where(
                ProgrammeEnrollment.status == status.value,
                ProgrammeEnrollment.is_deleted == False  # noqa: E712
            )
            if programme_id:
                query = query.where(ProgrammeEnrollment.programme_id == programme_id)
            count = await self.session.execute(query)
            result[status.value] = count.scalar() or 0
        return result

    async def count_by_inmate_status(self, inmate_id: UUID) -> dict:
        """Count enrollments by status for an inmate."""
        active_statuses = [
            EnrollmentStatus.ENROLLED.value,
            EnrollmentStatus.ACTIVE.value
        ]

        total_query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        active_query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.status.in_(active_statuses),
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        completed_query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.status == EnrollmentStatus.COMPLETED.value,
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        withdrawn_query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.status == EnrollmentStatus.WITHDRAWN.value,
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        hours_query = select(func.sum(ProgrammeEnrollment.hours_completed)).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        certs_query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.inmate_id == inmate_id,
            ProgrammeEnrollment.certificate_issued == True,  # noqa: E712
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )

        total = await self.session.execute(total_query)
        active = await self.session.execute(active_query)
        completed = await self.session.execute(completed_query)
        withdrawn = await self.session.execute(withdrawn_query)
        hours = await self.session.execute(hours_query)
        certs = await self.session.execute(certs_query)

        return {
            "total": total.scalar() or 0,
            "active": active.scalar() or 0,
            "completed": completed.scalar() or 0,
            "withdrawn": withdrawn.scalar() or 0,
            "hours_completed": hours.scalar() or 0,
            "certificates_earned": certs.scalar() or 0
        }

    async def count_completed_this_year(self) -> int:
        """Count completions in the current year."""
        current_year = date.today().year
        query = select(func.count()).select_from(ProgrammeEnrollment).where(
            ProgrammeEnrollment.status == EnrollmentStatus.COMPLETED.value,
            extract('year', ProgrammeEnrollment.completion_date) == current_year,
            ProgrammeEnrollment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_most_popular_programmes(self, limit: int = 5) -> List[dict]:
        """Get programmes with most enrollments."""
        query = (
            select(
                Programme.id,
                Programme.name,
                func.count(ProgrammeEnrollment.id).label('enrollment_count')
            )
            .join(ProgrammeEnrollment, Programme.id == ProgrammeEnrollment.programme_id)
            .where(
                Programme.is_deleted == False,  # noqa: E712
                ProgrammeEnrollment.is_deleted == False  # noqa: E712
            )
            .group_by(Programme.id, Programme.name)
            .order_by(func.count(ProgrammeEnrollment.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [
            {
                "programme_id": str(row.id),
                "name": row.name,
                "enrollment_count": row.enrollment_count
            }
            for row in result.all()
        ]
