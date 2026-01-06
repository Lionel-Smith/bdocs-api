"""
Reentry Planning DTOs - Data transfer objects for reentry operations.

Three DTO families:
1. Plan DTOs: Master reentry plan CRUD and approval
2. Checklist DTOs: Individual preparation items
3. Referral DTOs: External service referrals

Key computed fields:
- readiness_score: Percentage of checklist completion
- days_until_release: Days to expected release date
"""
from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.common.enums import (
    PlanStatus, HousingPlan, ChecklistType,
    ServiceType, ReferralStatus
)


# ============================================================================
# Reentry Plan DTOs
# ============================================================================

class ReentryPlanCreate(BaseModel):
    """Create a new reentry plan."""
    inmate_id: UUID
    expected_release_date: date
    housing_plan: HousingPlan = HousingPlan.UNKNOWN
    housing_address: Optional[str] = None
    employment_plan: Optional[str] = None
    has_id_documents: bool = False
    has_birth_certificate: bool = False
    has_nib_card: bool = False
    transportation_arranged: bool = False
    family_contact_name: Optional[str] = Field(None, max_length=200)
    family_contact_phone: Optional[str] = Field(None, max_length=20)
    support_services: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    notes: Optional[str] = None

    @field_validator('expected_release_date')
    @classmethod
    def validate_release_date(cls, v: date) -> date:
        """Release date should typically be in the future."""
        # Allow past dates for data entry of existing plans
        return v

    @field_validator('family_contact_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = ''.join(c for c in v if c.isdigit())
        if len(clean) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v


class ReentryPlanUpdate(BaseModel):
    """Update reentry plan details."""
    expected_release_date: Optional[date] = None
    housing_plan: Optional[HousingPlan] = None
    housing_address: Optional[str] = None
    employment_plan: Optional[str] = None
    has_id_documents: Optional[bool] = None
    has_birth_certificate: Optional[bool] = None
    has_nib_card: Optional[bool] = None
    transportation_arranged: Optional[bool] = None
    family_contact_name: Optional[str] = Field(None, max_length=200)
    family_contact_phone: Optional[str] = Field(None, max_length=20)
    support_services: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    notes: Optional[str] = None


class ReentryPlanStatusUpdate(BaseModel):
    """Update plan status."""
    status: PlanStatus
    notes: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: PlanStatus) -> PlanStatus:
        """Validate status transition."""
        # COMPLETED status requires separate completion flow
        return v


class ReentryPlanResponse(BaseModel):
    """Reentry plan response with computed fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    expected_release_date: date
    status: str
    housing_plan: str
    housing_address: Optional[str]
    employment_plan: Optional[str]
    has_id_documents: bool
    has_birth_certificate: bool
    has_nib_card: bool
    transportation_arranged: bool
    family_contact_name: Optional[str]
    family_contact_phone: Optional[str]
    support_services: Optional[List[Any]]
    risk_factors: Optional[List[Any]]
    notes: Optional[str]
    created_by: Optional[UUID]
    approved_by: Optional[UUID]
    approval_date: Optional[date]
    days_until_release: int
    is_overdue: bool
    readiness_score: Optional[int] = None  # Computed externally
    checklist_total: Optional[int] = None
    checklist_completed: Optional[int] = None
    inserted_date: datetime
    updated_date: Optional[datetime]


class ReentryPlanListResponse(BaseModel):
    """Paginated list of reentry plans."""
    items: List[ReentryPlanResponse]
    total: int


class ReentryPlanSummary(BaseModel):
    """Summary of reentry plan for inmate profile."""
    plan_id: Optional[UUID]
    status: Optional[str]
    expected_release_date: Optional[date]
    days_until_release: Optional[int]
    readiness_score: Optional[int]
    housing_plan: Optional[str]
    has_critical_items: bool
    incomplete_items: int
    active_referrals: int


# ============================================================================
# Checklist DTOs
# ============================================================================

class ReentryChecklistCreate(BaseModel):
    """Create a checklist item."""
    item_type: ChecklistType
    description: str = Field(..., min_length=1)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class ReentryChecklistUpdate(BaseModel):
    """Update a checklist item."""
    description: Optional[str] = Field(None, min_length=1)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class ReentryChecklistComplete(BaseModel):
    """Mark checklist item as complete."""
    notes: Optional[str] = None


class ReentryChecklistResponse(BaseModel):
    """Checklist item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reentry_plan_id: UUID
    item_type: str
    description: str
    is_completed: bool
    completed_date: Optional[date]
    completed_by: Optional[UUID]
    due_date: Optional[date]
    is_overdue: bool
    notes: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]


class ReentryChecklistListResponse(BaseModel):
    """List of checklist items."""
    items: List[ReentryChecklistResponse]
    total: int
    completed: int
    incomplete: int


# ============================================================================
# Referral DTOs
# ============================================================================

class ReentryReferralCreate(BaseModel):
    """Create a service referral."""
    reentry_plan_id: UUID
    inmate_id: UUID
    service_type: ServiceType
    provider_name: str = Field(..., min_length=1, max_length=200)
    provider_contact: str = Field(..., min_length=1, max_length=200)
    referral_date: date = Field(default_factory=date.today)
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None


class ReentryReferralUpdate(BaseModel):
    """Update referral details."""
    provider_name: Optional[str] = Field(None, min_length=1, max_length=200)
    provider_contact: Optional[str] = Field(None, min_length=1, max_length=200)
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None


class ReentryReferralStatusUpdate(BaseModel):
    """Update referral status."""
    status: ReferralStatus
    outcome: Optional[str] = None
    notes: Optional[str] = None


class ReentryReferralResponse(BaseModel):
    """Referral response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reentry_plan_id: UUID
    inmate_id: UUID
    service_type: str
    provider_name: str
    provider_contact: str
    referral_date: date
    status: str
    appointment_date: Optional[datetime]
    outcome: Optional[str]
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]


class ReentryReferralListResponse(BaseModel):
    """List of referrals."""
    items: List[ReentryReferralResponse]
    total: int


# ============================================================================
# Statistics and Report DTOs
# ============================================================================

class UpcomingReleaseItem(BaseModel):
    """Upcoming release item for dashboard."""
    plan_id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    booking_number: Optional[str] = None
    expected_release_date: date
    days_until_release: int
    status: str
    readiness_score: int
    housing_plan: str
    is_ready: bool


class UpcomingReleasesResponse(BaseModel):
    """List of upcoming releases."""
    items: List[UpcomingReleaseItem]
    total: int
    ready_count: int
    not_ready_count: int


class NotReadyPlanItem(BaseModel):
    """Plan not ready for release."""
    plan_id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    expected_release_date: date
    days_until_release: int
    readiness_score: int
    incomplete_items: List[str]
    missing_critical: List[str]


class NotReadyPlansResponse(BaseModel):
    """List of plans not ready for release."""
    items: List[NotReadyPlanItem]
    total: int


class ReentryStatistics(BaseModel):
    """Overall reentry planning statistics."""
    total_active_plans: int
    draft_plans: int
    in_progress_plans: int
    ready_plans: int
    releases_next_30_days: int
    releases_next_90_days: int
    average_readiness_score: float
    plans_below_50_percent: int
    active_referrals: int
    completed_referrals_this_month: int
