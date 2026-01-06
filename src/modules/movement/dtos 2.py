"""
Movement DTOs - Pydantic models for validation and serialization.

Status workflow:
SCHEDULED → IN_PROGRESS → COMPLETED
    ↓
CANCELLED (only from SCHEDULED)
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from src.common.enums import MovementType, MovementStatus


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    MovementStatus.SCHEDULED: [MovementStatus.IN_PROGRESS, MovementStatus.CANCELLED],
    MovementStatus.IN_PROGRESS: [MovementStatus.COMPLETED],
    MovementStatus.COMPLETED: [],  # Terminal state
    MovementStatus.CANCELLED: [],  # Terminal state
}


# ============================================================================
# Movement Create/Update DTOs
# ============================================================================

class MovementCreate(BaseModel):
    """Create a new movement."""
    inmate_id: UUID
    movement_type: MovementType
    from_location: str = Field(..., min_length=1, max_length=200)
    to_location: str = Field(..., min_length=1, max_length=200)
    scheduled_time: datetime
    escort_officer_id: Optional[UUID] = None
    vehicle_id: Optional[str] = Field(None, max_length=50)
    court_appearance_id: Optional[UUID] = None
    notes: Optional[str] = None

    @field_validator('from_location', 'to_location')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class MovementUpdate(BaseModel):
    """Update movement details (not status)."""
    scheduled_time: Optional[datetime] = None
    escort_officer_id: Optional[UUID] = None
    vehicle_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovementStatusUpdate(BaseModel):
    """
    Update movement status with workflow validation.

    Includes timestamps for status transitions:
    - IN_PROGRESS: sets departure_time
    - COMPLETED: sets arrival_time
    """
    status: MovementStatus
    departure_time: Optional[datetime] = None  # Set when IN_PROGRESS
    arrival_time: Optional[datetime] = None  # Set when COMPLETED
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_status_timestamps(self):
        """Validate timestamps match status."""
        if self.status == MovementStatus.IN_PROGRESS and not self.departure_time:
            self.departure_time = datetime.utcnow()

        if self.status == MovementStatus.COMPLETED and not self.arrival_time:
            self.arrival_time = datetime.utcnow()

        return self

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Movement Response DTOs
# ============================================================================

class MovementResponse(BaseModel):
    """Movement response."""
    id: UUID
    inmate_id: UUID
    movement_type: MovementType
    status: MovementStatus
    from_location: str
    to_location: str
    scheduled_time: datetime
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    escort_officer_id: Optional[UUID]
    vehicle_id: Optional[str]
    court_appearance_id: Optional[UUID]
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MovementListResponse(BaseModel):
    """List of movements."""
    items: List[MovementResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Movement Summary DTOs
# ============================================================================

class InmateMovementSummary(BaseModel):
    """Summary of an inmate's movements."""
    inmate_id: UUID
    total_movements: int
    scheduled_count: int
    in_progress_count: int
    completed_count: int
    cancelled_count: int
    recent_movements: List[MovementResponse]

    model_config = ConfigDict(from_attributes=True)


class DailyMovementSummary(BaseModel):
    """Summary of movements for a specific date."""
    date: datetime
    total_scheduled: int
    total_in_progress: int
    total_completed: int
    total_cancelled: int
    movements_by_type: dict  # MovementType -> count
    movements: List[MovementResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Movement Filter DTOs
# ============================================================================

class MovementFilter(BaseModel):
    """Filters for querying movements."""
    inmate_id: Optional[UUID] = None
    movement_type: Optional[MovementType] = None
    status: Optional[MovementStatus] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    escort_officer_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
