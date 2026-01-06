"""
Healthcare DTOs - Data Transfer Objects for healthcare management.

HIPAA NOTE: These DTOs handle Protected Health Information (PHI).
Ensure role-based access control is enforced at the API layer.

Provides structured data validation for medical records,
encounters, and medication administration.
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.common.enums import (
    BloodType, EncounterType, ProviderType,
    RouteType, MedAdminStatus
)


# =============================================================================
# Vitals DTO
# =============================================================================

class VitalsDTO(BaseModel):
    """Vital signs recorded during encounter."""
    model_config = ConfigDict(from_attributes=True)

    bp: Optional[str] = Field(None, description="Blood pressure (e.g., '120/80')")
    pulse: Optional[int] = Field(None, ge=0, le=300, description="Heart rate BPM")
    temp: Optional[float] = Field(None, ge=90, le=110, description="Temperature °F")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    resp_rate: Optional[int] = Field(None, ge=0, le=100, description="Respiratory rate")
    o2_sat: Optional[int] = Field(None, ge=0, le=100, description="Oxygen saturation %")


# =============================================================================
# Medical Record DTOs
# =============================================================================

class AllergyDTO(BaseModel):
    """Allergy entry."""
    model_config = ConfigDict(from_attributes=True)

    allergen: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., description="mild/moderate/severe")
    reaction: Optional[str] = Field(None, max_length=500)


class ChronicConditionDTO(BaseModel):
    """Chronic condition entry."""
    model_config = ConfigDict(from_attributes=True)

    condition: str = Field(..., min_length=1, max_length=200)
    diagnosed_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)


class CurrentMedicationDTO(BaseModel):
    """Current medication entry."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    prescriber: Optional[str] = Field(None, max_length=200)


class DietaryRestrictionDTO(BaseModel):
    """Dietary restriction entry."""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="medical/religious/allergy")
    details: str = Field(..., max_length=500)


