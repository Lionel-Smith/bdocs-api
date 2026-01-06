"""
Sentence DTOs - Pydantic models for validation and serialization.

Includes DTOs for:
- Sentences
- Sentence Adjustments
- Release calculations
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from src.common.enums import SentenceType, AdjustmentType


# ============================================================================
# Sentence DTOs
# ============================================================================

class SentenceCreate(BaseModel):
    """Create a new sentence."""
    inmate_id: UUID
    court_case_id: UUID
    sentence_date: date
    sentence_type: SentenceType
    original_term_months: Optional[int] = Field(None, ge=1, description="Term in months for fixed sentences")
    life_sentence: bool = False
    is_death_sentence: bool = False
    minimum_term_months: Optional[int] = Field(None, ge=1, description="Minimum term for life sentences")
    start_date: date
    time_served_days: int = Field(0, ge=0, description="Pre-trial detention credit")
    sentencing_judge: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_sentence_type_fields(self):
        """Validate fields based on sentence type."""
        if self.sentence_type == SentenceType.IMPRISONMENT:
            if not self.original_term_months and not self.life_sentence:
                raise ValueError("IMPRISONMENT requires original_term_months or life_sentence=true")

        if self.sentence_type == SentenceType.LIFE:
            self.life_sentence = True

        if self.sentence_type == SentenceType.DEATH:
            self.is_death_sentence = True
            self.life_sentence = False
            self.original_term_months = None

        if self.life_sentence and self.is_death_sentence:
            raise ValueError("Cannot be both life sentence and death sentence")

        return self

    model_config = ConfigDict(from_attributes=True)


class SentenceUpdate(BaseModel):
    """Update a sentence."""
    original_term_months: Optional[int] = Field(None, ge=1)
    minimum_term_months: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    time_served_days: Optional[int] = Field(None, ge=0)
    good_time_days: Optional[int] = Field(None, ge=0)
    sentencing_judge: Optional[str] = Field(None, max_length=200)
    actual_release_date: Optional[date] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SentenceResponse(BaseModel):
    """Sentence response."""
    id: UUID
    inmate_id: UUID
    court_case_id: UUID
    sentence_date: date
    sentence_type: SentenceType
    original_term_months: Optional[int]
    life_sentence: bool
    is_death_sentence: bool
    minimum_term_months: Optional[int]
    start_date: date
    expected_release_date: Optional[date]
    actual_release_date: Optional[date]
    time_served_days: int
    good_time_days: int
    sentencing_judge: Optional[str]
    notes: Optional[str]
    created_by: Optional[UUID]
    inserted_date: datetime
    updated_date: Optional[datetime]
    # Computed fields
    total_adjustment_days: Optional[int] = None
    days_remaining: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SentenceListResponse(BaseModel):
    """List of sentences."""
    items: List[SentenceResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Sentence Adjustment DTOs
# ============================================================================

class SentenceAdjustmentCreate(BaseModel):
    """Create a sentence adjustment."""
    adjustment_type: AdjustmentType
    days: int = Field(..., description="Days to adjust (positive = reduces sentence)")
    effective_date: date
    reason: str = Field(..., min_length=1, max_length=1000)
    document_reference: Optional[str] = Field(None, max_length=100)

    @field_validator('days')
    @classmethod
    def validate_days(cls, v: int) -> int:
        """Days can be positive (reducing sentence) or negative (adding time)."""
        if v == 0:
            raise ValueError("Adjustment days cannot be zero")
        return v

    model_config = ConfigDict(from_attributes=True)


class SentenceAdjustmentResponse(BaseModel):
    """Sentence adjustment response."""
    id: UUID
    sentence_id: UUID
    adjustment_type: AdjustmentType
    days: int
    effective_date: date
    reason: str
    document_reference: Optional[str]
    approved_by: Optional[UUID]
    inserted_date: datetime

    model_config = ConfigDict(from_attributes=True)


class SentenceAdjustmentListResponse(BaseModel):
    """List of sentence adjustments."""
    items: List[SentenceAdjustmentResponse]
    total: int
    total_days_adjusted: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Release Calculation DTOs
# ============================================================================

class ReleaseCalculation(BaseModel):
    """Result of release date calculation."""
    sentence_id: UUID
    inmate_id: UUID
    sentence_type: SentenceType
    original_term_months: Optional[int]
    life_sentence: bool
    is_death_sentence: bool
    start_date: date
    # Credits and adjustments
    time_served_days: int
    good_time_days: int
    adjustment_days: int  # Sum of all adjustments
    total_credits: int  # time_served + good_time + adjustments
    # Remission calculation (up to 1/3)
    eligible_remission_days: int
    max_remission_days: int  # Maximum allowed (1/3 of sentence)
    # Release dates
    original_release_date: Optional[date]  # Without any credits
    expected_release_date: Optional[date]  # With all credits applied
    days_remaining: Optional[int]
    # Flags
    is_eligible_for_release: bool
    release_notes: str

    model_config = ConfigDict(from_attributes=True)


class ReleasingSoonResponse(BaseModel):
    """List of inmates releasing soon."""
    items: List[SentenceResponse]
    total: int
    days_ahead: int
    cutoff_date: date

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary DTOs
# ============================================================================

class InmateSentenceSummary(BaseModel):
    """Summary of inmate's sentences."""
    inmate_id: UUID
    total_sentences: int
    active_sentences: int
    total_term_months: Optional[int]  # Sum of all fixed terms
    has_life_sentence: bool
    has_death_sentence: bool
    earliest_release_date: Optional[date]
    sentences: List[SentenceResponse]

    model_config = ConfigDict(from_attributes=True)
