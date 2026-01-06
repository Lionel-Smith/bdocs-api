"""
Incident Management DTOs - Data transfer objects for incident operations.

Three DTO families:
1. Incident DTOs: Main incident CRUD and status management
2. Involvement DTOs: Person involvement tracking
3. Attachment DTOs: File/evidence management

Key features:
- Auto-generated incident numbers (service layer)
- Severity escalation support
- External notification tracking
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.common.enums import (
    IncidentType, IncidentSeverity, IncidentStatus, InvolvementType
)


# ============================================================================
# Incident DTOs
# ============================================================================

class IncidentCreate(BaseModel):
    """Create a new incident report."""
    incident_type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    occurred_at: datetime
    location: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    immediate_actions: Optional[str] = None
    injuries_reported: bool = False
    property_damage: bool = False
    external_notification_required: bool = False

    @field_validator('occurred_at')
    @classmethod
    def validate_occurred_at(cls, v: datetime) -> datetime:
        """Incident cannot occur in the future."""
        if v > datetime.now(v.tzinfo):
            raise ValueError('Incident occurrence time cannot be in the future')
        return v


class IncidentUpdate(BaseModel):
    """Update incident details."""
    incident_type: Optional[IncidentType] = None
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    immediate_actions: Optional[str] = None
    injuries_reported: Optional[bool] = None
    property_damage: Optional[bool] = None
    external_notification_required: Optional[bool] = None
    external_notified: Optional[bool] = None


class IncidentStatusUpdate(BaseModel):
    """Update incident status."""
    status: IncidentStatus
    notes: Optional[str] = None


class IncidentSeverityUpdate(BaseModel):
    """Escalate or update incident severity."""
    severity: IncidentSeverity
    reason: str = Field(..., min_length=1, description="Reason for severity change")


class IncidentResolve(BaseModel):
    """Resolve an incident."""
    resolution: str = Field(..., min_length=1, description="Resolution description is required")
    notes: Optional[str] = None


class IncidentResponse(BaseModel):
    """Incident response with computed fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_number: str
    incident_type: str
    severity: str
    status: str
    occurred_at: datetime
    location: str
    reported_at: datetime
    reported_by: UUID
    description: str
    immediate_actions: Optional[str]
    injuries_reported: bool
    property_damage: bool
    external_notification_required: bool
    external_notified: bool
    resolution: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    is_open: bool
    requires_notification: bool
    involvement_count: Optional[int] = None
    attachment_count: Optional[int] = None
    inserted_date: datetime
    updated_date: Optional[datetime]


class IncidentListResponse(BaseModel):
    """Paginated list of incidents."""
    items: List[IncidentResponse]
    total: int


class IncidentDetailResponse(BaseModel):
    """Incident with full details including involvements and attachments."""
    incident: IncidentResponse
    involvements: List['IncidentInvolvementResponse']
    attachments: List['IncidentAttachmentResponse']


# ============================================================================
# Involvement DTOs
# ============================================================================

class IncidentInvolvementCreate(BaseModel):
    """Create involvement record."""
    inmate_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    involvement_type: InvolvementType
    description: str = Field(..., min_length=1)
    injuries: Optional[str] = None
    disciplinary_action_taken: bool = False

    @field_validator('staff_id')
    @classmethod
    def validate_person(cls, v: Optional[UUID], info) -> Optional[UUID]:
        """At least one of inmate_id or staff_id should be provided."""
        # This is a soft validation - external persons may have neither
        return v


class IncidentInvolvementUpdate(BaseModel):
    """Update involvement record."""
    involvement_type: Optional[InvolvementType] = None
    description: Optional[str] = None
    injuries: Optional[str] = None
    disciplinary_action_taken: Optional[bool] = None


class IncidentInvolvementResponse(BaseModel):
    """Involvement response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    inmate_id: Optional[UUID]
    staff_id: Optional[UUID]
    involvement_type: str
    description: str
    injuries: Optional[str]
    disciplinary_action_taken: bool
    inmate_name: Optional[str] = None
    staff_name: Optional[str] = None
    inserted_date: datetime
    updated_date: Optional[datetime]


class IncidentInvolvementListResponse(BaseModel):
    """List of involvements."""
    items: List[IncidentInvolvementResponse]
    total: int


# ============================================================================
# Attachment DTOs
# ============================================================================

class IncidentAttachmentCreate(BaseModel):
    """Create attachment record."""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=1, max_length=50)
    file_path: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class IncidentAttachmentResponse(BaseModel):
    """Attachment response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    file_name: str
    file_type: str
    file_path: str
    uploaded_at: datetime
    uploaded_by: UUID
    description: Optional[str]
    inserted_date: datetime


class IncidentAttachmentListResponse(BaseModel):
    """List of attachments."""
    items: List[IncidentAttachmentResponse]
    total: int


# ============================================================================
# Query and Filter DTOs
# ============================================================================

class IncidentFilter(BaseModel):
    """Filter parameters for incident queries."""
    incident_type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    injuries_reported: Optional[bool] = None


# ============================================================================
# Statistics DTOs
# ============================================================================

class IncidentTypeCount(BaseModel):
    """Count by incident type."""
    incident_type: str
    count: int


class IncidentSeverityCount(BaseModel):
    """Count by severity."""
    severity: str
    count: int


class IncidentStatistics(BaseModel):
    """Incident statistics for reporting."""
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    incidents_this_month: int
    incidents_requiring_notification: int
    incidents_with_injuries: int
    by_type: List[IncidentTypeCount]
    by_severity: List[IncidentSeverityCount]
    average_resolution_days: Optional[float]


class InmateIncidentSummary(BaseModel):
    """Summary of incidents for an inmate."""
    inmate_id: UUID
    total_involvements: int
    as_victim: int
    as_perpetrator: int
    as_witness: int
    recent_incidents: List[IncidentResponse]
