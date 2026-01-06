"""
Inmate Model - Core entity for BDOCS Prison Information System.

This model tracks all individuals in custody of the Bahamas Department
of Correctional Services, whether remanded or sentenced.
"""
from datetime import date, datetime
from typing import Optional, List
import uuid

from sqlalchemy import String, Date, DateTime, Integer, Float, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import InmateStatus, SecurityLevel, Gender


# Bahamian Islands for island_of_origin field
BAHAMIAN_ISLANDS = [
    "New Providence", "Grand Bahama", "Abaco", "Eleuthera", "Exuma",
    "Andros", "Long Island", "Cat Island", "San Salvador", "Inagua",
    "Bimini", "Berry Islands", "Acklins", "Crooked Island", "Mayaguana",
    "Ragged Island"
]


class Inmate(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Inmate record for BDOCS.

    Booking number format: BDOCS-{year}-{5-digit-sequence}
    Example: BDOCS-2026-00001

    The Bahamas prison system includes:
    - BDCS (Bahamas Department of Correctional Services) - main facility
    - Simpson Penn Centre for Boys
    - Williemae Pratt Centre for Girls
    """
    __tablename__ = 'inmates'

    # Booking Information
    booking_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Format: BDOCS-YYYY-NNNNN"
    )

    # National ID
    nib_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="National Insurance Board number"
    )

    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    aliases: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Known aliases or street names"
    )

    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    gender: Mapped[Gender] = mapped_column(
        ENUM(Gender, name='gender_enum', create_type=False),
        nullable=False
    )

    nationality: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Bahamian"
    )

    island_of_origin: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Bahamian island of origin (if applicable)"
    )

    # Physical Description
    height_cm: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Height in centimeters"
    )

    weight_kg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Weight in kilograms"
    )

    eye_color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    hair_color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    distinguishing_marks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Tattoos, scars, birthmarks, etc."
    )

    photo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to mugshot/booking photo"
    )

    # Classification
    status: Mapped[InmateStatus] = mapped_column(
        ENUM(InmateStatus, name='inmate_status_enum', create_type=False),
        nullable=False,
        default=InmateStatus.REMAND
    )

    security_level: Mapped[SecurityLevel] = mapped_column(
        ENUM(SecurityLevel, name='security_level_enum', create_type=False),
        nullable=False,
        default=SecurityLevel.MEDIUM
    )

    # Dates
    admission_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    release_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual or projected release date"
    )

    # Contact Information (Emergency Contact)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )

    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Format: (242) XXX-XXXX"
    )

    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Table indexes for common queries
    __table_args__ = (
        Index('ix_inmates_name', 'last_name', 'first_name'),
        Index('ix_inmates_status', 'status'),
        Index('ix_inmates_admission', 'admission_date'),
        Index('ix_inmates_security', 'security_level'),
    )

    @property
    def full_name(self) -> str:
        """Return full name in 'Last, First Middle' format."""
        parts = [self.last_name + ",", self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def age(self) -> int:
        """Calculate current age from date of birth."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    # Relationships
    movements = relationship(
        'Movement',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    classifications = relationship(
        'Classification',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    housing_assignments = relationship(
        'HousingAssignment',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    court_cases = relationship(
        'CourtCase',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    court_appearances = relationship(
        'CourtAppearance',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    sentences = relationship(
        'Sentence',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    clemency_petitions = relationship(
        'ClemencyPetition',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    programme_enrollments = relationship(
        'ProgrammeEnrollment',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    btvi_certifications = relationship(
        'BTVICertification',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    case_assignments = relationship(
        'CaseAssignment',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    case_notes = relationship(
        'CaseNote',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    rehabilitation_goals = relationship(
        'RehabilitationGoal',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    work_release_assignments = relationship(
        'WorkReleaseAssignment',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    reentry_plans = relationship(
        'ReentryPlan',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    reentry_referrals = relationship(
        'ReentryReferral',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    incident_involvements = relationship(
        'IncidentInvolvement',
        back_populates='inmate',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Inmate {self.booking_number}: {self.full_name}>"