class MedicalRecordCreateDTO(BaseModel):
    """Create a medical record (intake screening)."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID = Field(..., description="Inmate to create record for")
    blood_type: Optional[BloodType] = None
    allergies: Optional[List[AllergyDTO]] = None
    chronic_conditions: Optional[List[ChronicConditionDTO]] = None
    current_medications: Optional[List[CurrentMedicationDTO]] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    mental_health_flag: bool = Field(default=False)
    suicide_watch: bool = Field(default=False)
    dietary_restrictions: Optional[List[DietaryRestrictionDTO]] = None
    disability_accommodations: Optional[str] = Field(None, max_length=2000)


class MedicalRecordUpdateDTO(BaseModel):
    """Update a medical record."""
    model_config = ConfigDict(from_attributes=True)

    blood_type: Optional[BloodType] = None
    allergies: Optional[List[AllergyDTO]] = None
    chronic_conditions: Optional[List[ChronicConditionDTO]] = None
    current_medications: Optional[List[CurrentMedicationDTO]] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    last_physical_date: Optional[date] = None
    next_physical_due: Optional[date] = None
    mental_health_flag: Optional[bool] = None
    dietary_restrictions: Optional[List[DietaryRestrictionDTO]] = None
    disability_accommodations: Optional[str] = Field(None, max_length=2000)


class SuicideWatchUpdateDTO(BaseModel):
    """Update suicide watch status - CRITICAL."""
    model_config = ConfigDict(from_attributes=True)

    suicide_watch: bool = Field(..., description="Enable or disable suicide watch")
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for change")


class MedicalRecordDTO(BaseModel):
    """Medical record response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    inmate_booking_number: Optional[str] = None
    blood_type: Optional[BloodType] = None
    allergies: Optional[List[dict]] = None
    chronic_conditions: Optional[List[dict]] = None
    current_medications: Optional[List[dict]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    last_physical_date: Optional[date] = None
    next_physical_due: Optional[date] = None
    mental_health_flag: bool
    suicide_watch: bool
    dietary_restrictions: Optional[List[dict]] = None
    disability_accommodations: Optional[str] = None
    created_by: UUID
    creator_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class MedicalRecordSummaryDTO(BaseModel):
    """Minimal medical record info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: str
    blood_type: Optional[BloodType] = None
    allergy_count: int
    chronic_condition_count: int
    mental_health_flag: bool
    suicide_watch: bool


# =============================================================================
# Medical Encounter DTOs
# =============================================================================

class PrescribedMedicationDTO(BaseModel):
    """Medication prescribed during encounter."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)


class EncounterCreateDTO(BaseModel):
    """Create a medical encounter."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID = Field(..., description="Inmate being seen")
    encounter_type: EncounterType = Field(...)
    chief_complaint: str = Field(..., min_length=1, max_length=2000)
    vitals: Optional[VitalsDTO] = None
    diagnosis: Optional[str] = Field(None, max_length=2000)
    treatment: Optional[str] = Field(None, max_length=2000)
    medications_prescribed: Optional[List[PrescribedMedicationDTO]] = None
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[date] = None
    provider_name: str = Field(..., min_length=1, max_length=200)
    provider_type: ProviderType = Field(...)
    location: str = Field(default="Medical Unit", max_length=100)
    referred_external: bool = Field(default=False)
    external_facility: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=5000)


class EncounterDTO(BaseModel):
    """Medical encounter response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    inmate_booking_number: Optional[str] = None
    encounter_date: datetime
    encounter_type: EncounterType
    chief_complaint: str
    vitals: Optional[dict] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    medications_prescribed: Optional[List[dict]] = None
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    provider_name: str
    provider_type: ProviderType
    location: str
    referred_external: bool
    external_facility: Optional[str] = None
    notes: Optional[str] = None
    created_by: UUID
    creator_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class EncounterListDTO(BaseModel):
    """Minimal encounter info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_name: str
    encounter_date: datetime
    encounter_type: EncounterType
    chief_complaint: str
    provider_name: str
    provider_type: ProviderType
    follow_up_required: bool


# =============================================================================
# Medication Administration DTOs
# =============================================================================

class MedicationScheduleDTO(BaseModel):
    """Schedule a medication administration."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID = Field(..., description="Inmate receiving medication")
    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    route: RouteType = Field(default=RouteType.ORAL)
    scheduled_time: datetime = Field(..., description="When medication is due")
    notes: Optional[str] = Field(None, max_length=1000)


class MedicationAdministerDTO(BaseModel):
    """Record medication administration."""
    model_config = ConfigDict(from_attributes=True)

    notes: Optional[str] = Field(None, max_length=1000)


class MedicationRefuseDTO(BaseModel):
    """Record medication refusal - requires witness."""
    model_config = ConfigDict(from_attributes=True)

    refusal_witnessed_by: UUID = Field(..., description="Staff who witnessed refusal")
    notes: Optional[str] = Field(None, max_length=1000)


class MedicationAdminDTO(BaseModel):
    """Medication administration response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: Optional[str] = None
    inmate_booking_number: Optional[str] = None
    medication_name: str
    dosage: str
    route: RouteType
    scheduled_time: datetime
    administered_time: Optional[datetime] = None
    administered_by: Optional[UUID] = None
    administrator_name: Optional[str] = None
    status: MedAdminStatus
    refusal_witnessed_by: Optional[UUID] = None
    witness_name: Optional[str] = None
    notes: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class MedicationDueDTO(BaseModel):
    """Medication due for administration."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inmate_id: UUID
    inmate_name: str
    inmate_booking_number: str
    medication_name: str
    dosage: str
    route: RouteType
    scheduled_time: datetime
    minutes_until_due: int
    is_overdue: bool


# =============================================================================
# Suicide Watch DTO
# =============================================================================

class SuicideWatchInmateDTO(BaseModel):
    """Inmate on suicide watch."""
    model_config = ConfigDict(from_attributes=True)

    inmate_id: UUID
    inmate_name: str
    inmate_booking_number: str
    housing_unit: Optional[str] = None
    suicide_watch_since: Optional[datetime] = None
    mental_health_flag: bool
    last_encounter_date: Optional[datetime] = None
    last_encounter_type: Optional[EncounterType] = None


# =============================================================================
# Statistics DTO
# =============================================================================

class HealthcareStatisticsDTO(BaseModel):
    """Healthcare statistics summary."""
    model_config = ConfigDict(from_attributes=True)

    # Medical records
    total_medical_records: int
    inmates_with_allergies: int
    inmates_with_chronic_conditions: int

    # Mental health
    mental_health_flagged: int
    on_suicide_watch: int

    # Encounters today
    encounters_today: int
    by_encounter_type: dict  # EncounterType -> count
    external_referrals_today: int

    # Medications
    medications_scheduled_today: int
    medications_administered_today: int
    medications_refused_today: int
    medications_missed_today: int

    # Upcoming
    follow_ups_due_week: int
    physicals_due_month: int
