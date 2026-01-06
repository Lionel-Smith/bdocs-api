"""
Work Release Service - Business logic for work release operations.

Key validations:
- CRITICAL: Only MINIMUM security inmates eligible for work release
- Employer must be approved with valid MOU
- Status transitions follow workflow rules
- Late return detection with automatic status update

Workflows:
- Employer: Create → Approve (with MOU) → Active/Inactive
- Assignment: PENDING_APPROVAL → APPROVED → ACTIVE → COMPLETED/TERMINATED
- Log: DEPARTED → RETURNED_ON_TIME/RETURNED_LATE/DID_NOT_RETURN
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.work_release.models import (
    WorkReleaseEmployer,
    WorkReleaseAssignment,
    WorkReleaseLog
)
from src.modules.work_release.repository import (
    WorkReleaseEmployerRepository,
    WorkReleaseAssignmentRepository,
    WorkReleaseLogRepository
)
from src.modules.work_release.dtos import (
    WorkReleaseEmployerCreate,
    WorkReleaseEmployerUpdate,
    WorkReleaseEmployerApprove,
    WorkReleaseEmployerResponse,
    WorkReleaseAssignmentCreate,
    WorkReleaseAssignmentUpdate,
    WorkReleaseAssignmentStatusUpdate,
    WorkReleaseAssignmentResponse,
    WorkReleaseLogDeparture,
    WorkReleaseLogReturn,
    WorkReleaseLogResponse,
    InmateWorkReleaseSummary,
    WorkReleaseStatistics,
    DailyWorkReleaseReport
)
from src.common.enums import WorkReleaseStatus, LogStatus, SecurityLevel


class WorkReleaseService:
    """Service for work release business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.employer_repo = WorkReleaseEmployerRepository(session)
        self.assignment_repo = WorkReleaseAssignmentRepository(session)
        self.log_repo = WorkReleaseLogRepository(session)

    # ========================================================================
    # Employer Operations
    # ========================================================================

    async def create_employer(
        self,
        data: WorkReleaseEmployerCreate
    ) -> WorkReleaseEmployer:
        """Create a new employer (pending approval)."""
        employer = WorkReleaseEmployer(
            name=data.name,
            business_type=data.business_type,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            address=data.address,
            notes=data.notes,
            is_approved=False,
            mou_signed=False,
            is_active=True
        )
        return await self.employer_repo.create(employer)

    async def get_employer(self, employer_id: UUID) -> Optional[WorkReleaseEmployer]:
        """Get employer by ID."""
        return await self.employer_repo.get_by_id(employer_id)

    async def get_all_employers(
        self,
        approved_only: bool = False,
        active_only: bool = False
    ) -> List[WorkReleaseEmployer]:
        """Get all employers with optional filters."""
        return await self.employer_repo.get_all(approved_only, active_only)

    async def get_available_employers(self) -> List[WorkReleaseEmployer]:
        """Get employers that can accept new inmates."""
        return await self.employer_repo.get_accepting_inmates()

    async def update_employer(
        self,
        employer_id: UUID,
        data: WorkReleaseEmployerUpdate
    ) -> Optional[WorkReleaseEmployer]:
        """Update employer details."""
        employer = await self.employer_repo.get_by_id(employer_id)
        if not employer:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(employer, field, value)

        return await self.employer_repo.update(employer)

    async def approve_employer(
        self,
        employer_id: UUID,
        data: WorkReleaseEmployerApprove,
        approved_by: Optional[UUID] = None
    ) -> Optional[WorkReleaseEmployer]:
        """
        Approve an employer for work release programme.

        Requires MOU to be signed.
        """
        employer = await self.employer_repo.get_by_id(employer_id)
        if not employer:
            return None

        if not data.mou_signed:
            raise ValueError("MOU must be signed to approve employer")

        employer.is_approved = True
        employer.approval_date = date.today()
        employer.approved_by = approved_by
        employer.mou_signed = data.mou_signed
        employer.mou_expiry_date = data.mou_expiry_date
        if data.notes:
            employer.notes = data.notes

        return await self.employer_repo.update(employer)

    async def revoke_employer_approval(
        self,
        employer_id: UUID,
        reason: str
    ) -> Optional[WorkReleaseEmployer]:
        """Revoke employer approval."""
        employer = await self.employer_repo.get_by_id(employer_id)
        if not employer:
            return None

        employer.is_approved = False
        employer.is_active = False
        employer.notes = f"{employer.notes or ''}\n[REVOKED] {date.today()}: {reason}".strip()

        return await self.employer_repo.update(employer)

    async def delete_employer(self, employer_id: UUID) -> bool:
        """Soft delete an employer."""
        employer = await self.employer_repo.get_by_id(employer_id)
        if not employer:
            return False

        # Check for active assignments
        active = await self.assignment_repo.get_by_employer(employer_id, active_only=True)
        if active:
            raise ValueError("Cannot delete employer with active assignments")

        return await self.employer_repo.soft_delete(employer)

    # ========================================================================
    # Assignment Operations
    # ========================================================================

    async def create_assignment(
        self,
        data: WorkReleaseAssignmentCreate,
        created_by: Optional[UUID] = None
    ) -> WorkReleaseAssignment:
        """
        Create a work release assignment (pending approval).

        Does NOT validate inmate eligibility - that happens at approval.
        """
        # Verify employer exists and can accept inmates
        employer = await self.employer_repo.get_by_id(data.employer_id)
        if not employer:
            raise ValueError("Employer not found")

        if not employer.can_accept_inmates:
            raise ValueError(
                "Employer cannot accept inmates. Check approval status and MOU validity."
            )

        # Check for existing active assignment
        existing = await self.assignment_repo.get_active_assignment(data.inmate_id)
        if existing:
            raise ValueError(
                f"Inmate already has active work release at {existing.employer.name}"
            )

        # Convert work_schedule to dict if needed
        schedule_dict = None
        if data.work_schedule:
            schedule_dict = {
                day: {"start": sched.start, "end": sched.end}
                for day, sched in data.work_schedule.items()
            }

        assignment = WorkReleaseAssignment(
            inmate_id=data.inmate_id,
            employer_id=data.employer_id,
            position_title=data.position_title,
            start_date=data.start_date,
            end_date=data.end_date,
            hourly_rate=data.hourly_rate,
            work_schedule=schedule_dict,
            supervisor_name=data.supervisor_name,
            supervisor_phone=data.supervisor_phone,
            notes=data.notes,
            status=WorkReleaseStatus.PENDING_APPROVAL.value,
            created_by=created_by
        )

        return await self.assignment_repo.create(assignment)

    async def get_assignment(
        self,
        assignment_id: UUID
    ) -> Optional[WorkReleaseAssignment]:
        """Get assignment by ID."""
        return await self.assignment_repo.get_by_id(assignment_id)

    async def get_inmate_assignments(
        self,
        inmate_id: UUID,
        active_only: bool = False
    ) -> List[WorkReleaseAssignment]:
        """Get all assignments for an inmate."""
        return await self.assignment_repo.get_by_inmate(inmate_id, active_only)

    async def get_active_work_releases(self) -> List[WorkReleaseAssignment]:
        """Get all active work release assignments."""
        return await self.assignment_repo.get_all_active()

    async def get_pending_approvals(self) -> List[WorkReleaseAssignment]:
        """Get all assignments pending approval."""
        return await self.assignment_repo.get_pending_approval()

    async def approve_assignment(
        self,
        assignment_id: UUID,
        approved_by: Optional[UUID] = None
    ) -> WorkReleaseAssignment:
        """
        Approve a work release assignment.

        CRITICAL VALIDATIONS:
        1. Employer must be approved with valid MOU
        2. Inmate must be MINIMUM security level

        Transitions: PENDING_APPROVAL → APPROVED
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.PENDING_APPROVAL.value:
            raise ValueError(
                f"Cannot approve assignment with status {assignment.status}"
            )

        # Validate employer
        employer = assignment.employer
        if not employer.is_approved:
            raise ValueError("Employer is not approved for work release")

        if not employer.is_mou_valid:
            raise ValueError("Employer MOU is invalid or expired")

        # CRITICAL: Validate inmate security level
        # Import here to avoid circular imports
        from src.modules.inmate.models import Inmate

        query = select(Inmate).where(Inmate.id == assignment.inmate_id)
        result = await self.session.execute(query)
        inmate = result.scalar_one_or_none()

        if not inmate:
            raise ValueError("Inmate not found")

        if inmate.security_level != SecurityLevel.MINIMUM.value:
            raise ValueError(
                f"Only MINIMUM security inmates are eligible for work release. "
                f"Inmate is {inmate.security_level} security."
            )

        # Approve the assignment
        assignment.status = WorkReleaseStatus.APPROVED.value
        assignment.approved_by = approved_by
        assignment.approval_date = date.today()

        return await self.assignment_repo.update(assignment)

    async def activate_assignment(
        self,
        assignment_id: UUID
    ) -> WorkReleaseAssignment:
        """
        Activate an approved assignment.

        Transitions: APPROVED → ACTIVE
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.APPROVED.value:
            raise ValueError(
                f"Cannot activate assignment with status {assignment.status}. "
                f"Must be APPROVED first."
            )

        assignment.status = WorkReleaseStatus.ACTIVE.value
        return await self.assignment_repo.update(assignment)

    async def suspend_assignment(
        self,
        assignment_id: UUID,
        reason: str
    ) -> WorkReleaseAssignment:
        """
        Suspend an active assignment.

        Transitions: ACTIVE → SUSPENDED
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.ACTIVE.value:
            raise ValueError("Can only suspend ACTIVE assignments")

        assignment.status = WorkReleaseStatus.SUSPENDED.value
        assignment.notes = f"{assignment.notes or ''}\n[SUSPENDED] {date.today()}: {reason}".strip()

        return await self.assignment_repo.update(assignment)

    async def reinstate_assignment(
        self,
        assignment_id: UUID
    ) -> WorkReleaseAssignment:
        """
        Reinstate a suspended assignment.

        Transitions: SUSPENDED → ACTIVE
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.SUSPENDED.value:
            raise ValueError("Can only reinstate SUSPENDED assignments")

        assignment.status = WorkReleaseStatus.ACTIVE.value
        assignment.notes = f"{assignment.notes or ''}\n[REINSTATED] {date.today()}".strip()

        return await self.assignment_repo.update(assignment)

    async def complete_assignment(
        self,
        assignment_id: UUID
    ) -> WorkReleaseAssignment:
        """
        Mark assignment as successfully completed.

        Transitions: ACTIVE → COMPLETED
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.ACTIVE.value:
            raise ValueError("Can only complete ACTIVE assignments")

        assignment.status = WorkReleaseStatus.COMPLETED.value
        assignment.end_date = date.today()

        return await self.assignment_repo.update(assignment)

    async def terminate_assignment(
        self,
        assignment_id: UUID,
        reason: str
    ) -> WorkReleaseAssignment:
        """
        Terminate an assignment early.

        Transitions: ACTIVE/SUSPENDED → TERMINATED
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        valid_for_termination = {
            WorkReleaseStatus.ACTIVE.value,
            WorkReleaseStatus.SUSPENDED.value
        }

        if assignment.status not in valid_for_termination:
            raise ValueError(
                f"Cannot terminate assignment with status {assignment.status}"
            )

        assignment.status = WorkReleaseStatus.TERMINATED.value
        assignment.end_date = date.today()
        assignment.termination_reason = reason

        return await self.assignment_repo.update(assignment)

    async def update_assignment(
        self,
        assignment_id: UUID,
        data: WorkReleaseAssignmentUpdate
    ) -> Optional[WorkReleaseAssignment]:
        """Update assignment details (non-status fields)."""
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(assignment, field, value)

        return await self.assignment_repo.update(assignment)

    # ========================================================================
    # Log Operations
    # ========================================================================

    async def log_departure(
        self,
        data: WorkReleaseLogDeparture,
        created_by: Optional[UUID] = None
    ) -> WorkReleaseLog:
        """
        Log inmate departure for work.

        Creates a new log entry with DEPARTED status.
        """
        # Verify assignment is active
        assignment = await self.assignment_repo.get_by_id(data.assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if assignment.status != WorkReleaseStatus.ACTIVE.value:
            raise ValueError(
                f"Cannot log departure for assignment with status {assignment.status}"
            )

        # Check for existing log on this date
        existing = await self.log_repo.get_by_assignment_and_date(
            data.assignment_id,
            data.log_date
        )
        if existing:
            raise ValueError(
                f"Log already exists for {data.log_date}. Use log_return to update."
            )

        log = WorkReleaseLog(
            assignment_id=data.assignment_id,
            log_date=data.log_date,
            departure_time=data.departure_time,
            expected_return_time=data.expected_return_time,
            status=LogStatus.DEPARTED.value,
            notes=data.notes
        )

        return await self.log_repo.create(log)

    async def log_return(
        self,
        log_id: UUID,
        data: WorkReleaseLogReturn,
        verified_by: Optional[UUID] = None
    ) -> WorkReleaseLog:
        """
        Log inmate return from work.

        Automatically determines if return was on-time or late.
        """
        log = await self.log_repo.get_by_id(log_id)
        if not log:
            raise ValueError("Log entry not found")

        if log.status != LogStatus.DEPARTED.value:
            raise ValueError(
                f"Cannot log return for entry with status {log.status}"
            )

        log.actual_return_time = data.actual_return_time
        log.verified_by = verified_by

        # Determine if return was late
        if data.actual_return_time > log.expected_return_time:
            log.status = LogStatus.RETURNED_LATE.value
        else:
            log.status = LogStatus.RETURNED_ON_TIME.value

        if data.notes:
            log.notes = f"{log.notes or ''}\n[RETURN] {data.notes}".strip()

        return await self.log_repo.update(log)

    async def mark_no_return(
        self,
        log_id: UUID,
        notes: str,
        verified_by: Optional[UUID] = None
    ) -> WorkReleaseLog:
        """
        Mark an inmate as did not return.

        CRITICAL: This is a serious security incident.
        """
        log = await self.log_repo.get_by_id(log_id)
        if not log:
            raise ValueError("Log entry not found")

        if log.status != LogStatus.DEPARTED.value:
            raise ValueError(
                f"Cannot mark no-return for entry with status {log.status}"
            )

        log.status = LogStatus.DID_NOT_RETURN.value
        log.verified_by = verified_by
        log.notes = f"{log.notes or ''}\n[NO RETURN] {notes}".strip()

        # Consider suspending the assignment
        assignment = await self.assignment_repo.get_by_id(log.assignment_id)
        if assignment and assignment.status == WorkReleaseStatus.ACTIVE.value:
            assignment.status = WorkReleaseStatus.SUSPENDED.value
            assignment.notes = f"{assignment.notes or ''}\n[AUTO-SUSPENDED] {date.today()}: Did not return".strip()
            await self.assignment_repo.update(assignment)

        return await self.log_repo.update(log)

    async def mark_excused(
        self,
        log_id: UUID,
        reason: str,
        verified_by: Optional[UUID] = None
    ) -> WorkReleaseLog:
        """Mark a log entry as excused (holiday, sick, etc.)."""
        log = await self.log_repo.get_by_id(log_id)
        if not log:
            raise ValueError("Log entry not found")

        log.status = LogStatus.EXCUSED.value
        log.verified_by = verified_by
        log.notes = f"{log.notes or ''}\n[EXCUSED] {reason}".strip()

        return await self.log_repo.update(log)

    async def get_log(self, log_id: UUID) -> Optional[WorkReleaseLog]:
        """Get log by ID."""
        return await self.log_repo.get_by_id(log_id)

    async def get_assignment_logs(
        self,
        assignment_id: UUID,
        limit: Optional[int] = None
    ) -> List[WorkReleaseLog]:
        """Get logs for an assignment."""
        return await self.log_repo.get_by_assignment(assignment_id, limit)

    async def get_daily_logs(self, log_date: date) -> List[WorkReleaseLog]:
        """Get all logs for a specific date."""
        return await self.log_repo.get_by_date(log_date)

    async def get_unresolved_logs(self) -> List[WorkReleaseLog]:
        """Get logs where inmates haven't returned."""
        return await self.log_repo.get_unresolved()

    # ========================================================================
    # Summary and Statistics
    # ========================================================================

    async def get_inmate_work_release_summary(
        self,
        inmate_id: UUID
    ) -> InmateWorkReleaseSummary:
        """Get work release summary for an inmate."""
        assignments = await self.assignment_repo.get_by_inmate(inmate_id)
        active = next(
            (a for a in assignments if a.status == WorkReleaseStatus.ACTIVE.value),
            None
        )

        # Count logs across all assignments
        total_work_days = 0
        late_returns = 0
        no_shows = 0

        for assignment in assignments:
            logs = await self.log_repo.get_by_assignment(assignment.id)
            for log in logs:
                if log.status in [
                    LogStatus.RETURNED_ON_TIME.value,
                    LogStatus.RETURNED_LATE.value
                ]:
                    total_work_days += 1
                if log.status == LogStatus.RETURNED_LATE.value:
                    late_returns += 1
                if log.status == LogStatus.DID_NOT_RETURN.value:
                    no_shows += 1

        active_response = None
        if active:
            active_response = WorkReleaseAssignmentResponse(
                id=active.id,
                inmate_id=active.inmate_id,
                employer_id=active.employer_id,
                employer_name=active.employer.name if active.employer else None,
                position_title=active.position_title,
                start_date=active.start_date,
                end_date=active.end_date,
                status=active.status,
                hourly_rate=active.hourly_rate,
                work_schedule=active.work_schedule,
                supervisor_name=active.supervisor_name,
                supervisor_phone=active.supervisor_phone,
                approved_by=active.approved_by,
                approval_date=active.approval_date,
                termination_reason=active.termination_reason,
                notes=active.notes,
                created_by=active.created_by,
                inserted_date=active.inserted_date,
                updated_date=active.updated_date
            )

        return InmateWorkReleaseSummary(
            inmate_id=inmate_id,
            current_assignment=active_response,
            total_assignments=len(assignments),
            total_work_days=total_work_days,
            late_returns=late_returns,
            no_shows=no_shows
        )

    async def get_statistics(self) -> WorkReleaseStatistics:
        """Get overall work release statistics."""
        employer_counts = await self.employer_repo.count_by_approval_status()
        assignment_counts = await self.assignment_repo.count_by_status()

        # Get inmates currently at work (departed today, not yet returned)
        today = date.today()
        today_logs = await self.log_repo.get_by_date(today)
        at_work = sum(1 for log in today_logs if log.status == LogStatus.DEPARTED.value)

        # Monthly stats
        year, month = today.year, today.month
        month_counts = await self.log_repo.count_by_status_for_month(year, month)

        return WorkReleaseStatistics(
            total_employers=employer_counts['total'],
            approved_employers=employer_counts['approved'],
            active_assignments=assignment_counts.get(WorkReleaseStatus.ACTIVE.value, 0),
            total_assignments=sum(assignment_counts.values()),
            inmates_at_work_today=at_work,
            late_returns_this_month=month_counts.get(LogStatus.RETURNED_LATE.value, 0),
            no_shows_this_month=month_counts.get(LogStatus.DID_NOT_RETURN.value, 0)
        )

    async def get_daily_report(
        self,
        report_date: Optional[date] = None
    ) -> DailyWorkReleaseReport:
        """Generate daily work release activity report."""
        if report_date is None:
            report_date = date.today()

        logs = await self.log_repo.get_by_date(report_date)
        counts = await self.log_repo.count_by_status_for_date(report_date)

        log_responses = [
            WorkReleaseLogResponse(
                id=log.id,
                assignment_id=log.assignment_id,
                log_date=log.log_date,
                departure_time=log.departure_time,
                expected_return_time=log.expected_return_time,
                actual_return_time=log.actual_return_time,
                status=log.status,
                is_late=log.is_late,
                minutes_late=log.minutes_late,
                verified_by=log.verified_by,
                notes=log.notes,
                inserted_date=log.inserted_date,
                updated_date=log.updated_date
            )
            for log in logs
        ]

        return DailyWorkReleaseReport(
            report_date=report_date,
            departed=counts.get(LogStatus.DEPARTED.value, 0),
            returned_on_time=counts.get(LogStatus.RETURNED_ON_TIME.value, 0),
            returned_late=counts.get(LogStatus.RETURNED_LATE.value, 0),
            did_not_return=counts.get(LogStatus.DID_NOT_RETURN.value, 0),
            still_out=counts.get(LogStatus.DEPARTED.value, 0),
            logs=log_responses
        )
