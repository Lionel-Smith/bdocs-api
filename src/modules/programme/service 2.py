"""
Programme Service - Business logic for rehabilitation programmes.

Implements key operations:
- Programme management (CRUD)
- Session scheduling and tracking
- Enrollment with eligibility and capacity checks
- Attendance recording
- Completion with grade and certification

Enrollment workflow: ENROLLED → ACTIVE → COMPLETED
Alternative paths: WITHDRAWN, SUSPENDED
"""
from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import ProgrammeCategory, SessionStatus, EnrollmentStatus
from src.modules.programme.models import Programme, ProgrammeSession, ProgrammeEnrollment
from src.modules.programme.repository import (
    ProgrammeRepository,
    ProgrammeSessionRepository,
    ProgrammeEnrollmentRepository
)
from src.modules.programme.dtos import (
    ProgrammeCreate,
    ProgrammeUpdate,
    ProgrammeResponse,
    ProgrammeSessionCreate,
    ProgrammeSessionUpdate,
    ProgrammeEnrollmentCreate,
    ProgrammeEnrollmentUpdate,
    ProgrammeEnrollmentStatusUpdate,
    ProgrammeEnrollmentDetailResponse,
    InmateProgrammeSummary,
    ProgrammeStatistics,
    VALID_ENROLLMENT_TRANSITIONS
)


