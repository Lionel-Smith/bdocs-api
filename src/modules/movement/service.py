"""
Movement Service - Business logic for movement tracking.

Implements status workflow validation:
SCHEDULED → IN_PROGRESS → COMPLETED
    ↓
CANCELLED (only from SCHEDULED)

Key features:
- Status transition validation
- Auto-timestamps for status changes
- Conflict detection (inmate already moving)
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import MovementType, MovementStatus
from src.modules.movement.models import Movement
from src.modules.movement.repository import MovementRepository
from src.modules.movement.dtos import (
    MovementCreate,
    MovementUpdate,
    MovementStatusUpdate,
    MovementResponse,
    MovementListResponse,
    InmateMovementSummary,
    DailyMovementSummary,
    MovementFilter,
    VALID_STATUS_TRANSITIONS,
)


# ============================================================================
# Custom Exceptions
# ============================================================================

class MovementNotFoundError(Exception):
    """Raised when a movement record is not found."""
    pass


class InvalidStatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


class InmateAlreadyMovingError(Exception):
    """Raised when inmate already has an active movement."""
    pass


# ============================================================================
# Movement Service
# ============================================================================

class MovementService:
    """Service layer for movement operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = MovementRepository(session)

    # ------------------------------------------------------------------------
    # Status Workflow Validation
    # ------------------------------------------------------------------------

    def validate_status_transition(
        self,
        current_status: MovementStatus,
        new_status: MovementStatus
    ) -> bool:
        """
        Validate a status transition is allowed.

        Valid transitions:
        - SCHEDULED → IN_PROGRESS, CANCELLED
        - IN_PROGRESS → COMPLETED
        - COMPLETED → (none, terminal)
        - CANCELLED → (none, terminal)

        Raises:
            InvalidStatusTransitionError if transition is not valid
        """
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Cannot transition from {current_status.value} to {new_status.value}. "
                f"Allowed transitions: {[s.value for s in allowed] if allowed else 'none (terminal state)'}"
            )

        return True

    # ------------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------------

    async def create_movement(
        self,
        data: MovementCreate,
        created_by: Optional[UUID] = None
    ) -> MovementResponse:
        """
        Create a new movement record.

        Validates that inmate doesn't already have an active movement.
        """
        # Check for existing active movement
        has_active = await self.repository.has_active_movement(data.inmate_id)
        if has_active:
            raise InmateAlreadyMovingError(
                f"Inmate {data.inmate_id} already has an active movement"
            )

        movement = Movement(
            inmate_id=data.inmate_id,
            movement_type=data.movement_type.value,
            status=MovementStatus.SCHEDULED.value,
            from_location=data.from_location,
            to_location=data.to_location,
            scheduled_time=data.scheduled_time,
            escort_officer_id=data.escort_officer_id,
            vehicle_id=data.vehicle_id,
            court_appearance_id=data.court_appearance_id,
            notes=data.notes,
            created_by=created_by,
            inserted_by=str(created_by) if created_by else 'system'
        )

        created = await self.repository.create(movement)
        return MovementResponse.model_validate(created)

    async def get_movement(self, movement_id: UUID) -> MovementResponse:
        """Get a movement by ID."""
        movement = await self.repository.get_by_id(movement_id)
        if not movement or movement.is_deleted:
            raise MovementNotFoundError(f"Movement {movement_id} not found")
        return MovementResponse.model_validate(movement)

    async def update_movement(
        self,
        movement_id: UUID,
        data: MovementUpdate,
        updated_by: Optional[str] = None
    ) -> MovementResponse:
        """Update movement details (not status)."""
        movement = await self.repository.get_by_id(movement_id)
        if not movement or movement.is_deleted:
            raise MovementNotFoundError(f"Movement {movement_id} not found")

        # Can only update scheduled movements
        if movement.status != MovementStatus.SCHEDULED.value:
            raise InvalidStatusTransitionError(
                f"Cannot update movement in {movement.status} status. "
                "Only SCHEDULED movements can be updated."
            )

        # Apply updates
        if data.scheduled_time is not None:
            movement.scheduled_time = data.scheduled_time
        if data.escort_officer_id is not None:
            movement.escort_officer_id = data.escort_officer_id
        if data.vehicle_id is not None:
            movement.vehicle_id = data.vehicle_id
        if data.notes is not None:
            movement.notes = data.notes

        movement.updated_by = updated_by
        movement.updated_date = datetime.utcnow()

        updated = await self.repository.update(movement)
        return MovementResponse.model_validate(updated)

    async def update_status(
        self,
        movement_id: UUID,
        data: MovementStatusUpdate,
        updated_by: Optional[str] = None
    ) -> MovementResponse:
        """
        Update movement status with workflow validation.

        Auto-sets timestamps:
        - IN_PROGRESS: sets departure_time
        - COMPLETED: sets arrival_time
        """
        movement = await self.repository.get_by_id(movement_id)
        if not movement or movement.is_deleted:
            raise MovementNotFoundError(f"Movement {movement_id} not found")

        current_status = MovementStatus(movement.status)
        new_status = data.status

        # Validate transition
        self.validate_status_transition(current_status, new_status)

        # Update status
        movement.status = new_status.value

        # Set timestamps based on new status
        if new_status == MovementStatus.IN_PROGRESS:
            movement.departure_time = data.departure_time or datetime.utcnow()
        elif new_status == MovementStatus.COMPLETED:
            movement.arrival_time = data.arrival_time or datetime.utcnow()

        # Add notes if provided
        if data.notes:
            existing_notes = movement.notes or ""
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            movement.notes = f"{existing_notes}\n[{timestamp}] Status → {new_status.value}: {data.notes}".strip()

        movement.updated_by = updated_by
        movement.updated_date = datetime.utcnow()

        updated = await self.repository.update(movement)
        return MovementResponse.model_validate(updated)

    async def delete_movement(
        self,
        movement_id: UUID,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Soft delete a movement (only if SCHEDULED or CANCELLED)."""
        movement = await self.repository.get_by_id(movement_id)
        if not movement or movement.is_deleted:
            raise MovementNotFoundError(f"Movement {movement_id} not found")

        # Can only delete scheduled or cancelled movements
        if movement.status not in [MovementStatus.SCHEDULED.value, MovementStatus.CANCELLED.value]:
            raise InvalidStatusTransitionError(
                f"Cannot delete movement in {movement.status} status. "
                "Only SCHEDULED or CANCELLED movements can be deleted."
            )

        movement.is_deleted = True
        movement.deleted_at = datetime.utcnow()
        movement.deleted_by = deleted_by

        await self.repository.update(movement)
        return True

    # ------------------------------------------------------------------------
    # Query Operations
    # ------------------------------------------------------------------------

    async def get_movements_by_inmate(
        self,
        inmate_id: UUID
    ) -> MovementListResponse:
        """Get all movements for an inmate."""
        movements = await self.repository.get_by_inmate(inmate_id)
        return MovementListResponse(
            items=[MovementResponse.model_validate(m) for m in movements],
            total=len(movements)
        )

    async def get_movements_by_status(
        self,
        status: MovementStatus
    ) -> MovementListResponse:
        """Get all movements with a specific status."""
        movements = await self.repository.get_by_status(status)
        return MovementListResponse(
            items=[MovementResponse.model_validate(m) for m in movements],
            total=len(movements)
        )

    async def get_scheduled_movements(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> MovementListResponse:
        """Get scheduled movements within a date range."""
        movements = await self.repository.get_scheduled_movements(from_date, to_date)
        return MovementListResponse(
            items=[MovementResponse.model_validate(m) for m in movements],
            total=len(movements)
        )

    async def get_in_progress_movements(self) -> MovementListResponse:
        """Get all movements currently in progress."""
        movements = await self.repository.get_in_progress_movements()
        return MovementListResponse(
            items=[MovementResponse.model_validate(m) for m in movements],
            total=len(movements)
        )

    async def search_movements(
        self,
        filters: MovementFilter,
        skip: int = 0,
        limit: int = 100
    ) -> MovementListResponse:
        """Search movements with filters."""
        movements = await self.repository.get_filtered_movements(
            inmate_id=filters.inmate_id,
            movement_type=filters.movement_type,
            status=filters.status,
            from_date=filters.from_date,
            to_date=filters.to_date,
            escort_officer_id=filters.escort_officer_id,
            skip=skip,
            limit=limit
        )
        return MovementListResponse(
            items=[MovementResponse.model_validate(m) for m in movements],
            total=len(movements)
        )

    # ------------------------------------------------------------------------
    # Summary Operations
    # ------------------------------------------------------------------------

    async def get_inmate_movement_summary(
        self,
        inmate_id: UUID,
        recent_limit: int = 5
    ) -> InmateMovementSummary:
        """Get movement summary for an inmate."""
        movements = await self.repository.get_by_inmate(inmate_id)
        counts = await self.repository.count_by_status(inmate_id)

        return InmateMovementSummary(
            inmate_id=inmate_id,
            total_movements=len(movements),
            scheduled_count=counts.get(MovementStatus.SCHEDULED.value, 0),
            in_progress_count=counts.get(MovementStatus.IN_PROGRESS.value, 0),
            completed_count=counts.get(MovementStatus.COMPLETED.value, 0),
            cancelled_count=counts.get(MovementStatus.CANCELLED.value, 0),
            recent_movements=[
                MovementResponse.model_validate(m) for m in movements[:recent_limit]
            ]
        )

    async def get_daily_movement_summary(
        self,
        target_date: date
    ) -> DailyMovementSummary:
        """Get movement summary for a specific date."""
        movements = await self.repository.get_movements_for_date(target_date)
        counts = await self.repository.count_by_status()
        type_counts = await self.repository.count_by_type_for_date(target_date)

        return DailyMovementSummary(
            date=datetime.combine(target_date, datetime.min.time()),
            total_scheduled=sum(1 for m in movements if m.status == MovementStatus.SCHEDULED.value),
            total_in_progress=sum(1 for m in movements if m.status == MovementStatus.IN_PROGRESS.value),
            total_completed=sum(1 for m in movements if m.status == MovementStatus.COMPLETED.value),
            total_cancelled=sum(1 for m in movements if m.status == MovementStatus.CANCELLED.value),
            movements_by_type=type_counts,
            movements=[MovementResponse.model_validate(m) for m in movements]
        )
