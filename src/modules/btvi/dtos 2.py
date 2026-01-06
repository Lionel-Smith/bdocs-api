"""
BTVI Certification DTOs - Pydantic models for validation and serialization.

Supports:
- Certification issuance and updates
- External verification
- Trade-based queries
- Statistics reporting
"""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import BTVICertType, SkillLevel


# ============================================================================
# BTVI Certification DTOs
# ============================================================================

class BTVICertificationCreate(BaseModel):
    """Create a new BTVI certification."""
    inmate_id: UUID
    programme_enrollment_id: Optional[UUID] = Field(
        None,
        description="Link to programme enrollment if cert earned through prison programme"
    )
    certification_type: BTVICertType
    issued_date: date
    expiry_date: Optional[date] = None
    issuing_authority: str = Field(
        default='Bahamas Technical and Vocational Institute (BTVI)',
        max_length=200
    )
    skill_level: SkillLevel
    hours_training: int = Field(..., ge=1, description="Total training hours")
    assessment_score: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Assessment score (0-100)"
    )
    instructor_name: str = Field(..., min_length=1, max_length=200)
    verification_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    @field_validator('instructor_name', 'issuing_authority')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator('expiry_date')
    @classmethod
    def expiry_after_issued(cls, v: Optional[date], info) -> Optional[date]:
        issued = info.data.get('issued_date')
        if v and issued and v <= issued:
            raise ValueError('expiry_date must be after issued_date')
        return v

    model_config = ConfigDict(from_attributes=True)


class BTVICertificationUpdate(BaseModel):
    """Update a BTVI certification."""
    programme_enrollment_id: Optional[UUID] = None
    expiry_date: Optional[date] = None
    issuing_authority: Optional[str] = Field(None, max_length=200)
    skill_level: Optional[SkillLevel] = None
    hours_training: Optional[int] = Field(None, ge=1)
    assessment_score: Optional[Decimal] = Field(None, ge=0, le=100)
    instructor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    verification_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BTVICertificationVerify(BaseModel):
    """Verify a BTVI certification."""
    is_verified: bool = True
    verification_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(
        None,
        description="Notes about verification (e.g., verification method, date)"
    )

    model_config = ConfigDict(from_attributes=True)


class BTVICertificationResponse(BaseModel):
    """BTVI certification response."""
    id: UUID
    inmate_id: UUID
    programme_enrollment_id: Optional[UUID]
    certification_number: str
    certification_type: BTVICertType
    issued_date: date
    expiry_date: Optional[date]
    issuing_authority: str
    skill_level: SkillLevel
    hours_training: int
    assessment_score: Optional[Decimal]
    instructor_name: str
    verification_url: Optional[str]
    is_verified: bool
    is_expired: bool
    is_valid: bool
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class BTVICertificationListResponse(BaseModel):
    """List of BTVI certifications."""
    items: List[BTVICertificationResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary and Statistics DTOs
# ============================================================================

class InmateBTVISummary(BaseModel):
    """Summary of inmate's BTVI certifications."""
    inmate_id: UUID
    total_certifications: int
    valid_certifications: int
    expired_certifications: int
    verified_certifications: int
    by_trade: dict  # trade -> count
    by_skill_level: dict  # level -> count
    total_training_hours: int
    certifications: List[BTVICertificationResponse]

    model_config = ConfigDict(from_attributes=True)


class BTVITradeStatistics(BaseModel):
    """Statistics for a specific trade."""
    certification_type: BTVICertType
    total_certifications: int
    by_skill_level: dict  # level -> count
    average_training_hours: Optional[float]
    average_assessment_score: Optional[float]
    verified_count: int
    expired_count: int

    model_config = ConfigDict(from_attributes=True)


class BTVIStatistics(BaseModel):
    """Overall BTVI certification statistics."""
    total_certifications: int
    valid_certifications: int
    expired_certifications: int
    verified_certifications: int
    by_trade: dict  # trade -> count
    by_skill_level: dict  # level -> count
    issued_this_year: int
    average_training_hours: Optional[float]
    average_assessment_score: Optional[float]
    most_popular_trades: List[dict]  # [{trade, count}]

    model_config = ConfigDict(from_attributes=True)