class ProgrammeService:
    """Service for programme operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.programme_repo = ProgrammeRepository(session)
        self.session_repo = ProgrammeSessionRepository(session)
        self.enrollment_repo = ProgrammeEnrollmentRepository(session)

    # ========================================================================
    # Programme CRUD
    # ========================================================================

    async def create_programme(
        self,
        data: ProgrammeCreate,
        created_by: Optional[UUID] = None
    ) -> Programme:
        """Create a new programme."""
        # Check for duplicate code
        existing = await self.programme_repo.get_by_code(data.code)
        if existing:
            raise ValueError(f"Programme with code {data.code} already exists")

        programme = Programme(
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            category=data.category.value,
            provider=data.provider,
            duration_weeks=data.duration_weeks,
            max_participants=data.max_participants,
            eligibility_criteria=data.eligibility_criteria,
            is_active=data.is_active,
            created_by=created_by
        )

        return await self.programme_repo.create(programme)

    async def get_programme(self, programme_id: UUID) -> Optional[Programme]:
        """Get programme by ID."""
        return await self.programme_repo.get_by_id(programme_id)

    async def get_programme_by_code(self, code: str) -> Optional[Programme]:
        """Get programme by code."""
        return await self.programme_repo.get_by_code(code)

    async def get_all_programmes(
        self,
        active_only: bool = False,
        category: Optional[ProgrammeCategory] = None
    ) -> List[Programme]:
        """Get programmes with optional filters."""
        if category:
            return await self.programme_repo.get_by_category(category, active_only)
        elif active_only:
            return await self.programme_repo.get_active()
        else:
            return await self.programme_repo.get_all()

    async def update_programme(
        self,
        programme_id: UUID,
        data: ProgrammeUpdate
    ) -> Optional[Programme]:
        """Update programme fields."""
        programme = await self.programme_repo.get_by_id(programme_id)
        if not programme:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(programme, field):
                if field == 'category' and value:
                    setattr(programme, field, value.value)
                else:
                    setattr(programme, field, value)

        return await self.programme_repo.update(programme)

    async def delete_programme(self, programme_id: UUID) -> bool:
        """Soft delete a programme."""
        programme = await self.programme_repo.get_by_id(programme_id)
        if not programme:
            return False

        # Check for active enrollments
        active_count = await self.programme_repo.get_enrollment_count(programme_id)
        if active_count > 0:
            raise ValueError(
                f"Cannot delete programme with {active_count} active enrollments"
            )

        return await self.programme_repo.delete(programme_id)

    # ========================================================================
    # Session Management
    # ========================================================================

    async def create_session(
        self,
        programme_id: UUID,
        data: ProgrammeSessionCreate
    ) -> ProgrammeSession:
        """Create a new session for a programme."""
        programme = await self.programme_repo.get_by_id(programme_id)
        if not programme:
            raise ValueError(f"Programme not found: {programme_id}")

        if not programme.is_active:
            raise ValueError("Cannot create session for inactive programme")

        session = ProgrammeSession(
            programme_id=programme_id,
            session_date=data.session_date,
            start_time=data.start_time,
            end_time=data.end_time,
            location=data.location,
            instructor_name=data.instructor_name,
            status=SessionStatus.SCHEDULED.value,
            notes=data.notes
        )

        return await self.session_repo.create(session)

    async def get_session(self, session_id: UUID) -> Optional[ProgrammeSession]:
        """Get session by ID."""
        return await self.session_repo.get_by_id(session_id)

    async def get_programme_sessions(
        self,
        programme_id: UUID,
        status: Optional[SessionStatus] = None
    ) -> List[ProgrammeSession]:
        """Get sessions for a programme."""
        return await self.session_repo.get_by_programme(programme_id, status)

    async def update_session(
        self,
        session_id: UUID,
        data: ProgrammeSessionUpdate
    ) -> Optional[ProgrammeSession]:
        """Update session fields."""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(session, field):
                if field == 'status' and value:
                    setattr(session, field, value.value)
                else:
                    setattr(session, field, value)

        return await self.session_repo.update(session)

    async def record_attendance(
        self,
        session_id: UUID,
        attendance_count: int,
        notes: Optional[str] = None
    ) -> ProgrammeSession:
        """
        Record attendance for a session.

        Marks session as COMPLETED and updates attendance count.
        Also updates hours_completed for active enrollments in the programme.
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != SessionStatus.SCHEDULED.value:
            raise ValueError(f"Cannot record attendance for session with status: {session.status}")

        # Update session
        session.status = SessionStatus.COMPLETED.value
        session.attendance_count = attendance_count
        if notes:
            session.notes = notes

        session = await self.session_repo.update(session)

        # Calculate session hours
        session_hours = (
            session.end_time.hour * 60 + session.end_time.minute -
            session.start_time.hour * 60 - session.start_time.minute
        ) // 60  # Convert to hours

        # Update hours for active enrollments
        active_enrollments = await self.enrollment_repo.get_by_programme(
            session.programme_id,
            status=EnrollmentStatus.ACTIVE
        )
        for enrollment in active_enrollments:
            enrollment.hours_completed += session_hours
            await self.enrollment_repo.update(enrollment)

        return session

    # ========================================================================
    # Enrollment Management
    # ========================================================================

    async def enroll_inmate(
        self,
        programme_id: UUID,
        data: ProgrammeEnrollmentCreate,
        enrolled_by: Optional[UUID] = None
    ) -> ProgrammeEnrollment:
        """
        Enroll an inmate in a programme.

        Validates:
        - Programme exists and is active
        - Programme has capacity
        - Inmate not already enrolled in this programme
        - Eligibility criteria (if defined)
        """
        programme = await self.programme_repo.get_by_id(programme_id)
        if not programme:
            raise ValueError(f"Programme not found: {programme_id}")

        if not programme.is_active:
            raise ValueError("Cannot enroll in inactive programme")

        # Check capacity
        current_count = await self.programme_repo.get_enrollment_count(programme_id)
        if current_count >= programme.max_participants:
            raise ValueError(
                f"Programme at capacity ({current_count}/{programme.max_participants})"
            )

        # Check for existing active enrollment
        existing = await self.enrollment_repo.get_active_enrollment(
            programme_id, data.inmate_id
        )
        if existing:
            raise ValueError("Inmate already enrolled in this programme")

        # TODO: Check eligibility criteria if defined
        # This would require accessing the inmate module to check:
        # - Security level
        # - Time served
        # - Disciplinary record
        # - Previous programme completions

        enrollment = ProgrammeEnrollment(
            programme_id=programme_id,
            inmate_id=data.inmate_id,
            enrolled_date=date.today(),
            status=EnrollmentStatus.ENROLLED.value,
            hours_completed=0,
            certificate_issued=False,
            notes=data.notes,
            enrolled_by=enrolled_by
        )

        return await self.enrollment_repo.create(enrollment)

    async def get_enrollment(self, enrollment_id: UUID) -> Optional[ProgrammeEnrollment]:
        """Get enrollment by ID."""
        return await self.enrollment_repo.get_by_id(enrollment_id)

    async def get_programme_enrollments(
        self,
        programme_id: UUID,
        status: Optional[EnrollmentStatus] = None
    ) -> List[ProgrammeEnrollment]:
        """Get enrollments for a programme."""
        return await self.enrollment_repo.get_by_programme(programme_id, status)

    async def update_enrollment(
        self,
        enrollment_id: UUID,
        data: ProgrammeEnrollmentUpdate
    ) -> Optional[ProgrammeEnrollment]:
        """Update enrollment fields (non-status)."""
        enrollment = await self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(enrollment, field):
                setattr(enrollment, field, value)

        return await self.enrollment_repo.update(enrollment)

    async def update_enrollment_status(
        self,
        enrollment_id: UUID,
        data: ProgrammeEnrollmentStatusUpdate
    ) -> ProgrammeEnrollment:
        """
        Update enrollment status with workflow validation.

        Validates transition is allowed per VALID_ENROLLMENT_TRANSITIONS.
        On COMPLETED, sets completion_date and optional grade/certificate.
        """
        enrollment = await self.enrollment_repo.get_by_id(enrollment_id)
        if not enrollment:
            raise ValueError(f"Enrollment not found: {enrollment_id}")

        current_status = EnrollmentStatus(enrollment.status)
        new_status = data.status

        # Validate transition
        self._validate_enrollment_transition(current_status, new_status)

        # Update status
        enrollment.status = new_status.value

        # Update notes if provided
        if data.notes:
            enrollment.notes = data.notes

        # Handle completion
        if new_status == EnrollmentStatus.COMPLETED:
            enrollment.completion_date = date.today()
            if data.grade:
                enrollment.grade = data.grade
            if data.certificate_issued is not None:
                enrollment.certificate_issued = data.certificate_issued

        return await self.enrollment_repo.update(enrollment)

    def _validate_enrollment_transition(
        self,
        current_status: EnrollmentStatus,
        new_status: EnrollmentStatus
    ) -> None:
        """Validate enrollment status transition."""
        allowed_transitions = VALID_ENROLLMENT_TRANSITIONS.get(current_status, [])

        if new_status not in allowed_transitions:
            allowed_str = ", ".join([s.value for s in allowed_transitions]) or "none"
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}. "
                f"Allowed transitions: {allowed_str}"
            )

    async def complete_enrollment(
        self,
        enrollment_id: UUID,
        grade: Optional[str] = None,
        certificate_issued: bool = False,
        notes: Optional[str] = None
    ) -> ProgrammeEnrollment:
        """
        Mark an enrollment as completed.

        Shorthand for update_enrollment_status with COMPLETED status.
        """
        return await self.update_enrollment_status(
            enrollment_id,
            ProgrammeEnrollmentStatusUpdate(
                status=EnrollmentStatus.COMPLETED,
                grade=grade,
                certificate_issued=certificate_issued,
                notes=notes
            )
        )

    # ========================================================================
    # Query Methods
    # ========================================================================

    async def get_inmate_enrollments(
        self,
        inmate_id: UUID
    ) -> List[ProgrammeEnrollment]:
        """Get all enrollments for an inmate."""
        return await self.enrollment_repo.get_by_inmate(inmate_id)

    async def get_upcoming_sessions(
        self,
        programme_id: Optional[UUID] = None,
        days: int = 7
    ) -> List[ProgrammeSession]:
        """Get upcoming sessions."""
        return await self.session_repo.get_upcoming(programme_id, days)

    # ========================================================================
    # Summary and Statistics
    # ========================================================================

    async def get_inmate_summary(self, inmate_id: UUID) -> InmateProgrammeSummary:
        """Get programme summary for an inmate."""
        enrollments = await self.enrollment_repo.get_by_inmate(inmate_id)
        counts = await self.enrollment_repo.count_by_inmate_status(inmate_id)

        # Build detailed response with programme info
        detailed_enrollments = []
        for enrollment in enrollments:
            programme = await self.programme_repo.get_by_id(enrollment.programme_id)
            detail = ProgrammeEnrollmentDetailResponse(
                id=enrollment.id,
                programme_id=enrollment.programme_id,
                inmate_id=enrollment.inmate_id,
                enrolled_date=enrollment.enrolled_date,
                status=EnrollmentStatus(enrollment.status),
                completion_date=enrollment.completion_date,
                grade=enrollment.grade,
                certificate_issued=enrollment.certificate_issued,
                hours_completed=enrollment.hours_completed,
                notes=enrollment.notes,
                enrolled_by=enrollment.enrolled_by,
                inserted_date=enrollment.inserted_date,
                updated_date=enrollment.updated_date,
                programme=ProgrammeResponse.model_validate(programme) if programme else None
            )
            detailed_enrollments.append(detail)

        return InmateProgrammeSummary(
            inmate_id=inmate_id,
            total_enrollments=counts["total"],
            active_enrollments=counts["active"],
            completed_programmes=counts["completed"],
            withdrawn_programmes=counts["withdrawn"],
            total_hours_completed=counts["hours_completed"],
            certificates_earned=counts["certificates_earned"],
            enrollments=detailed_enrollments
        )

    async def get_statistics(self) -> ProgrammeStatistics:
        """Get overall programme statistics."""
        all_programmes = await self.programme_repo.get_all()
        active_programmes = await self.programme_repo.get_active()
        by_category = await self.programme_repo.count_by_category()
        by_status = await self.enrollment_repo.count_by_status()
        completed_this_year = await self.enrollment_repo.count_completed_this_year()
        most_popular = await self.enrollment_repo.get_most_popular_programmes()

        total_enrollments = sum(by_status.values())
        active_enrollments = (
            by_status.get(EnrollmentStatus.ENROLLED.value, 0) +
            by_status.get(EnrollmentStatus.ACTIVE.value, 0)
        )

        # Calculate completion rate
        completed = by_status.get(EnrollmentStatus.COMPLETED.value, 0)
        terminal = completed + by_status.get(EnrollmentStatus.WITHDRAWN.value, 0)
        completion_rate = (completed / terminal * 100) if terminal > 0 else None

        return ProgrammeStatistics(
            total_programmes=len(all_programmes),
            active_programmes=len(active_programmes),
            by_category=by_category,
            total_enrollments=total_enrollments,
            active_enrollments=active_enrollments,
            completed_this_year=completed_this_year,
            average_completion_rate=completion_rate,
            most_popular_programmes=most_popular
        )
