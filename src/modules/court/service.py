"""
Court Service - Business logic for court cases and appearances.

Key features:
- Court case management
- Appearance scheduling with auto-Movement creation
- Outcome recording
- Upcoming appearances queries
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import (
    CourtType, CaseStatus, AppearanceType, AppearanceOutcome,
    MovementType, MovementStatus
)
from src.modules.court.models import CourtCase, CourtAppearance
from src.modules.court.repository import CourtCaseRepository, CourtAppearanceRepository
from src.modules.court.dtos import (
    CourtCaseCreate,
    CourtCaseUpdate,
    CourtCaseResponse,
    CourtCaseListResponse,
    CourtAppearanceCreate,
    CourtAppearanceUpdate,
    CourtAppearanceOutcomeUpdate,
    CourtAppearanceResponse,
    CourtAppearanceListResponse,
    InmateCourtSummary,
    UpcomingAppearancesResponse,
)
from src.modules.movement.models import Movement
from src.modules.movement.repository import MovementRepository


# ============================================================================
# Custom Exceptions
# ============================================================================

class CourtCaseNotFoundError(Exception):
    """Raised when a court case is not found."""
    pass


class CourtAppearanceNotFoundError(Exception):
    """Raised when a court appearance is not found."""
    pass


class DuplicateCaseNumberError(Exception):
    """Raised when case number already exists."""
    pass


class InvalidAppearanceError(Exception):
    """Raised for invalid appearance operations."""
    pass


# Default transport origin
DEFAULT_FACILITY = "Fox Hill Correctional Facility"


# ============================================================================
# Court Service
# ============================================================================

class CourtService:
    """Service layer for court operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.case_repo = CourtCaseRepository(session)
        self.appearance_repo = CourtAppearanceRepository(session)
        self.movement_repo = MovementRepository(session)

    # ------------------------------------------------------------------------
    # Court Case Operations
    # ------------------------------------------------------------------------

    async def create_case(
        self,
        data: CourtCaseCreate,
        created_by: Optional[str] = None
    ) -> CourtCaseResponse:
        """Create a new court case."""
        # Check for duplicate case number
        existing = await self.case_repo.get_by_case_number(data.case_number)
        if existing:
            raise DuplicateCaseNumberError(
                f"Case number {data.case_number} already exists"
            )

        # Convert charges to dict list
        charges_list = [c.model_dump() for c in data.charges]

        court_case = CourtCase(
            inmate_id=data.inmate_id,
            case_number=data.case_number.upper(),
            court_type=data.court_type.value,
            charges=charges_list,
            filing_date=data.filing_date,
            status=CaseStatus.PENDING.value,
            presiding_judge=data.presiding_judge,
            prosecutor=data.prosecutor,
            defense_attorney=data.defense_attorney,
            notes=data.notes,
            inserted_by=created_by
        )

        created = await self.case_repo.create(court_case)
        return CourtCaseResponse.model_validate(created)

    async def get_case(self, case_id: UUID) -> CourtCaseResponse:
        """Get a court case by ID."""
        court_case = await self.case_repo.get_by_id(case_id)
        if not court_case or court_case.is_deleted:
            raise CourtCaseNotFoundError(f"Court case {case_id} not found")
        return CourtCaseResponse.model_validate(court_case)

    async def get_case_by_number(self, case_number: str) -> CourtCaseResponse:
        """Get a court case by case number."""
        court_case = await self.case_repo.get_by_case_number(case_number)
        if not court_case:
            raise CourtCaseNotFoundError(f"Court case {case_number} not found")
        return CourtCaseResponse.model_validate(court_case)

    async def update_case(
        self,
        case_id: UUID,
        data: CourtCaseUpdate,
        updated_by: Optional[str] = None
    ) -> CourtCaseResponse:
        """Update a court case."""
        court_case = await self.case_repo.get_by_id(case_id)
        if not court_case or court_case.is_deleted:
            raise CourtCaseNotFoundError(f"Court case {case_id} not found")

        # Apply updates
        if data.status is not None:
            court_case.status = data.status.value
        if data.presiding_judge is not None:
            court_case.presiding_judge = data.presiding_judge
        if data.prosecutor is not None:
            court_case.prosecutor = data.prosecutor
        if data.defense_attorney is not None:
            court_case.defense_attorney = data.defense_attorney
        if data.charges is not None:
            court_case.charges = [c.model_dump() for c in data.charges]
        if data.notes is not None:
            court_case.notes = data.notes

        court_case.updated_by = updated_by
        court_case.updated_date = datetime.utcnow()

        updated = await self.case_repo.update(court_case)
        return CourtCaseResponse.model_validate(updated)

    async def get_cases_by_inmate(self, inmate_id: UUID) -> CourtCaseListResponse:
        """Get all court cases for an inmate."""
        cases = await self.case_repo.get_by_inmate(inmate_id)
        return CourtCaseListResponse(
            items=[CourtCaseResponse.model_validate(c) for c in cases],
            total=len(cases)
        )

    async def get_all_cases(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> CourtCaseListResponse:
        """Get all court cases with pagination."""
        cases = await self.case_repo.get_all(skip=skip, limit=limit)
        return CourtCaseListResponse(
            items=[CourtCaseResponse.model_validate(c) for c in cases],
            total=len(cases)
        )

    # ------------------------------------------------------------------------
    # Court Appearance Operations
    # ------------------------------------------------------------------------

    async def create_appearance(
        self,
        data: CourtAppearanceCreate,
        created_by: Optional[UUID] = None
    ) -> CourtAppearanceResponse:
        """
        Create a new court appearance.

        If auto_create_movement is True, automatically schedules a
        COURT_TRANSPORT movement for the appearance date.
        """
        # Verify case exists
        court_case = await self.case_repo.get_by_id(data.court_case_id)
        if not court_case or court_case.is_deleted:
            raise CourtCaseNotFoundError(f"Court case {data.court_case_id} not found")

        # Create the appearance
        appearance = CourtAppearance(
            court_case_id=data.court_case_id,
            inmate_id=data.inmate_id,
            appearance_date=data.appearance_date,
            appearance_type=data.appearance_type.value,
            court_location=data.court_location,
            notes=data.notes,
            created_by=created_by,
            inserted_by=str(created_by) if created_by else 'system'
        )

        # Auto-create movement if requested
        movement_id = None
        if data.auto_create_movement:
            movement = await self._create_court_transport(
                inmate_id=data.inmate_id,
                appearance_date=data.appearance_date,
                court_location=data.court_location,
                created_by=created_by
            )
            movement_id = movement.id
            appearance.movement_id = movement_id

        created = await self.appearance_repo.create(appearance)

        # Update movement with appearance ID if created
        if movement_id:
            movement = await self.movement_repo.get_by_id(movement_id)
            if movement:
                movement.court_appearance_id = created.id
                await self.movement_repo.update(movement)

        response = CourtAppearanceResponse.model_validate(created)
        response.case_number = court_case.case_number
        return response

    async def _create_court_transport(
        self,
        inmate_id: UUID,
        appearance_date: datetime,
        court_location: str,
        created_by: Optional[UUID] = None
    ) -> Movement:
        """Create a COURT_TRANSPORT movement for an appearance."""
        # Schedule transport 1 hour before appearance
        transport_time = appearance_date - timedelta(hours=1)

        movement = Movement(
            inmate_id=inmate_id,
            movement_type=MovementType.COURT_TRANSPORT.value,
            status=MovementStatus.SCHEDULED.value,
            from_location=DEFAULT_FACILITY,
            to_location=court_location,
            scheduled_time=transport_time,
            created_by=created_by,
            inserted_by=str(created_by) if created_by else 'system',
            notes=f"Auto-created for court appearance at {appearance_date.strftime('%Y-%m-%d %H:%M')}"
        )

        return await self.movement_repo.create(movement)

    async def get_appearance(self, appearance_id: UUID) -> CourtAppearanceResponse:
        """Get a court appearance by ID."""
        appearance = await self.appearance_repo.get_by_id(appearance_id)
        if not appearance or appearance.is_deleted:
            raise CourtAppearanceNotFoundError(
                f"Court appearance {appearance_id} not found"
            )

        response = CourtAppearanceResponse.model_validate(appearance)

        # Get case number
        if appearance.court_case_id:
            court_case = await self.case_repo.get_by_id(appearance.court_case_id)
            if court_case:
                response.case_number = court_case.case_number

        return response

    async def update_appearance(
        self,
        appearance_id: UUID,
        data: CourtAppearanceUpdate,
        updated_by: Optional[str] = None
    ) -> CourtAppearanceResponse:
        """Update a court appearance (before it occurs)."""
        appearance = await self.appearance_repo.get_by_id(appearance_id)
        if not appearance or appearance.is_deleted:
            raise CourtAppearanceNotFoundError(
                f"Court appearance {appearance_id} not found"
            )

        # Can only update if no outcome yet
        if appearance.outcome is not None:
            raise InvalidAppearanceError(
                "Cannot update appearance that already has an outcome"
            )

        # Apply updates
        if data.appearance_date is not None:
            appearance.appearance_date = data.appearance_date
            # Also update linked movement if exists
            if appearance.movement_id:
                movement = await self.movement_repo.get_by_id(appearance.movement_id)
                if movement and movement.status == MovementStatus.SCHEDULED.value:
                    movement.scheduled_time = data.appearance_date - timedelta(hours=1)
                    await self.movement_repo.update(movement)

        if data.court_location is not None:
            appearance.court_location = data.court_location
            # Update movement destination
            if appearance.movement_id:
                movement = await self.movement_repo.get_by_id(appearance.movement_id)
                if movement and movement.status == MovementStatus.SCHEDULED.value:
                    movement.to_location = data.court_location
                    await self.movement_repo.update(movement)

        if data.notes is not None:
            appearance.notes = data.notes

        appearance.updated_by = updated_by
        appearance.updated_date = datetime.utcnow()

        updated = await self.appearance_repo.update(appearance)
        return CourtAppearanceResponse.model_validate(updated)

    async def record_outcome(
        self,
        appearance_id: UUID,
        data: CourtAppearanceOutcomeUpdate,
        updated_by: Optional[str] = None
    ) -> CourtAppearanceResponse:
        """Record the outcome of a court appearance."""
        appearance = await self.appearance_repo.get_by_id(appearance_id)
        if not appearance or appearance.is_deleted:
            raise CourtAppearanceNotFoundError(
                f"Court appearance {appearance_id} not found"
            )

        # Can only record outcome once
        if appearance.outcome is not None:
            raise InvalidAppearanceError(
                f"Appearance already has outcome: {appearance.outcome}"
            )

        # Record outcome
        appearance.outcome = data.outcome.value

        if data.next_appearance_date:
            appearance.next_appearance_date = data.next_appearance_date

        if data.notes:
            existing_notes = appearance.notes or ""
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            appearance.notes = f"{existing_notes}\n[{timestamp}] Outcome: {data.outcome.value} - {data.notes}".strip()

        appearance.updated_by = updated_by
        appearance.updated_date = datetime.utcnow()

        updated = await self.appearance_repo.update(appearance)
        return CourtAppearanceResponse.model_validate(updated)

    async def get_appearances_by_inmate(
        self,
        inmate_id: UUID
    ) -> CourtAppearanceListResponse:
        """Get all appearances for an inmate."""
        appearances = await self.appearance_repo.get_by_inmate(inmate_id)
        return CourtAppearanceListResponse(
            items=[CourtAppearanceResponse.model_validate(a) for a in appearances],
            total=len(appearances)
        )

    async def get_appearances_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime
    ) -> CourtAppearanceListResponse:
        """Get appearances within a date range."""
        appearances = await self.appearance_repo.get_by_date_range(from_date, to_date)
        return CourtAppearanceListResponse(
            items=[CourtAppearanceResponse.model_validate(a) for a in appearances],
            total=len(appearances)
        )

    async def get_upcoming_appearances(
        self,
        days_ahead: int = 7
    ) -> UpcomingAppearancesResponse:
        """Get upcoming appearances (no outcome yet)."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        appearances = await self.appearance_repo.get_upcoming_appearances(days_ahead)

        return UpcomingAppearancesResponse(
            items=[CourtAppearanceResponse.model_validate(a) for a in appearances],
            total=len(appearances),
            date_range_start=now,
            date_range_end=end_date
        )

    # ------------------------------------------------------------------------
    # Summary Operations
    # ------------------------------------------------------------------------

    async def get_inmate_court_summary(
        self,
        inmate_id: UUID,
        recent_limit: int = 5
    ) -> InmateCourtSummary:
        """Get complete court summary for an inmate."""
        cases = await self.case_repo.get_by_inmate(inmate_id)
        appearances = await self.appearance_repo.get_by_inmate(inmate_id)

        active_count = sum(
            1 for c in cases
            if c.status in [CaseStatus.PENDING.value, CaseStatus.ACTIVE.value]
        )

        upcoming_count = sum(
            1 for a in appearances
            if a.outcome is None and a.appearance_date > datetime.utcnow()
        )

        return InmateCourtSummary(
            inmate_id=inmate_id,
            total_cases=len(cases),
            active_cases=active_count,
            total_appearances=len(appearances),
            upcoming_appearances=upcoming_count,
            cases=[CourtCaseResponse.model_validate(c) for c in cases],
            recent_appearances=[
                CourtAppearanceResponse.model_validate(a)
                for a in appearances[:recent_limit]
            ]
        )
