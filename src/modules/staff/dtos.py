"""
Staff Management DTOs - Data Transfer Objects for staff operations.

Provides structured data validation for staff records,
shift scheduling, and training management.
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.common.enums import (
    StaffRank, Department, StaffStatus,
    ShiftType, ShiftStatus, TrainingType
)


# =============================================================================
# Staff DTOs
# =============================================================================

class StaffCreateDTO(BaseModel):
    """Create a new staff record."""
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(..., description="Link to auth users table")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    rank: StaffRank = Field(default=StaffRank.OFFICER)
    department: Department = Field(default=Department.SECURITY)
    hire_date: date = Field(..., description="Employment start date")
    phone: Optional[str] = Field(None, max_length=20, description="Format: (242) XXX-XXXX")
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)


class StaffUpdateDTO(BaseModel):
    """Update an existing staff record."""
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    rank: Optional[StaffRank] = None
    department: Optional[Department] = None
    status: Optional[StaffStatus] = None
    phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class CertificationDTO(BaseModel):
    """Certification entry in staff record."""
    model_config = ConfigDict(from_attributes=True)

    cert_type: str = Field(..., description="Certification type")
    obtained_date: date = Field(..., description="Date obtained")
    expiry_date: Optional[date] = Field(None, description="Expiration date")
    cert_number: Optional[str] = Field(None, description="Certificate number")


class StaffDTO(BaseModel):
    """Staff record response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    employee_number: str
    first_name: str
    last_name: str
    full_name: str  # Computed
    rank: StaffRank
    department: Department
    hire_date: date
    years_of_service: int  # Computed
    status: StaffStatus
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    certifications: Optional[List[dict]] = None
    is_active: bool

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class StaffListDTO(BaseModel):
    """Minimal staff info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_number: str
    full_name: str
    rank: StaffRank
    department: Department
    status: StaffStatus
    is_active: bool


# =============================================================================
# Shift DTOs
# =============================================================================

class ShiftCreateDTO(BaseModel):
    """Create a new shift assignment."""
    model_config = ConfigDict(from_attributes=True)

    staff_id: UUID = Field(..., description="Staff member to assign")
    shift_date: date = Field(..., description="Date of shift")
    shift_type: ShiftType = Field(..., description="Shift type (DAY/EVENING/NIGHT)")
    start_time: time = Field(..., description="Shift start time")
    end_time: time = Field(..., description="Shift end time")
    housing_unit_id: Optional[UUID] = Field(None, description="Assigned post/housing unit")
    notes: Optional[str] = Field(None, max_length=1000)


class ShiftUpdateDTO(BaseModel):
    """Update an existing shift."""
    model_config = ConfigDict(from_attributes=True)

    shift_type: Optional[ShiftType] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    housing_unit_id: Optional[UUID] = None
    status: Optional[ShiftStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class ShiftDTO(BaseModel):
    """Shift response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_id: UUID
    staff_name: Optional[str] = None  # Computed from relationship
    employee_number: Optional[str] = None
    shift_date: date
    shift_type: ShiftType
    start_time: time
    end_time: time
    housing_unit_id: Optional[UUID] = None
    housing_unit_name: Optional[str] = None  # Computed from relationship
    status: ShiftStatus
    notes: Optional[str] = None
    created_by: UUID
    creator_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class ShiftListDTO(BaseModel):
    """Minimal shift info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_name: str
    employee_number: str
    shift_date: date
    shift_type: ShiftType
    start_time: time
    end_time: time
    status: ShiftStatus
    housing_unit_name: Optional[str] = None


class BulkShiftCreateDTO(BaseModel):
    """Create multiple shifts at once."""
    model_config = ConfigDict(from_attributes=True)

    shifts: List[ShiftCreateDTO] = Field(..., min_length=1, max_length=100)


# =============================================================================
# Training DTOs
# =============================================================================

class TrainingCreateDTO(BaseModel):
    """Create a training record."""
    model_config = ConfigDict(from_attributes=True)

    staff_id: UUID = Field(..., description="Staff member")
    training_type: TrainingType = Field(..., description="Type of training")
    training_date: date = Field(..., description="Date completed")
    expiry_date: Optional[date] = Field(None, description="Expiration date if applicable")
    hours: int = Field(..., ge=1, description="Training hours")
    instructor: str = Field(..., min_length=1, max_length=200)
    certification_number: Optional[str] = Field(None, max_length=50)


class TrainingUpdateDTO(BaseModel):
    """Update a training record."""
    model_config = ConfigDict(from_attributes=True)

    expiry_date: Optional[date] = None
    hours: Optional[int] = Field(None, ge=1)
    instructor: Optional[str] = Field(None, max_length=200)
    certification_number: Optional[str] = Field(None, max_length=50)
    is_current: Optional[bool] = None


class TrainingDTO(BaseModel):
    """Training record response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_id: UUID
    staff_name: Optional[str] = None
    employee_number: Optional[str] = None
    training_type: TrainingType
    training_date: date
    expiry_date: Optional[date] = None
    hours: int
    instructor: str
    certification_number: Optional[str] = None
    is_current: bool
    is_expired: bool  # Computed
    days_until_expiry: Optional[int] = None  # Computed

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class TrainingListDTO(BaseModel):
    """Minimal training info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_name: str
    employee_number: str
    training_type: TrainingType
    training_date: date
    expiry_date: Optional[date] = None
    is_current: bool
    is_expired: bool
    days_until_expiry: Optional[int] = None


class ExpiringCertificationDTO(BaseModel):
    """Certification expiring soon."""
    model_config = ConfigDict(from_attributes=True)

    training_id: UUID
    staff_id: UUID
    staff_name: str
    employee_number: str
    department: Department
    training_type: TrainingType
    expiry_date: date
    days_until_expiry: int


# =============================================================================
# On-Duty / Schedule DTOs
# =============================================================================

class OnDutyStaffDTO(BaseModel):
    """Staff currently on duty."""
    model_config = ConfigDict(from_attributes=True)

    staff_id: UUID
    employee_number: str
    staff_name: str
    rank: StaffRank
    department: Department
    shift_id: UUID
    shift_type: ShiftType
    start_time: time
    end_time: time
    housing_unit_name: Optional[str] = None


class DailyScheduleDTO(BaseModel):
    """Daily shift schedule."""
    model_config = ConfigDict(from_attributes=True)

    date: date
    day_shifts: List[ShiftListDTO]
    evening_shifts: List[ShiftListDTO]
    night_shifts: List[ShiftListDTO]
    total_staff: int
    coverage_gaps: Optional[List[str]] = None


# =============================================================================
# Statistics DTOs
# =============================================================================

class StaffStatisticsDTO(BaseModel):
    """Staff statistics summary."""
    model_config = ConfigDict(from_attributes=True)

    total_staff: int
    active_staff: int
    on_leave: int
    suspended: int

    by_department: dict  # Department -> count
    by_rank: dict  # Rank -> count

    # Shift statistics
    shifts_today: int
    staff_on_duty: int

    # Training statistics
    expiring_certifications_30_days: int
    expired_certifications: int

    # Averages
    average_years_of_service: float
