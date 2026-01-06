"""
Inmate DTOs - Pydantic models for request/response validation.

Includes Bahamas-specific validations like phone number format.
"""
import re
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.common.enums import InmateStatus, SecurityLevel, Gender
from src.modules.inmate.models import BAHAMIAN_ISLANDS


# Bahamas phone regex: (242) XXX-XXXX or 242-XXX-XXXX or 242XXXXXXX
BAHAMAS_PHONE_PATTERN = re.compile(
    r'^(\(242\)\s?|242[-\s]?)?[0-9]{3}[-\s]?[0-9]{4}$'
)


def validate_bahamas_phone(phone: Optional[str]) -> Optional[str]:
    """
    Validate and normalize Bahamas phone number.
    Returns format: (242) XXX-XXXX
    """
    if phone is None:
        return None

    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)

    # Handle 7-digit local number
    if len(digits) == 7:
        digits = '242' + digits

    # Must be 10 digits (242 + 7 local)
    if len(digits) != 10 or not digits.startswith('242'):
        raise ValueError('Phone must be a valid Bahamas number: (242) XXX-XXXX')

    # Format as (242) XXX-XXXX
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


class InmateBase(BaseModel):
    """Base fields shared across DTOs."""
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    aliases: Optional[List[str]] = Field(default_factory=list)
    date_of_birth: date
    gender: Gender
    nationality: str = Field(default="Bahamian", max_length=100)
    island_of_origin: Optional[str] = Field(None, max_length=50)

    # Physical description
    height_cm: Optional[int] = Field(None, ge=50, le=250)
    weight_kg: Optional[float] = Field(None, ge=20, le=300)
    eye_color: Optional[str] = Field(None, max_length=30)
    hair_color: Optional[str] = Field(None, max_length=30)
    distinguishing_marks: Optional[str] = None

    @field_validator('island_of_origin')
    @classmethod
    def validate_island(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in BAHAMIAN_ISLANDS:
            raise ValueError(f'Invalid island. Must be one of: {", ".join(BAHAMIAN_ISLANDS)}')
        return v

    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        age = (date.today() - v).days // 365
        if age < 16:
            raise ValueError('Inmate must be at least 16 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        return v


class InmateCreate(InmateBase):
    """DTO for creating a new inmate during intake."""
    nib_number: Optional[str] = Field(None, max_length=20)
    photo_url: Optional[str] = Field(None, max_length=500)
    status: InmateStatus = Field(default=InmateStatus.REMAND)
    security_level: SecurityLevel = Field(default=SecurityLevel.MEDIUM)
    admission_date: Optional[datetime] = None  # Defaults to now if not provided

    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)

    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_bahamas_phone(v)

    model_config = ConfigDict(from_attributes=True)


class InmateUpdate(BaseModel):
    """DTO for updating inmate information."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    aliases: Optional[List[str]] = None
    nib_number: Optional[str] = Field(None, max_length=20)

    # Physical description
    height_cm: Optional[int] = Field(None, ge=50, le=250)
    weight_kg: Optional[float] = Field(None, ge=20, le=300)
    eye_color: Optional[str] = Field(None, max_length=30)
    hair_color: Optional[str] = Field(None, max_length=30)
    distinguishing_marks: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=500)

    # Classification
    status: Optional[InmateStatus] = None
    security_level: Optional[SecurityLevel] = None
    release_date: Optional[datetime] = None

    # Emergency contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)

    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_bahamas_phone(v)

    model_config = ConfigDict(from_attributes=True)


class InmateResponse(BaseModel):
    """DTO for returning inmate data in API responses."""
    id: UUID
    booking_number: str
    nib_number: Optional[str]

    # Personal info
    first_name: str
    middle_name: Optional[str]
    last_name: str
    full_name: str  # Computed property
    aliases: Optional[List[str]]
    date_of_birth: date
    age: int  # Computed property
    gender: Gender
    nationality: str
    island_of_origin: Optional[str]

    # Physical description
    height_cm: Optional[int]
    weight_kg: Optional[float]
    eye_color: Optional[str]
    hair_color: Optional[str]
    distinguishing_marks: Optional[str]
    photo_url: Optional[str]

    # Classification
    status: InmateStatus
    security_level: SecurityLevel
    admission_date: datetime
    release_date: Optional[datetime]

    # Emergency contact
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]

    # Audit fields
    inserted_date: datetime
    updated_date: Optional[datetime]
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class InmateListResponse(BaseModel):
    """Paginated list response for inmates."""
    items: List[InmateResponse]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class InmateSearchParams(BaseModel):
    """Query parameters for inmate search."""
    query: Optional[str] = Field(None, min_length=2, description="Search name or booking number")
    status: Optional[InmateStatus] = None
    security_level: Optional[SecurityLevel] = None
    gender: Optional[Gender] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
