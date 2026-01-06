"""
Dashboard DTOs - Response models for dashboard endpoints.

All responses include a generated_at timestamp for cache freshness tracking.
"""
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Response with Timestamp
# ============================================================================

class DashboardBaseResponse(BaseModel):
    """Base class for all dashboard responses with cache timestamp."""
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when data was generated (for cache freshness)"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary Endpoint
# ============================================================================

class StatusBreakdown(BaseModel):
    """Breakdown of inmates by status."""
    remand: int = 0
    sentenced: int = 0
    released: int = 0
    transferred: int = 0
    deceased: int = 0


class SecurityBreakdown(BaseModel):
    """Breakdown of inmates by security level."""
    maximum: int = 0
    medium: int = 0
    minimum: int = 0


class GenderBreakdown(BaseModel):
    """Breakdown of inmates by gender."""
    male: int = 0
    female: int = 0


class DashboardSummaryResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/summary

    Overview of total population with breakdowns.
    """
    total_inmates: int
    by_status: StatusBreakdown
    by_security_level: SecurityBreakdown
    by_gender: GenderBreakdown
    capacity_utilization: float = Field(
        ...,
        description="Percentage of total capacity currently used (0-100+)"
    )


# ============================================================================
# Population Endpoint
# ============================================================================

class OvercrowdedUnit(BaseModel):
    """Details of an overcrowded housing unit."""
    id: UUID
    code: str
    name: str
    capacity: int
    current_occupancy: int
    over_capacity_by: int = Field(
        ...,
        description="Number of inmates over capacity"
    )
    utilization_percent: float


class DashboardPopulationResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/population

    Population metrics including capacity and remand ratio.
    """
    current_population: int
    total_capacity: int
    available_beds: int
    utilization_percent: float
    overcrowded_units: List[OvercrowdedUnit]
    overcrowded_unit_count: int
    remand_count: int
    remand_percentage: float = Field(
        ...,
        description="Percentage of population on remand (target <40%)"
    )
    remand_target_met: bool = Field(
        ...,
        description="Whether remand percentage is below 40% target"
    )


# ============================================================================
# Movements Today Endpoint
# ============================================================================

class MovementTypeBreakdown(BaseModel):
    """Breakdown of movements by type."""
    internal_transfer: int = 0
    court_transport: int = 0
    medical_transport: int = 0
    work_release: int = 0
    temporary_release: int = 0
    furlough: int = 0
    external_appointment: int = 0
    release: int = 0


class DashboardMovementsTodayResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/movements/today

    Today's movement summary.
    """
    date: datetime
    total_movements: int
    scheduled: int
    in_progress: int
    completed: int
    cancelled: int
    by_type: MovementTypeBreakdown


# ============================================================================
# Court Upcoming Endpoint
# ============================================================================

class CourtTypeBreakdown(BaseModel):
    """Breakdown by court type."""
    magistrates: int = 0
    supreme: int = 0
    court_of_appeal: int = 0
    privy_council: int = 0
    coroners: int = 0


class AppearanceTypeBreakdown(BaseModel):
    """Breakdown by appearance type."""
    arraignment: int = 0
    bail_hearing: int = 0
    trial: int = 0
    sentencing: int = 0
    appeal: int = 0
    motion: int = 0


class DashboardCourtUpcomingResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/court/upcoming

    Upcoming court appearances for next 7 days.
    """
    period_days: int = 7
    total_appearances: int
    by_court_type: CourtTypeBreakdown
    by_appearance_type: AppearanceTypeBreakdown


# ============================================================================
# Releases Upcoming Endpoint
# ============================================================================

class ReleaseTimeframe(BaseModel):
    """Release counts by timeframe."""
    next_30_days: int = 0
    next_60_days: int = 0
    next_90_days: int = 0


class ReleaseTypeBreakdown(BaseModel):
    """Breakdown by sentence type releasing."""
    imprisonment: int = 0
    time_served: int = 0
    suspended: int = 0
    probation: int = 0


class DashboardReleasesUpcomingResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/releases/upcoming

    Upcoming releases by timeframe.
    """
    by_timeframe: ReleaseTimeframe
    by_type: ReleaseTypeBreakdown
    total_upcoming: int = Field(
        ...,
        description="Total releases in next 90 days"
    )


# ============================================================================
# Clemency Pending Endpoint
# ============================================================================

class ClemencyStatusBreakdown(BaseModel):
    """Breakdown of pending clemency petitions by status."""
    submitted: int = 0
    under_review: int = 0
    committee_scheduled: int = 0
    awaiting_minister: int = 0
    governor_general: int = 0
    deferred: int = 0


class OldestPendingPetition(BaseModel):
    """Details of oldest pending petition."""
    id: UUID
    petition_number: str
    status: str
    filed_date: datetime
    days_pending: int
    petitioner_name: str


class DashboardClemencyPendingResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/clemency/pending

    Pending clemency petition summary.
    """
    total_pending: int
    by_status: ClemencyStatusBreakdown
    avg_days_in_status: Dict[str, float] = Field(
        default_factory=dict,
        description="Average days in each status"
    )
    oldest_pending: Optional[OldestPendingPetition] = None


# ============================================================================
# Alerts Endpoint
# ============================================================================

class AlertItem(BaseModel):
    """Individual alert item."""
    id: UUID
    type: str
    severity: str = Field(..., description="HIGH, MEDIUM, LOW")
    message: str
    related_entity: Optional[str] = None
    related_id: Optional[UUID] = None
    created_at: datetime


class DashboardAlertsResponse(DashboardBaseResponse):
    """
    GET /api/v1/dashboard/alerts

    System alerts requiring attention.
    """
    total_alerts: int
    high_severity: int
    medium_severity: int
    low_severity: int
    overcrowded_units: List[AlertItem]
    overdue_classifications: List[AlertItem]
    missed_court_dates: List[AlertItem]
    expiring_sentences_no_plan: List[AlertItem]
