"""
Clemency DTOs - Pydantic models for validation and serialization.

Includes workflow validation for status transitions.

Status workflow:
SUBMITTED → UNDER_REVIEW → COMMITTEE_SCHEDULED →
AWAITING_MINISTER → GOVERNOR_GENERAL → GRANTED/DENIED

WITHDRAWN and DEFERRED can occur from most states.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import PetitionType, PetitionStatus


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    PetitionStatus.SUBMITTED: [
        PetitionStatus.UNDER_REVIEW,
        PetitionStatus.WITHDRAWN
    ],
    PetitionStatus.UNDER_REVIEW: [
        PetitionStatus.COMMITTEE_SCHEDULED,
        PetitionStatus.WITHDRAWN,
        PetitionStatus.DEFERRED
    ],
    PetitionStatus.COMMITTEE_SCHEDULED: [
        PetitionStatus.AWAITING_MINISTER,
        PetitionStatus.WITHDRAWN,
        PetitionStatus.DEFERRED
    ],
    PetitionStatus.AWAITING_MINISTER: [
        PetitionStatus.GOVERNOR_GENERAL,
        PetitionStatus.WITHDRAWN,
        PetitionStatus.DEFERRED
    ],
    PetitionStatus.GOVERNOR_GENERAL: [
        PetitionStatus.GRANTED,
        PetitionStatus.DENIED,
        PetitionStatus.DEFERRED
    ],
    PetitionStatus.GRANTED: [],  # Terminal state
    PetitionStatus.DENIED: [],   # Terminal state
    PetitionStatus.WITHDRAWN: [],  # Terminal state
    PetitionStatus.DEFERRED: [
        PetitionStatus.UNDER_REVIEW,  # Can restart review
        PetitionStatus.WITHDRAWN
    ],
}


# ============================================================================
# Supporting Document DTO
# ============================================================================

class SupportingDocument(BaseModel):
    """Reference to a supporting document."""
    name: str = Field(..., min_length=1, max_length=200)
    document_type: str = Field(..., max_length=50, description="e.g., 'character_reference', 'medical_report'")
    url: Optional[str] = Field(None, max_length=500)
    date_added: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Clemency Petition DTOs
# ============================================================================

class ClemencyPetitionCreate(BaseModel):
    """Create a new clemency petition."""
    inmate_id: UUID
    sentence_id: UUID
    petition_type: PetitionType
    filed_date: date
    petitioner_name: str = Field(..., min_length=1, max_length=200)
    petitioner_relationship: str = Field(..., min_length=1, max_length=100)
    grounds_for_clemency: str = Field(..., min_length=10)
    supporting_documents: Optional[List[SupportingDocument]] = None
    victim_notification_date: Optional[date] = None
    victim_response: Optional[str] = None

    @field_validator('petitioner_name', 'petitioner_relationship')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class ClemencyPetitionUpdate(BaseModel):
    """Update a clemency petition (non-status fields)."""
    petitioner_name: Optional[str] = Field(None, min_length=1, max_length=200)
    petitioner_relationship: Optional[str] = Field(None, max_length=100)
    grounds_for_clemency: Optional[str] = Field(None, min_length=10)
    supporting_documents: Optional[List[SupportingDocument]] = None
    victim_notification_date: Optional[date] = None
    victim_response: Optional[str] = None
    committee_review_date: Optional[date] = None
    committee_recommendation: Optional[str] = None
    minister_review_date: Optional[date] = None
    minister_recommendation: Optional[str] = None
    governor_general_date: Optional[date] = None
    decision_date: Optional[date] = None
    decision_notes: Optional[str] = None
    granted_reduction_days: Optional[int] = Field(None, ge=1)

    model_config = ConfigDict(from_attributes=True)


class ClemencyStatusUpdate(BaseModel):
    """Update petition status with workflow validation."""
    status: PetitionStatus
    notes: Optional[str] = None
    # Fields that may be set during specific transitions
    committee_review_date: Optional[date] = None
    committee_recommendation: Optional[str] = None
    minister_review_date: Optional[date] = None
    minister_recommendation: Optional[str] = None
    governor_general_date: Optional[date] = None
    decision_date: Optional[date] = None
    decision_notes: Optional[str] = None
    granted_reduction_days: Optional[int] = Field(None, ge=1, description="Days to reduce sentence (for GRANTED)")

    model_config = ConfigDict(from_attributes=True)


class ClemencyPetitionResponse(BaseModel):
    """Clemency petition response."""
    id: UUID
    inmate_id: UUID
    sentence_id: UUID
    petition_number: str
    petition_type: PetitionType
    status: PetitionStatus
    filed_date: date
    petitioner_name: str
    petitioner_relationship: str
    grounds_for_clemency: str
    supporting_documents: Optional[List[dict]]
    victim_notification_date: Optional[date]
    victim_response: Optional[str]
    committee_review_date: Optional[date]
    committee_recommendation: Optional[str]
    minister_review_date: Optional[date]
    minister_recommendation: Optional[str]
    governor_general_date: Optional[date]
    decision_date: Optional[date]
    decision_notes: Optional[str]
    granted_reduction_days: Optional[int]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ClemencyPetitionListResponse(BaseModel):
    """List of clemency petitions."""
    items: List[ClemencyPetitionResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Status History DTOs
# ============================================================================

class ClemencyStatusHistoryResponse(BaseModel):
    """Status history entry response."""
    id: UUID
    petition_id: UUID
    from_status: Optional[PetitionStatus]
    to_status: PetitionStatus
    changed_date: datetime
    changed_by: Optional[UUID]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ClemencyStatusHistoryListResponse(BaseModel):
    """List of status history entries."""
    items: List[ClemencyStatusHistoryResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary and Statistics DTOs
# ============================================================================

class InmateClemencySummary(BaseModel):
    """Summary of inmate's clemency petitions."""
    inmate_id: UUID
    total_petitions: int
    pending_petitions: int
    granted_petitions: int
    denied_petitions: int
    petitions: List[ClemencyPetitionResponse]

    model_config = ConfigDict(from_attributes=True)


class ClemencyStatistics(BaseModel):
    """Statistics on clemency petitions."""
    total_petitions: int
    by_status: dict  # status -> count
    by_type: dict    # petition_type -> count
    pending_committee: int
    pending_minister: int
    pending_governor_general: int
    granted_last_year: int
    denied_last_year: int
    average_processing_days: Optional[float]

    model_config = ConfigDict(from_attributes=True)
