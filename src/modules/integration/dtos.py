"""
External Integration DTOs - Data Transfer Objects for RBPF integration.

Provides structured data validation for integration requests, responses,
and log entries.

NOTE: This is a STUB implementation. Response structures match expected
RBPF API format based on preliminary specifications.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.common.enums import RequestType, IntegrationStatus


# =============================================================================
# RBPF Request DTOs
# =============================================================================

class PersonLookupRequest(BaseModel):
    """Request to look up a person by NIB number."""
    model_config = ConfigDict(from_attributes=True)

    nib_number: str = Field(
        ...,
        min_length=9,
        max_length=15,
        description="National Insurance Board number"
    )


class WarrantCheckRequest(BaseModel):
    """Request to check for active warrants."""
    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date = Field(..., description="Date of birth for matching")
    nib_number: Optional[str] = Field(None, description="Optional NIB for exact match")


class BookingNotificationRequest(BaseModel):
    """Notification to RBPF of new inmate booking."""
    model_config = ConfigDict(from_attributes=True)

    # Inmate identification
    inmate_id: UUID = Field(..., description="BDOCS inmate UUID")
    booking_number: str = Field(..., description="BDOCS booking number")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: date
    nib_number: Optional[str] = None

    # Booking details
    booking_date: datetime = Field(..., description="Date and time of booking")
    offense: str = Field(..., max_length=500, description="Primary offense/charge")
    court_case_number: Optional[str] = Field(None, max_length=50)
    arresting_agency: Optional[str] = Field(None, max_length=100)


class ReleaseNotificationRequest(BaseModel):
    """Notification to RBPF of inmate release."""
    model_config = ConfigDict(from_attributes=True)

    # Inmate identification
    inmate_id: UUID = Field(..., description="BDOCS inmate UUID")
    booking_number: str = Field(..., description="BDOCS booking number")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    nib_number: Optional[str] = None

    # Release details
    release_date: datetime = Field(..., description="Date and time of release")
    release_type: str = Field(..., description="Type of release (e.g., SERVED, BAIL, CLEMENCY)")
    conditions: Optional[str] = Field(None, max_length=1000, description="Release conditions if any")


# =============================================================================
# RBPF Response DTOs (Mock structures)
# =============================================================================

class CriminalRecordEntry(BaseModel):
    """Individual criminal record entry from RBPF."""
    model_config = ConfigDict(from_attributes=True)

    offense: str
    offense_date: date
    court: str
    case_number: str
    disposition: str
    sentence: Optional[str] = None


class PersonLookupResponse(BaseModel):
    """Response from RBPF person lookup."""
    model_config = ConfigDict(from_attributes=True)

    found: bool = Field(..., description="Whether person was found in RBPF system")
    nib_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    aliases: Optional[List[str]] = None
    criminal_history: Optional[List[CriminalRecordEntry]] = None
    last_known_address: Optional[str] = None
    rbpf_id: Optional[str] = Field(None, description="RBPF internal identifier")


class WarrantEntry(BaseModel):
    """Individual warrant record from RBPF."""
    model_config = ConfigDict(from_attributes=True)

    warrant_number: str
    warrant_type: str  # ARREST, BENCH, etc.
    issue_date: date
    issuing_court: str
    offense: str
    status: str  # ACTIVE, EXECUTED, RECALLED


class WarrantCheckResponse(BaseModel):
    """Response from RBPF warrant check."""
    model_config = ConfigDict(from_attributes=True)

    has_warrants: bool = Field(..., description="Whether active warrants exist")
    warrant_count: int = 0
    warrants: Optional[List[WarrantEntry]] = None
    last_checked: datetime


class NotificationResponse(BaseModel):
    """Response from RBPF notification (booking/release)."""
    model_config = ConfigDict(from_attributes=True)

    acknowledged: bool = Field(..., description="Whether RBPF acknowledged notification")
    reference_number: Optional[str] = Field(None, description="RBPF reference number")
    timestamp: datetime
    message: Optional[str] = None


# =============================================================================
# Integration Log DTOs
# =============================================================================

class IntegrationLogDTO(BaseModel):
    """External system log entry response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_name: str
    request_type: RequestType
    status: IntegrationStatus
    request_time: datetime
    response_time: Optional[datetime] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    correlation_id: UUID
    initiated_by: UUID
    initiator_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime


class IntegrationLogDetailDTO(IntegrationLogDTO):
    """Detailed log entry including payloads."""
    model_config = ConfigDict(from_attributes=True)

    request_payload: dict
    response_payload: Optional[dict] = None


class IntegrationLogListDTO(BaseModel):
    """Minimal log info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_name: str
    request_type: RequestType
    status: IntegrationStatus
    request_time: datetime
    response_time_ms: Optional[int] = None
    correlation_id: UUID


# =============================================================================
# Health Check DTOs
# =============================================================================

class SystemHealthDTO(BaseModel):
    """Health status of an external system."""
    model_config = ConfigDict(from_attributes=True)

    system_name: str
    status: str  # HEALTHY, DEGRADED, UNAVAILABLE
    last_successful_request: Optional[datetime] = None
    last_failed_request: Optional[datetime] = None
    success_rate_24h: float = Field(..., description="Success rate in last 24 hours")
    average_response_time_ms: Optional[int] = None


class IntegrationHealthDTO(BaseModel):
    """Overall integration health summary."""
    model_config = ConfigDict(from_attributes=True)

    overall_status: str  # HEALTHY, DEGRADED, UNAVAILABLE
    systems: List[SystemHealthDTO]
    checked_at: datetime
