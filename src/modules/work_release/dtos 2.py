"""
Work Release DTOs - Data transfer objects for work release operations.

Three DTO families:
1. Employer DTOs: CRUD + approval workflow
2. Assignment DTOs: Workflow status management
3. Log DTOs: Departure/return tracking

Key validations:
- Phone format: (242) XXX-XXXX (Bahamas)
- Work schedule: JSONB with day-of-week keys
- Status transitions follow defined workflows
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Employer DTOs
# ============================================================================

class WorkReleaseEmployerCreate(BaseModel):
    """Create a new work release employer."""
    name: str = Field(..., min_length=1, max_length=200)
    business_type: str = Field(..., min_length=1, max_length=100)
    contact_name: str = Field(..., min_length=1, max_length=200)
    contact_phone: str = Field(..., min_length=10, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: str = Field(..., min_length=1)
    notes: Optional[str] = None

    @field_validator('contact_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Bahamas phone format."""
        # Allow formats: (242) XXX-XXXX or 242-XXX-XXXX or plain digits
        clean = ''.join(c for c in v if c.isdigit())
        if len(clean) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v


class WorkReleaseEmployerUpdate(BaseModel):
    """Update an existing employer."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('contact_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = ''.join(c for c in v if c.isdigit())
        if len(clean) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v


class WorkReleaseEmployerApprove(BaseModel):
    """Approve an employer for work release programme."""
    mou_signed: bool = Field(..., description="MOU must be signed for approval")
    mou_expiry_date: Optional[date] = Field(None, description="MOU expiration date")
    notes: Optional[str] = None

    @field_validator('mou_expiry_date')
    @classmethod
    def validate_mou_expiry(cls, v: Optional[date], info) -> Optional[date]:
        """MOU expiry must be in the future."""
        if v and v <= date.today():
            raise ValueError('MOU expiry date must be in the future')
        return v


class WorkReleaseEmployerResponse(BaseModel):
    """Employer response with computed properties."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    business_type: str
    contact_name: str
    contact_phone: str
    contact_email: Optional[str]
    address: str
    is_approved: bool
    approval_date: Optional[date]
    approved_by: Optional[UUID]
    mou_signed: bool
    mou_expiry_date: Optional[date]
    is_mou_valid: bool
    can_accept_inmates: bool
    is_active: bool
    notes: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]


class WorkReleaseEmployerListResponse(BaseModel):
    """Paginated list of employers."""
    items: List[WorkReleaseEmployerResponse]
    total: int


# ============================================================================
# Assignment DTOs
# ============================================================================

class WorkSchedule(BaseModel):
    """Daily work schedule entry."""
    start: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="Format: HH:MM")
    end: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="Format: HH:MM")


class WorkReleaseAssignmentCreate(BaseModel):
    """Create a work release assignment."""
    inmate_id: UUID
    employer_id: UUID
    position_title: str = Field(..., min_length=1, max_length=200)
    start_date: date
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    work_schedule: Optional[Dict[str, WorkSchedule]] = Field(
        None,
        description="Weekly schedule: {'monday': {'start': '08:00', 'end': '17:00'}, ...}"
    )
    supervisor_name: str = Field(..., min_length=1, max_length=200)
    supervisor_phone: str = Field(..., min_length=10, max_length=20)
    notes: Optional[str] = None

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v: date) -> date:
        """Start date cannot be in the past."""
        if v < date.today():
            raise ValueError('Start date cannot be in the past')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """End date must be after start date."""
        if v and 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @field_validator('work_schedule')
    @classmethod
    def validate_schedule(cls, v: Optional[Dict]) -> Optional[Dict]:
        """Validate schedule has valid day keys."""
        if v is None:
            return v
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        for day in v.keys():
            if day.lower() not in valid_days:
                raise ValueError(f'Invalid day: {day}. Must be one of: {valid_days}')
        return v


class WorkReleaseAssignmentUpdate(BaseModel):
    """Update assignment details (non-status fields)."""
    position_title: Optional[str] = Field(None, min_length=1, max_length=200)
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    work_schedule: Optional[Dict[str, Any]] = None
    supervisor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    supervisor_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    notes: Optional[str] = None


class WorkReleaseAssignmentStatusUpdate(BaseModel):
    """Update assignment status with optional reason."""
    status: str = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change (required for TERMINATED)")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is a valid WorkReleaseStatus."""
        valid = {'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'SUSPENDED', 'COMPLETED', 'TERMINATED'}
        if v.upper() not in valid:
            raise ValueError(f'Invalid status. Must be one of: {valid}')
        return v.upper()


class WorkReleaseAssignmentResponse(BaseModel):
    """Assignment response with employer details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    employer_id: UUID
    employer_name: Optional[str] = None
    position_title: str
    start_date: date
    end_date: Optional[date]
    status: str
    hourly_rate: Optional[Decimal]
    work_schedule: Optional[Dict[str, Any]]
    supervisor_name: str
    supervisor_phone: str
    approved_by: Optional[UUID]
    approval_date: Optional[date]
    termination_reason: Optional[str]
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]


class WorkReleaseAssignmentListResponse(BaseModel):
    """Paginated list of assignments."""
    items: List[WorkReleaseAssignmentResponse]
    total: int


# ============================================================================
# Log DTOs
# ============================================================================

class WorkReleaseLogDeparture(BaseModel):
    """Log inmate departure for work."""
    assignment_id: UUID
    log_date: date = Field(default_factory=date.today)
    departure_time: time
    expected_return_time: time
    notes: Optional[str] = None

    @field_validator('expected_return_time')
    @classmethod
    def validate_return_time(cls, v: time, info) -> time:
        """Return time must be after departure."""
        if 'departure_time' in info.data and v <= info.data['departure_time']:
            raise ValueError('Expected return time must be after departure time')
        return v


class WorkReleaseLogReturn(BaseModel):
    """Log inmate return from work."""
    actual_return_time: time
    notes: Optional[str] = None


class WorkReleaseLogResponse(BaseModel):
    """Log entry response with computed late status."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID
    log_date: date
    departure_time: time
    expected_return_time: time
    actual_return_time: Optional[time]
    status: str
    is_late: bool
    minutes_late: Optional[int]
    verified_by: Optional[UUID]
    notes: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]


class WorkReleaseLogListResponse(BaseModel):
    """Paginated list of log entries."""
    items: List[WorkReleaseLogResponse]
    total: int


# ============================================================================
# Summary and Statistics DTOs
# ============================================================================

class InmateWorkReleaseSummary(BaseModel):
    """Work release summary for an inmate."""
    inmate_id: UUID
    current_assignment: Optional[WorkReleaseAssignmentResponse]
    total_assignments: int
    total_work_days: int
    late_returns: int
    no_shows: int


class WorkReleaseStatistics(BaseModel):
    """Overall work release programme statistics."""
    total_employers: int
    approved_employers: int
    active_assignments: int
    total_assignments: int
    inmates_at_work_today: int
    late_returns_this_month: int
    no_shows_this_month: int


class DailyWorkReleaseReport(BaseModel):
    """Daily report of work release activity."""
    report_date: date
    departed: int
    returned_on_time: int
    returned_late: int
    did_not_return: int
    still_out: int
    logs: List[WorkReleaseLogResponse]
