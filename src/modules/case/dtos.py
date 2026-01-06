"""
Case Management DTOs - Pydantic models for validation and serialization.

Supports:
- Case officer assignments
- Case note documentation
- Rehabilitation goal tracking
- Caseload management
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import NoteType, GoalType, GoalStatus


# ============================================================================
# Case Assignment DTOs
# ============================================================================

class CaseAssignmentCreate(BaseModel):
    """Assign a case officer to an inmate."""
    inmate_id: UUID
    case_officer_id: UUID
    assigned_date: date = Field(default_factory=date.today)
    caseload_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaseAssignmentEnd(BaseModel):
    """End a case assignment."""
    end_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(
        None,
        description="Notes about why assignment is ending"
    )

    model_config = ConfigDict(from_attributes=True)


class CaseAssignmentResponse(BaseModel):
    """Case assignment response."""
    id: UUID
    inmate_id: UUID
    case_officer_id: UUID
    assigned_date: date
    end_date: Optional[date]
    is_active: bool
    caseload_notes: Optional[str]
    assigned_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CaseAssignmentListResponse(BaseModel):
    """List of case assignments."""
    items: List[CaseAssignmentResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Case Note DTOs
# ============================================================================

class CaseNoteCreate(BaseModel):
    """Create a new case note."""
    inmate_id: UUID
    note_date: date = Field(default_factory=date.today)
    note_type: NoteType
    content: str = Field(..., min_length=10)
    is_confidential: bool = False
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None

    @field_validator('follow_up_date')
    @classmethod
    def validate_follow_up(cls, v: Optional[date], info) -> Optional[date]:
        follow_up_required = info.data.get('follow_up_required')
        if follow_up_required and not v:
            raise ValueError('follow_up_date required when follow_up_required is true')
        if v and not follow_up_required:
            raise ValueError('follow_up_required must be true to set follow_up_date')
        return v

    model_config = ConfigDict(from_attributes=True)


class CaseNoteResponse(BaseModel):
    """Case note response."""
    id: UUID
    case_assignment_id: UUID
    inmate_id: UUID
    note_date: date
    note_type: NoteType
    content: str
    is_confidential: bool
    follow_up_required: bool
    follow_up_date: Optional[date]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CaseNoteListResponse(BaseModel):
    """List of case notes."""
    items: List[CaseNoteResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Rehabilitation Goal DTOs
# ============================================================================

class RehabilitationGoalCreate(BaseModel):
    """Create a new rehabilitation goal."""
    goal_type: GoalType
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    target_date: date

    @field_validator('title')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator('target_date')
    @classmethod
    def target_in_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError('target_date must be in the future')
        return v

    model_config = ConfigDict(from_attributes=True)


class RehabilitationGoalUpdate(BaseModel):
    """Update a rehabilitation goal."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[GoalStatus] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RehabilitationGoalProgressUpdate(BaseModel):
    """Update goal progress."""
    progress_percentage: int = Field(..., ge=0, le=100)
    notes: Optional[str] = Field(
        None,
        description="Notes about progress update"
    )
    status: Optional[GoalStatus] = Field(
        None,
        description="Optionally update status (auto-set to COMPLETED if progress=100)"
    )

    model_config = ConfigDict(from_attributes=True)


class RehabilitationGoalResponse(BaseModel):
    """Rehabilitation goal response."""
    id: UUID
    inmate_id: UUID
    goal_type: GoalType
    title: str
    description: Optional[str]
    target_date: date
    status: GoalStatus
    progress_percentage: int
    completion_date: Optional[date]
    is_overdue: bool
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class RehabilitationGoalListResponse(BaseModel):
    """List of rehabilitation goals."""
    items: List[RehabilitationGoalResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary DTOs
# ============================================================================

class InmateCaseSummary(BaseModel):
    """Summary of inmate's case management."""
    inmate_id: UUID
    current_assignment: Optional[CaseAssignmentResponse]
    total_assignments: int
    total_notes: int
    recent_notes: List[CaseNoteResponse]
    goals_summary: dict  # status -> count
    active_goals: List[RehabilitationGoalResponse]
    overdue_goals: List[RehabilitationGoalResponse]

    model_config = ConfigDict(from_attributes=True)


class CaseOfficerCaseload(BaseModel):
    """Case officer's current caseload."""
    case_officer_id: UUID
    total_active_cases: int
    assignments: List[CaseAssignmentResponse]
    pending_follow_ups: int
    overdue_goals_count: int

    model_config = ConfigDict(from_attributes=True)


class CaseStatistics(BaseModel):
    """Overall case management statistics."""
    total_active_assignments: int
    total_case_notes: int
    notes_by_type: dict  # note_type -> count
    goals_by_status: dict  # status -> count
    goals_by_type: dict  # goal_type -> count
    overdue_goals: int
    pending_follow_ups: int
    average_goals_per_inmate: Optional[float]

    model_config = ConfigDict(from_attributes=True)
