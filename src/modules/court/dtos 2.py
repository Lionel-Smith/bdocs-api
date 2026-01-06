"""
Court DTOs - Pydantic models for validation and serialization.

Includes DTOs for:
- Court Cases
- Court Appearances
- Charge objects (nested in cases)
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import CourtType, CaseStatus, AppearanceType, AppearanceOutcome


# ============================================================================
# Charge DTOs (nested in Court Case)
# ============================================================================

class ChargeCreate(BaseModel):
    """Single criminal charge."""
    offense: str = Field(..., min_length=1, max_length=500)
    statute: Optional[str] = Field(None, max_length=100, description="Legal statute reference")
    count: int = Field(1, ge=1, description="Number of counts")
    plea: Optional[str] = Field(None, pattern=r'^(GUILTY|NOT_GUILTY|NO_CONTEST|NOT_ENTERED)$')

    model_config = ConfigDict(from_attributes=True)


class ChargeResponse(BaseModel):
    """Charge response."""
    offense: str
    statute: Optional[str]
    count: int
    plea: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Court Case DTOs
# ============================================================================

class CourtCaseCreate(BaseModel):
    """Create a new court case."""
    inmate_id: UUID
    case_number: str = Field(..., min_length=1, max_length=50, pattern=r'^[A-Z]{2,3}-\d{4}-\d+$')
    court_type: CourtType
    charges: List[ChargeCreate] = Field(..., min_length=1)
    filing_date: date
    presiding_judge: Optional[str] = Field(None, max_length=200)
    prosecutor: Optional[str] = Field(None, max_length=200)
    defense_attorney: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

    @field_validator('case_number')
    @classmethod
    def uppercase_case_number(cls, v: str) -> str:
        return v.upper()

    model_config = ConfigDict(from_attributes=True)


class CourtCaseUpdate(BaseModel):
    """Update court case."""
    status: Optional[CaseStatus] = None
    presiding_judge: Optional[str] = Field(None, max_length=200)
    prosecutor: Optional[str] = Field(None, max_length=200)
    defense_attorney: Optional[str] = Field(None, max_length=200)
    charges: Optional[List[ChargeCreate]] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourtCaseResponse(BaseModel):
    """Court case response."""
    id: UUID
    inmate_id: UUID
    case_number: str
    court_type: CourtType
    charges: List[dict]  # List of charge objects
    filing_date: date
    status: CaseStatus
    presiding_judge: Optional[str]
    prosecutor: Optional[str]
    defense_attorney: Optional[str]
    notes: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CourtCaseListResponse(BaseModel):
    """List of court cases."""
    items: List[CourtCaseResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Court Appearance DTOs
# ============================================================================

class CourtAppearanceCreate(BaseModel):
    """Create a new court appearance."""
    court_case_id: UUID
    inmate_id: UUID
    appearance_date: datetime
    appearance_type: AppearanceType
    court_location: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None
    auto_create_movement: bool = Field(
        True,
        description="Automatically create a COURT_TRANSPORT movement"
    )

    @field_validator('court_location')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class CourtAppearanceUpdate(BaseModel):
    """Update court appearance (before it occurs)."""
    appearance_date: Optional[datetime] = None
    court_location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourtAppearanceOutcomeUpdate(BaseModel):
    """Record outcome of a court appearance."""
    outcome: AppearanceOutcome
    next_appearance_date: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourtAppearanceResponse(BaseModel):
    """Court appearance response."""
    id: UUID
    court_case_id: UUID
    inmate_id: UUID
    appearance_date: datetime
    appearance_type: AppearanceType
    court_location: str
    outcome: Optional[AppearanceOutcome]
    next_appearance_date: Optional[datetime]
    movement_id: Optional[UUID]
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]
    # Joined fields
    case_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourtAppearanceListResponse(BaseModel):
    """List of court appearances."""
    items: List[CourtAppearanceResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary DTOs
# ============================================================================

class InmateCourtSummary(BaseModel):
    """Summary of inmate's court involvement."""
    inmate_id: UUID
    total_cases: int
    active_cases: int
    total_appearances: int
    upcoming_appearances: int
    cases: List[CourtCaseResponse]
    recent_appearances: List[CourtAppearanceResponse]

    model_config = ConfigDict(from_attributes=True)


class UpcomingAppearancesResponse(BaseModel):
    """List of upcoming court appearances."""
    items: List[CourtAppearanceResponse]
    total: int
    date_range_start: datetime
    date_range_end: datetime

    model_config = ConfigDict(from_attributes=True)
