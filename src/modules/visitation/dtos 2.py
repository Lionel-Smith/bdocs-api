"""
Visitation DTOs - Data Transfer Objects for visitation management.

Provides structured data validation for visitor registration,
visit scheduling, and visit logging.
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.common.enums import (
    Relationship, IDType, CheckStatus,
    VisitType, VisitStatus
)


# =============================================================================
# Approved Visitor DTOs
# =============================================================================

class VisitorCreateDTO(BaseModel):
    """Register a new visitor for an inmate."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID = Field(..., description="Inmate the visitor is registered for")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    relationship: Relationship = Field(..., description="Relationship to inmate")
    phone: str = Field(..., max_length=20, description="Format: (242) XXX-XXXX")
    email: Optional[EmailStr] = None
    id_type: IDType = Field(..., description="Type of identification document")
    id_number: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date = Field(..., description="Visitor date of birth")
    photo_url: Optional[str] = Field(None, max_length=500)


class VisitorUpdateDTO(BaseModel):
    """Update visitor information."""
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    relationship: Optional[Relationship] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    id_type: Optional[IDType] = None
    id_number: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class VisitorApprovalDTO(BaseModel):
    """Approve a visitor after background check."""
    model_config = ConfigDict(from_attributes=True)

    background_check_date: date = Field(..., description="Date background check was completed")
    background_check_status: CheckStatus = Field(
        default=CheckStatus.APPROVED,
        description="Result of background check"
    )


class VisitorDenialDTO(BaseModel):
    """Deny a visitor."""
    model_config = ConfigDict(from_attributes=True)

    denied_reason: str = Field(..., min_length=1, max_length=1000)
    background_check_date: Optional[date] = Field(None, description="Date if check was done")


class VisitorDTO(BaseModel):
    """Visitor response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None  # Computed
    first_name: str
    last_name: str
    full_name: str  # Computed
    relationship: Relationship
    phone: str
    email: Optional[str] = None
    id_type: IDType
    id_number: str
    date_of_birth: date
    age: int  # Computed
    photo_url: Optional[str] = None
    background_check_date: Optional[date] = None
    background_check_status: CheckStatus
    is_approved: bool
    approval_date: Optional[date] = None
    approved_by: Optional[UUID] = None
    approver_name: Optional[str] = None
    denied_reason: Optional[str] = None
    is_active: bool

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class VisitorListDTO(BaseModel):
    """Minimal visitor info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    relationship: Relationship
    background_check_status: CheckStatus
    is_approved: bool
    is_active: bool


# =============================================================================
# Visit Schedule DTOs
# =============================================================================

class VisitScheduleCreateDTO(BaseModel):
    """Schedule a new visit."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID = Field(..., description="Inmate to visit")
    visitor_id: UUID = Field(..., description="Approved visitor")
    scheduled_date: date = Field(..., description="Date of visit")
    scheduled_time: time = Field(..., description="Start time of visit")
    duration_minutes: int = Field(60, ge=15, le=240, description="Duration in minutes")
    visit_type: VisitType = Field(default=VisitType.GENERAL)
    location: str = Field(default="Main Visitation Room", max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)


class VisitScheduleUpdateDTO(BaseModel):
    """Update a scheduled visit."""
    model_config = ConfigDict(from_attributes=True)

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=240)
    visit_type: Optional[VisitType] = None
    location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)


class VisitCancelDTO(BaseModel):
    """Cancel a scheduled visit."""
    model_config = ConfigDict(from_attributes=True)

    cancelled_reason: str = Field(..., min_length=1, max_length=500)


class VisitScheduleDTO(BaseModel):
    """Visit schedule response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    inmate_booking_number: Optional[str] = None
    visitor_id: UUID
    visitor_name: Optional[str] = None
    visitor_relationship: Optional[Relationship] = None
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    visit_type: VisitType
    status: VisitStatus
    location: str
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    notes: Optional[str] = None
    created_by: UUID
    creator_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class VisitScheduleListDTO(BaseModel):
    """Minimal visit schedule info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_name: str
    visitor_name: str
    scheduled_date: date
    scheduled_time: time
    visit_type: VisitType
    status: VisitStatus
    location: str


# =============================================================================
# Visit Log DTOs
# =============================================================================

class CheckInDTO(BaseModel):
    """Check in a visitor."""
    model_config = ConfigDict(from_attributes=True)

    visitor_searched: bool = Field(default=True)
    items_stored: Optional[List[dict]] = Field(
        None,
        description="Personal items stored, e.g., [{'item': 'phone', 'description': 'iPhone'}]"
    )
    notes: Optional[str] = Field(None, max_length=1000)


class CheckOutDTO(BaseModel):
    """Check out a visitor."""
    model_config = ConfigDict(from_attributes=True)

    contraband_found: bool = Field(default=False)
    incident_id: Optional[UUID] = Field(None, description="Link to incident if one occurred")
    notes: Optional[str] = Field(None, max_length=1000)


class VisitLogDTO(BaseModel):
    """Visit log response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_schedule_id: UUID
    checked_in_at: datetime
    checked_out_at: Optional[datetime] = None
    visit_duration_minutes: Optional[int] = None
    visitor_searched: bool
    items_stored: Optional[List[dict]] = None
    contraband_found: bool
    incident_id: Optional[UUID] = None
    notes: Optional[str] = None
    processed_by: UUID
    processor_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


# =============================================================================
# Today's Visits DTO
# =============================================================================

class TodaysVisitDTO(BaseModel):
    """Visit information for daily dashboard."""
    model_config = ConfigDict(from_attributes=True)

    visit_id: UUID
    inmate_id: UUID
    inmate_name: str
    inmate_booking_number: str
    visitor_id: UUID
    visitor_name: str
    relationship: Relationship
    scheduled_time: time
    duration_minutes: int
    visit_type: VisitType
    status: VisitStatus
    location: str
    is_checked_in: bool
    checked_in_at: Optional[datetime] = None


# =============================================================================
# Statistics DTOs
# =============================================================================

class VisitationStatisticsDTO(BaseModel):
    """Visitation statistics summary."""
    model_config = ConfigDict(from_attributes=True)

    # Visitor counts
    total_approved_visitors: int
    pending_approval: int
    active_visitors: int

    # Today's visits
    visits_scheduled_today: int
    visits_completed_today: int
    visits_in_progress: int
    no_shows_today: int
    cancellations_today: int

    # Visit types
    by_visit_type: dict  # VisitType -> count

    # Security stats
    contraband_incidents_week: int
    total_visitors_searched_today: int

    # Average metrics
    average_visit_duration_minutes: float
