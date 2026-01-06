"""
Housing & Classification DTOs - Pydantic models for validation.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from src.common.enums import SecurityLevel, Gender


# ============================================================================
# Housing Unit DTOs
# ============================================================================

class HousingUnitCreate(BaseModel):
    """Create a new housing unit."""
    code: str = Field(..., min_length=1, max_length=10, pattern=r'^[A-Z]{3}-[A-Z0-9]+$')
    name: str = Field(..., min_length=1, max_length=100)
    security_level: SecurityLevel
    capacity: int = Field(..., ge=1, le=500)
    gender_restriction: Optional[Gender] = None
    is_juvenile: bool = False
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HousingUnitUpdate(BaseModel):
    """Update housing unit."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    is_active: Optional[bool] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HousingUnitResponse(BaseModel):
    """Housing unit response."""
    id: UUID
    code: str
    name: str
    security_level: SecurityLevel
    capacity: int
    current_occupancy: int
    available_beds: int  # Computed
    occupancy_rate: float  # Computed
    is_overcrowded: bool  # Computed
    gender_restriction: Optional[Gender]
    is_active: bool
    is_juvenile: bool
    description: Optional[str]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class HousingUnitListResponse(BaseModel):
    """List of housing units."""
    items: List[HousingUnitResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Classification DTOs
# ============================================================================

class ClassificationScores(BaseModel):
    """Classification scoring factors (each 1-5)."""
    charge_severity: int = Field(..., ge=1, le=5, description="Seriousness of charges")
    prior_record: int = Field(..., ge=1, le=5, description="Criminal history")
    institutional_behavior: int = Field(..., ge=1, le=5, description="Conduct while incarcerated")
    escape_risk: int = Field(..., ge=1, le=5, description="Flight risk")
    violence_risk: int = Field(..., ge=1, le=5, description="Risk of violence")

    @property
    def total(self) -> int:
        """Calculate total score."""
        return (
            self.charge_severity +
            self.prior_record +
            self.institutional_behavior +
            self.escape_risk +
            self.violence_risk
        )

    model_config = ConfigDict(from_attributes=True)


class ClassificationCreate(BaseModel):
    """Create classification assessment."""
    inmate_id: UUID
    scores: ClassificationScores
    review_date: Optional[date] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClassificationResponse(BaseModel):
    """Classification response."""
    id: UUID
    inmate_id: UUID
    classification_date: date
    security_level: SecurityLevel
    scores: dict  # ClassificationScores as dict
    total_score: int
    review_date: Optional[date]
    classified_by: Optional[UUID]
    notes: Optional[str]
    is_current: bool
    inserted_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassificationListResponse(BaseModel):
    """List of classifications for an inmate."""
    items: List[ClassificationResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Housing Assignment DTOs
# ============================================================================

class HousingAssignmentCreate(BaseModel):
    """Create housing assignment."""
    inmate_id: UUID
    housing_unit_id: UUID
    cell_number: Optional[str] = Field(None, max_length=20)
    bed_number: Optional[str] = Field(None, max_length=10)
    reason: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class HousingAssignmentEnd(BaseModel):
    """End a housing assignment."""
    reason: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class HousingAssignmentResponse(BaseModel):
    """Housing assignment response."""
    id: UUID
    inmate_id: UUID
    housing_unit_id: UUID
    housing_unit_code: Optional[str] = None  # Joined field
    housing_unit_name: Optional[str] = None  # Joined field
    cell_number: Optional[str]
    bed_number: Optional[str]
    assigned_date: datetime
    end_date: Optional[datetime]
    is_current: bool
    assigned_by: Optional[UUID]
    reason: Optional[str]
    inserted_date: datetime

    model_config = ConfigDict(from_attributes=True)


class HousingAssignmentListResponse(BaseModel):
    """List of housing assignments."""
    items: List[HousingAssignmentResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Inmate Housing Summary DTO
# ============================================================================

class InmateHousingSummary(BaseModel):
    """Summary of inmate's housing and classification."""
    inmate_id: UUID
    current_assignment: Optional[HousingAssignmentResponse]
    current_classification: Optional[ClassificationResponse]
    assignment_history: List[HousingAssignmentResponse]
    classification_history: List[ClassificationResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Overcrowding Report DTO
# ============================================================================

class OvercrowdedUnitReport(BaseModel):
    """Report of overcrowded units."""
    overcrowded_units: List[HousingUnitResponse]
    total_over_capacity: int
    facility_capacity: int
    facility_population: int
    facility_occupancy_rate: float

    model_config = ConfigDict(from_attributes=True)
