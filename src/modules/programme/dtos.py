"""
Programme DTOs - Pydantic models for validation and serialization.

Includes workflow validation for enrollment status transitions.

Enrollment workflow: ENROLLED → ACTIVE → COMPLETED
Alternative paths: WITHDRAWN, SUSPENDED
"""
from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import ProgrammeCategory, SessionStatus, EnrollmentStatus


# Valid enrollment status transitions
VALID_ENROLLMENT_TRANSITIONS = {
    EnrollmentStatus.ENROLLED: [
        EnrollmentStatus.ACTIVE,
        EnrollmentStatus.WITHDRAWN
    ],
    EnrollmentStatus.ACTIVE: [
        EnrollmentStatus.COMPLETED,
        EnrollmentStatus.WITHDRAWN,
        EnrollmentStatus.SUSPENDED
    ],
    EnrollmentStatus.COMPLETED: [],  # Terminal state
    EnrollmentStatus.WITHDRAWN: [],   # Terminal state
    EnrollmentStatus.SUSPENDED: [
        EnrollmentStatus.ACTIVE,      # Can be reinstated
        EnrollmentStatus.WITHDRAWN
    ],
}


# ============================================================================
# Programme DTOs
# ============================================================================

class ProgrammeCreate(BaseModel):
    """Create a new programme."""
    code: str = Field(..., min_length=1, max_length=20, pattern=r'^[A-Z0-9\-]+$')
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: ProgrammeCategory
    provider: str = Field(..., min_length=1, max_length=200)
    duration_weeks: int = Field(..., ge=1, le=104, description="Duration in weeks (1-104)")
    max_participants: int = Field(..., ge=1, le=100, description="Max participants per cohort")
    eligibility_criteria: Optional[dict] = None
    is_active: bool = True

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator('name', 'provider')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class ProgrammeUpdate(BaseModel):
    """Update a programme."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[ProgrammeCategory] = None
    provider: Optional[str] = Field(None, min_length=1, max_length=200)
    duration_weeks: Optional[int] = Field(None, ge=1, le=104)
    max_participants: Optional[int] = Field(None, ge=1, le=100)
    eligibility_criteria: Optional[dict] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ProgrammeResponse(BaseModel):
    """Programme response."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    category: ProgrammeCategory
    provider: str
    duration_weeks: int
    max_participants: int
    eligibility_criteria: Optional[dict]
    is_active: bool
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProgrammeListResponse(BaseModel):
    """List of programmes."""
    items: List[ProgrammeResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Programme Session DTOs
# ============================================================================

class ProgrammeSessionCreate(BaseModel):
    """Create a new programme session."""
    session_date: date
    start_time: time
    end_time: time
    location: str = Field(..., min_length=1, max_length=200)
    instructor_name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None

    @field_validator('location', 'instructor_name')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: time, info) -> time:
        start = info.data.get('start_time')
        if start and v <= start:
            raise ValueError('end_time must be after start_time')
        return v

    model_config = ConfigDict(from_attributes=True)


class ProgrammeSessionUpdate(BaseModel):
    """Update a programme session."""
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    instructor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[SessionStatus] = None
    attendance_count: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProgrammeSessionResponse(BaseModel):
    """Programme session response."""
    id: UUID
    programme_id: UUID
    session_date: date
    start_time: time
    end_time: time
    location: str
    instructor_name: str
    status: SessionStatus
    attendance_count: Optional[int]
    notes: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProgrammeSessionListResponse(BaseModel):
    """List of programme sessions."""
    items: List[ProgrammeSessionResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Programme Enrollment DTOs
# ============================================================================

class ProgrammeEnrollmentCreate(BaseModel):
    """Enroll an inmate in a programme."""
    inmate_id: UUID
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProgrammeEnrollmentUpdate(BaseModel):
    """Update an enrollment."""
    notes: Optional[str] = None
    hours_completed: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ProgrammeEnrollmentStatusUpdate(BaseModel):
    """Update enrollment status with workflow validation."""
    status: EnrollmentStatus
    notes: Optional[str] = None
    # For completion
    grade: Optional[str] = Field(None, max_length=10)
    certificate_issued: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ProgrammeEnrollmentResponse(BaseModel):
    """Programme enrollment response."""
    id: UUID
    programme_id: UUID
    inmate_id: UUID
    enrolled_date: date
    status: EnrollmentStatus
    completion_date: Optional[date]
    grade: Optional[str]
    certificate_issued: bool
    hours_completed: int
    notes: Optional[str]
    enrolled_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProgrammeEnrollmentListResponse(BaseModel):
    """List of programme enrollments."""
    items: List[ProgrammeEnrollmentResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class ProgrammeEnrollmentDetailResponse(ProgrammeEnrollmentResponse):
    """Enrollment with programme details."""
    programme: Optional[ProgrammeResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Attendance DTOs
# ============================================================================

class AttendanceRecord(BaseModel):
    """Record attendance for a session."""
    session_id: UUID
    inmate_ids: List[UUID] = Field(..., min_length=1, description="List of inmates who attended")
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary and Statistics DTOs
# ============================================================================

class InmateProgrammeSummary(BaseModel):
    """Summary of inmate's programme participation."""
    inmate_id: UUID
    total_enrollments: int
    active_enrollments: int
    completed_programmes: int
    withdrawn_programmes: int
    total_hours_completed: int
    certificates_earned: int
    enrollments: List[ProgrammeEnrollmentDetailResponse]

    model_config = ConfigDict(from_attributes=True)


class ProgrammeStatistics(BaseModel):
    """Statistics on programmes."""
    total_programmes: int
    active_programmes: int
    by_category: dict  # category -> count
    total_enrollments: int
    active_enrollments: int
    completed_this_year: int
    average_completion_rate: Optional[float]
    most_popular_programmes: List[dict]  # [{programme_id, name, enrollment_count}]

    model_config = ConfigDict(from_attributes=True)
