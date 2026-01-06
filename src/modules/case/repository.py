"""
Case Management Repository - Data access layer for case management.

Provides specialized queries for:
- Case assignments by inmate, officer, active status
- Case notes by inmate, type, follow-up status
- Rehabilitation goals by inmate, type, status
- Caseload and statistics
"""
from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import NoteType, GoalType, GoalStatus
from src.modules.case.models import CaseAssignment, CaseNote, RehabilitationGoal


class CaseAssignmentRepository(AsyncBaseRepository[CaseAssignment]):
    """Repository for CaseAssignment entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CaseAssignment, session)

    async def get_active_by_inmate(self, inmate_id: UUID) -> Optional[CaseAssignment]:
        """Get the active case assignment for an inmate."""
        query = select(CaseAssignment).where(
            CaseAssignment.inmate_id == inmate_id,
            CaseAssignment.is_active == True,  # noqa: E712
            CaseAssignment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[CaseAssignment]:
        """Get all assignments for an inmate."""
        query = select(CaseAssignment).where(
            CaseAssignment.inmate_id == inmate_id
        )
        if not include_deleted:
            query = query.where(CaseAssignment.is_deleted == False)  # noqa: E712
        query = query.order_by(CaseAssignment.assigned_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_officer(
        self,
        case_officer_id: UUID,
        active_only: bool = True,
        include_deleted: bool = False
    ) -> List[CaseAssignment]:
        """Get assignments for a case officer."""
        query = select(CaseAssignment).where(
            CaseAssignment.case_officer_id == case_officer_id
        )
        if active_only:
            query = query.where(CaseAssignment.is_active == True)  # noqa: E712
        if not include_deleted:
            query = query.where(CaseAssignment.is_deleted == False)  # noqa: E712
        query = query.order_by(CaseAssignment.assigned_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_assignments(self) -> List[CaseAssignment]:
        """Get all active assignments."""
        query = select(CaseAssignment).where(
            CaseAssignment.is_active == True,  # noqa: E712
            CaseAssignment.is_deleted == False  # noqa: E712
        ).order_by(CaseAssignment.assigned_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_active_by_officer(self, case_officer_id: UUID) -> int:
        """Count active assignments for an officer."""
        query = select(func.count()).select_from(CaseAssignment).where(
            CaseAssignment.case_officer_id == case_officer_id,
            CaseAssignment.is_active == True,  # noqa: E712
            CaseAssignment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_active(self) -> int:
        """Count total active assignments."""
        query = select(func.count()).select_from(CaseAssignment).where(
            CaseAssignment.is_active == True,  # noqa: E712
            CaseAssignment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0


class CaseNoteRepository(AsyncBaseRepository[CaseNote]):
    """Repository for CaseNote entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CaseNote, session)

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_confidential: bool = False,
        limit: Optional[int] = None
    ) -> List[CaseNote]:
        """Get case notes for an inmate."""
        query = select(CaseNote).where(CaseNote.inmate_id == inmate_id)
        if not include_confidential:
            query = query.where(CaseNote.is_confidential == False)  # noqa: E712
        query = query.order_by(CaseNote.note_date.desc())
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_assignment(
        self,
        case_assignment_id: UUID
    ) -> List[CaseNote]:
        """Get case notes for an assignment."""
        query = select(CaseNote).where(
            CaseNote.case_assignment_id == case_assignment_id
        ).order_by(CaseNote.note_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        note_type: NoteType,
        inmate_id: Optional[UUID] = None
    ) -> List[CaseNote]:
        """Get case notes by type."""
        query = select(CaseNote).where(CaseNote.note_type == note_type.value)
        if inmate_id:
            query = query.where(CaseNote.inmate_id == inmate_id)
        query = query.order_by(CaseNote.note_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_follow_ups(
        self,
        case_officer_id: Optional[UUID] = None
    ) -> List[CaseNote]:
        """Get notes with pending follow-ups."""
        query = select(CaseNote).where(
            CaseNote.follow_up_required == True,  # noqa: E712
            or_(
                CaseNote.follow_up_date.is_(None),
                CaseNote.follow_up_date <= date.today()
            )
        )
        if case_officer_id:
            query = query.join(CaseAssignment).where(
                CaseAssignment.case_officer_id == case_officer_id,
                CaseAssignment.is_active == True  # noqa: E712
            )
        query = query.order_by(CaseNote.follow_up_date.asc().nullsfirst())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_type(self) -> dict:
        """Count notes by type."""
        result = {}
        for note_type in NoteType:
            query = select(func.count()).select_from(CaseNote).where(
                CaseNote.note_type == note_type.value
            )
            count = await self.session.execute(query)
            result[note_type.value] = count.scalar() or 0
        return result

    async def count_by_inmate(self, inmate_id: UUID) -> int:
        """Count notes for an inmate."""
        query = select(func.count()).select_from(CaseNote).where(
            CaseNote.inmate_id == inmate_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_pending_follow_ups(
        self,
        case_officer_id: Optional[UUID] = None
    ) -> int:
        """Count pending follow-ups."""
        query = select(func.count()).select_from(CaseNote).where(
            CaseNote.follow_up_required == True  # noqa: E712
        )
        if case_officer_id:
            query = query.join(CaseAssignment).where(
                CaseAssignment.case_officer_id == case_officer_id,
                CaseAssignment.is_active == True  # noqa: E712
            )
        result = await self.session.execute(query)
        return result.scalar() or 0


class RehabilitationGoalRepository(AsyncBaseRepository[RehabilitationGoal]):
    """Repository for RehabilitationGoal entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RehabilitationGoal, session)

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[RehabilitationGoal]:
        """Get goals for an inmate."""
        query = select(RehabilitationGoal).where(
            RehabilitationGoal.inmate_id == inmate_id
        )
        if not include_deleted:
            query = query.where(RehabilitationGoal.is_deleted == False)  # noqa: E712
        query = query.order_by(RehabilitationGoal.target_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: GoalStatus,
        inmate_id: Optional[UUID] = None,
        include_deleted: bool = False
    ) -> List[RehabilitationGoal]:
        """Get goals by status."""
        query = select(RehabilitationGoal).where(
            RehabilitationGoal.status == status.value
        )
        if inmate_id:
            query = query.where(RehabilitationGoal.inmate_id == inmate_id)
        if not include_deleted:
            query = query.where(RehabilitationGoal.is_deleted == False)  # noqa: E712
        query = query.order_by(RehabilitationGoal.target_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        goal_type: GoalType,
        inmate_id: Optional[UUID] = None,
        include_deleted: bool = False
    ) -> List[RehabilitationGoal]:
        """Get goals by type."""
        query = select(RehabilitationGoal).where(
            RehabilitationGoal.goal_type == goal_type.value
        )
        if inmate_id:
            query = query.where(RehabilitationGoal.inmate_id == inmate_id)
        if not include_deleted:
            query = query.where(RehabilitationGoal.is_deleted == False)  # noqa: E712
        query = query.order_by(RehabilitationGoal.target_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue(
        self,
        inmate_id: Optional[UUID] = None
    ) -> List[RehabilitationGoal]:
        """Get overdue goals (past target date, not completed/cancelled)."""
        today = date.today()
        active_statuses = [
            GoalStatus.NOT_STARTED.value,
            GoalStatus.IN_PROGRESS.value
        ]
        query = select(RehabilitationGoal).where(
            RehabilitationGoal.target_date < today,
            RehabilitationGoal.status.in_(active_statuses),
            RehabilitationGoal.is_deleted == False  # noqa: E712
        )
        if inmate_id:
            query = query.where(RehabilitationGoal.inmate_id == inmate_id)
        query = query.order_by(RehabilitationGoal.target_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active(
        self,
        inmate_id: Optional[UUID] = None
    ) -> List[RehabilitationGoal]:
        """Get active goals (not started or in progress)."""
        active_statuses = [
            GoalStatus.NOT_STARTED.value,
            GoalStatus.IN_PROGRESS.value
        ]
        query = select(RehabilitationGoal).where(
            RehabilitationGoal.status.in_(active_statuses),
            RehabilitationGoal.is_deleted == False  # noqa: E712
        )
        if inmate_id:
            query = query.where(RehabilitationGoal.inmate_id == inmate_id)
        query = query.order_by(RehabilitationGoal.target_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self, inmate_id: Optional[UUID] = None) -> dict:
        """Count goals by status."""
        result = {}
        for status in GoalStatus:
            query = select(func.count()).select_from(RehabilitationGoal).where(
                RehabilitationGoal.status == status.value,
                RehabilitationGoal.is_deleted == False  # noqa: E712
            )
            if inmate_id:
                query = query.where(RehabilitationGoal.inmate_id == inmate_id)
            count = await self.session.execute(query)
            result[status.value] = count.scalar() or 0
        return result

    async def count_by_type(self, inmate_id: Optional[UUID] = None) -> dict:
        """Count goals by type."""
        result = {}
        for goal_type in GoalType:
            query = select(func.count()).select_from(RehabilitationGoal).where(
                RehabilitationGoal.goal_type == goal_type.value,
                RehabilitationGoal.is_deleted == False  # noqa: E712
            )
            if inmate_id:
                query = query.where(RehabilitationGoal.inmate_id == inmate_id)
            count = await self.session.execute(query)
            result[goal_type.value] = count.scalar() or 0
        return result

    async def count_overdue(self, case_officer_id: Optional[UUID] = None) -> int:
        """Count overdue goals."""
        today = date.today()
        active_statuses = [
            GoalStatus.NOT_STARTED.value,
            GoalStatus.IN_PROGRESS.value
        ]
        query = select(func.count()).select_from(RehabilitationGoal).where(
            RehabilitationGoal.target_date < today,
            RehabilitationGoal.status.in_(active_statuses),
            RehabilitationGoal.is_deleted == False  # noqa: E712
        )
        if case_officer_id:
            # Join through inmate's active case assignment
            query = query.join(
                CaseAssignment,
                and_(
                    CaseAssignment.inmate_id == RehabilitationGoal.inmate_id,
                    CaseAssignment.case_officer_id == case_officer_id,
                    CaseAssignment.is_active == True  # noqa: E712
                )
            )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_average_goals_per_inmate(self) -> Optional[float]:
        """Get average number of goals per inmate."""
        # Count unique inmates with goals
        inmates_query = select(
            func.count(func.distinct(RehabilitationGoal.inmate_id))
        ).where(RehabilitationGoal.is_deleted == False)  # noqa: E712
        inmates_result = await self.session.execute(inmates_query)
        inmates_count = inmates_result.scalar() or 0

        if inmates_count == 0:
            return None

        # Count total goals
        goals_query = select(func.count()).select_from(RehabilitationGoal).where(
            RehabilitationGoal.is_deleted == False  # noqa: E712
        )
        goals_result = await self.session.execute(goals_query)
        goals_count = goals_result.scalar() or 0

        return goals_count / inmates_count
