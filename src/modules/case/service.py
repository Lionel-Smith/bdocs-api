"""
Case Management Service - Business logic for case management.

Implements key operations:
- Case officer assignment (auto-ends previous)
- Case note documentation
- Rehabilitation goal tracking
- Caseload management

Case management is central to rehabilitation success,
providing structured support for each inmate's journey.
"""
from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import NoteType, GoalType, GoalStatus
from src.modules.case.models import CaseAssignment, CaseNote, RehabilitationGoal
from src.modules.case.repository import (
    CaseAssignmentRepository,
    CaseNoteRepository,
    RehabilitationGoalRepository
)
from src.modules.case.dtos import (
    CaseAssignmentCreate,
    CaseAssignmentEnd,
    CaseAssignmentResponse,
    CaseNoteCreate,
    CaseNoteResponse,
    RehabilitationGoalCreate,
    RehabilitationGoalUpdate,
    RehabilitationGoalProgressUpdate,
    RehabilitationGoalResponse,
    InmateCaseSummary,
    CaseOfficerCaseload,
    CaseStatistics,
)


class CaseService:
    """Service for case management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.assignment_repo = CaseAssignmentRepository(session)
        self.note_repo = CaseNoteRepository(session)
        self.goal_repo = RehabilitationGoalRepository(session)

    # ========================================================================
    # Case Assignment Operations
    # ========================================================================

    async def assign_case_officer(
        self,
        data: CaseAssignmentCreate,
        assigned_by: Optional[UUID] = None
    ) -> CaseAssignment:
        """
        Assign a case officer to an inmate.

        If the inmate has an existing active assignment, it will be ended
        automatically before creating the new assignment.
        """
        # End any existing active assignment
        existing = await self.assignment_repo.get_active_by_inmate(data.inmate_id)
        if existing:
            existing.is_active = False
            existing.end_date = data.assigned_date
            if existing.caseload_notes:
                existing.caseload_notes = (
                    f"{existing.caseload_notes}\n\n"
                    f"[{data.assigned_date}] Assignment ended - new officer assigned"
                )
            else:
                existing.caseload_notes = (
                    f"[{data.assigned_date}] Assignment ended - new officer assigned"
                )
            await self.assignment_repo.update(existing)

        # Create new assignment
        assignment = CaseAssignment(
            inmate_id=data.inmate_id,
            case_officer_id=data.case_officer_id,
            assigned_date=data.assigned_date,
            is_active=True,
            caseload_notes=data.caseload_notes,
            assigned_by=assigned_by
        )

        return await self.assignment_repo.create(assignment)

    async def get_assignment(
        self,
        assignment_id: UUID
    ) -> Optional[CaseAssignment]:
        """Get assignment by ID."""
        return await self.assignment_repo.get_by_id(assignment_id)

    async def get_active_assignment(
        self,
        inmate_id: UUID
    ) -> Optional[CaseAssignment]:
        """Get the active assignment for an inmate."""
        return await self.assignment_repo.get_active_by_inmate(inmate_id)

    async def get_all_assignments(
        self,
        active_only: bool = False
    ) -> List[CaseAssignment]:
        """Get all assignments."""
        if active_only:
            return await self.assignment_repo.get_active_assignments()
        return await self.assignment_repo.get_all()

    async def end_assignment(
        self,
        assignment_id: UUID,
        data: CaseAssignmentEnd
    ) -> CaseAssignment:
        """End a case assignment."""
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment not found: {assignment_id}")

        if not assignment.is_active:
            raise ValueError("Assignment is already ended")

        assignment.is_active = False
        assignment.end_date = data.end_date

        if data.notes:
            if assignment.caseload_notes:
                assignment.caseload_notes = (
                    f"{assignment.caseload_notes}\n\n"
                    f"[{data.end_date}] {data.notes}"
                )
            else:
                assignment.caseload_notes = f"[{data.end_date}] {data.notes}"

        return await self.assignment_repo.update(assignment)

    async def get_caseload(
        self,
        case_officer_id: UUID
    ) -> CaseOfficerCaseload:
        """Get a case officer's current caseload."""
        assignments = await self.assignment_repo.get_by_officer(
            case_officer_id, active_only=True
        )
        pending_follow_ups = await self.note_repo.count_pending_follow_ups(case_officer_id)
        overdue_goals = await self.goal_repo.count_overdue(case_officer_id)

        return CaseOfficerCaseload(
            case_officer_id=case_officer_id,
            total_active_cases=len(assignments),
            assignments=[
                CaseAssignmentResponse.model_validate(a) for a in assignments
            ],
            pending_follow_ups=pending_follow_ups,
            overdue_goals_count=overdue_goals
        )

    # ========================================================================
    # Case Note Operations
    # ========================================================================

    async def add_case_note(
        self,
        data: CaseNoteCreate,
        created_by: Optional[UUID] = None
    ) -> CaseNote:
        """
        Add a case note for an inmate.

        The note is linked to the inmate's current active assignment.
        """
        # Get active assignment
        assignment = await self.assignment_repo.get_active_by_inmate(data.inmate_id)
        if not assignment:
            raise ValueError(
                f"No active case assignment for inmate: {data.inmate_id}"
            )

        note = CaseNote(
            case_assignment_id=assignment.id,
            inmate_id=data.inmate_id,
            note_date=data.note_date,
            note_type=data.note_type.value,
            content=data.content,
            is_confidential=data.is_confidential,
            follow_up_required=data.follow_up_required,
            follow_up_date=data.follow_up_date,
            created_by=created_by
        )

        return await self.note_repo.create(note)

    async def get_case_note(self, note_id: UUID) -> Optional[CaseNote]:
        """Get case note by ID."""
        return await self.note_repo.get_by_id(note_id)

    async def get_inmate_notes(
        self,
        inmate_id: UUID,
        include_confidential: bool = False,
        limit: Optional[int] = None
    ) -> List[CaseNote]:
        """Get case notes for an inmate."""
        return await self.note_repo.get_by_inmate(
            inmate_id, include_confidential, limit
        )

    async def get_pending_follow_ups(
        self,
        case_officer_id: Optional[UUID] = None
    ) -> List[CaseNote]:
        """Get notes with pending follow-ups."""
        return await self.note_repo.get_pending_follow_ups(case_officer_id)

    # ========================================================================
    # Rehabilitation Goal Operations
    # ========================================================================

    async def create_goal(
        self,
        inmate_id: UUID,
        data: RehabilitationGoalCreate,
        created_by: Optional[UUID] = None
    ) -> RehabilitationGoal:
        """Create a new rehabilitation goal for an inmate."""
        goal = RehabilitationGoal(
            inmate_id=inmate_id,
            goal_type=data.goal_type.value,
            title=data.title,
            description=data.description,
            target_date=data.target_date,
            status=GoalStatus.NOT_STARTED.value,
            progress_percentage=0,
            created_by=created_by
        )

        return await self.goal_repo.create(goal)

    async def get_goal(self, goal_id: UUID) -> Optional[RehabilitationGoal]:
        """Get goal by ID."""
        return await self.goal_repo.get_by_id(goal_id)

    async def get_inmate_goals(
        self,
        inmate_id: UUID
    ) -> List[RehabilitationGoal]:
        """Get all goals for an inmate."""
        return await self.goal_repo.get_by_inmate(inmate_id)

    async def update_goal(
        self,
        goal_id: UUID,
        data: RehabilitationGoalUpdate
    ) -> Optional[RehabilitationGoal]:
        """Update a rehabilitation goal."""
        goal = await self.goal_repo.get_by_id(goal_id)
        if not goal:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(goal, field):
                if field == 'goal_type' and value:
                    setattr(goal, field, value.value)
                elif field == 'status' and value:
                    setattr(goal, field, value.value)
                else:
                    setattr(goal, field, value)

        return await self.goal_repo.update(goal)

    async def update_goal_progress(
        self,
        goal_id: UUID,
        data: RehabilitationGoalProgressUpdate
    ) -> RehabilitationGoal:
        """
        Update goal progress.

        Automatically sets status to COMPLETED if progress reaches 100%
        and no other status is specified.
        """
        goal = await self.goal_repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Goal not found: {goal_id}")

        # Check if goal is already in terminal state
        if goal.status in [GoalStatus.COMPLETED.value, GoalStatus.CANCELLED.value]:
            raise ValueError(
                f"Cannot update progress for goal with status: {goal.status}"
            )

        goal.progress_percentage = data.progress_percentage

        # Update notes if provided
        if data.notes:
            if goal.notes:
                goal.notes = f"{goal.notes}\n\n[{date.today()}] {data.notes}"
            else:
                goal.notes = f"[{date.today()}] {data.notes}"

        # Handle status update
        if data.status:
            goal.status = data.status.value
            if data.status == GoalStatus.COMPLETED:
                goal.completion_date = date.today()
        elif data.progress_percentage >= 100:
            # Auto-complete if progress reaches 100%
            goal.status = GoalStatus.COMPLETED.value
            goal.completion_date = date.today()
        elif goal.status == GoalStatus.NOT_STARTED.value and data.progress_percentage > 0:
            # Auto-start if progress > 0
            goal.status = GoalStatus.IN_PROGRESS.value

        return await self.goal_repo.update(goal)

    async def delete_goal(self, goal_id: UUID) -> bool:
        """Soft delete a rehabilitation goal."""
        return await self.goal_repo.delete(goal_id)

    async def get_overdue_goals(
        self,
        inmate_id: Optional[UUID] = None
    ) -> List[RehabilitationGoal]:
        """Get overdue goals."""
        return await self.goal_repo.get_overdue(inmate_id)

    # ========================================================================
    # Summary and Statistics
    # ========================================================================

    async def get_inmate_case_summary(
        self,
        inmate_id: UUID
    ) -> InmateCaseSummary:
        """Get comprehensive case summary for an inmate."""
        # Get current assignment
        current_assignment = await self.assignment_repo.get_active_by_inmate(inmate_id)
        all_assignments = await self.assignment_repo.get_by_inmate(inmate_id)

        # Get notes
        notes = await self.note_repo.get_by_inmate(inmate_id, limit=10)
        total_notes = await self.note_repo.count_by_inmate(inmate_id)

        # Get goals
        goals = await self.goal_repo.get_by_inmate(inmate_id)
        goals_by_status = await self.goal_repo.count_by_status(inmate_id)
        active_goals = [g for g in goals if g.status in [
            GoalStatus.NOT_STARTED.value, GoalStatus.IN_PROGRESS.value
        ]]
        overdue_goals = [g for g in goals if g.is_overdue]

        return InmateCaseSummary(
            inmate_id=inmate_id,
            current_assignment=(
                CaseAssignmentResponse.model_validate(current_assignment)
                if current_assignment else None
            ),
            total_assignments=len(all_assignments),
            total_notes=total_notes,
            recent_notes=[
                CaseNoteResponse.model_validate(n) for n in notes
            ],
            goals_summary=goals_by_status,
            active_goals=[
                RehabilitationGoalResponse(
                    id=g.id,
                    inmate_id=g.inmate_id,
                    goal_type=GoalType(g.goal_type),
                    title=g.title,
                    description=g.description,
                    target_date=g.target_date,
                    status=GoalStatus(g.status),
                    progress_percentage=g.progress_percentage,
                    completion_date=g.completion_date,
                    is_overdue=g.is_overdue,
                    notes=g.notes,
                    created_by=g.created_by,
                    inserted_date=g.inserted_date,
                    updated_date=g.updated_date
                )
                for g in active_goals
            ],
            overdue_goals=[
                RehabilitationGoalResponse(
                    id=g.id,
                    inmate_id=g.inmate_id,
                    goal_type=GoalType(g.goal_type),
                    title=g.title,
                    description=g.description,
                    target_date=g.target_date,
                    status=GoalStatus(g.status),
                    progress_percentage=g.progress_percentage,
                    completion_date=g.completion_date,
                    is_overdue=g.is_overdue,
                    notes=g.notes,
                    created_by=g.created_by,
                    inserted_date=g.inserted_date,
                    updated_date=g.updated_date
                )
                for g in overdue_goals
            ]
        )

    async def get_statistics(self) -> CaseStatistics:
        """Get overall case management statistics."""
        total_active = await self.assignment_repo.count_active()
        total_notes = await self.note_repo.count()
        notes_by_type = await self.note_repo.count_by_type()
        goals_by_status = await self.goal_repo.count_by_status()
        goals_by_type = await self.goal_repo.count_by_type()
        overdue = await self.goal_repo.count_overdue()
        pending_follow_ups = await self.note_repo.count_pending_follow_ups()
        avg_goals = await self.goal_repo.get_average_goals_per_inmate()

        return CaseStatistics(
            total_active_assignments=total_active,
            total_case_notes=total_notes,
            notes_by_type=notes_by_type,
            goals_by_status=goals_by_status,
            goals_by_type=goals_by_type,
            overdue_goals=overdue,
            pending_follow_ups=pending_follow_ups,
            average_goals_per_inmate=avg_goals
        )
