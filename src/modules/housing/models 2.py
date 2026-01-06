"""
Housing & Classification Models for BDOCS.

Three core entities:
- HousingUnit: Physical housing locations at Fox Hill
- Classification: Security classification assessments
- HousingAssignment: Inmate-to-unit assignments
"""
from datetime import datetime, date
from typing import Optional
import uuid

from sqlalchemy import String, Integer, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import SecurityLevel, Gender


class HousingUnit(AsyncBase, UUIDMixin, AuditMixin):
    """
    Housing unit at Fox Hill Correctional Facility.

    Fox Hill has 11 primary units:
    - Maximum: MAX-A, MAX-B, MAX-C (high security inmates)
    - Medium: MED-A, MED-B, MED-C (general population)
    - Minimum: MIN-A, MIN-B (low risk, work release eligible)
    - Female: FEM-1 (female inmates)
    - Remand: REM-1 (pre-trial detainees)
    - Juvenile: JUV-1 (under 18)
    """
    __tablename__ = 'housing_units'

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Unit code (e.g., MAX-A, FEM-1)"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full unit name"
    )

    security_level: Mapped[SecurityLevel] = mapped_column(
        ENUM(SecurityLevel, name='security_level_enum', create_type=False),
        nullable=False
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum number of inmates"
    )

    current_occupancy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current number of inmates"
    )

    gender_restriction: Mapped[Optional[Gender]] = mapped_column(
        ENUM(Gender, name='gender_enum', create_type=False),
        nullable=True,
        comment="Gender restriction (NULL = any)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether unit is accepting inmates"
    )

    is_juvenile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Juvenile-only unit"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    __table_args__ = (
        Index('ix_housing_units_security', 'security_level'),
        Index('ix_housing_units_active', 'is_active'),
    )

    # Relationships
    assignments = relationship(
        'HousingAssignment',
        back_populates='housing_unit',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    @property
    def available_beds(self) -> int:
        """Calculate available bed count."""
        return max(0, self.capacity - self.current_occupancy)

    @property
    def occupancy_rate(self) -> float:
        """Calculate occupancy percentage."""
        if self.capacity == 0:
            return 0.0
        return round(self.current_occupancy / self.capacity * 100, 1)

    @property
    def is_overcrowded(self) -> bool:
        """Check if unit exceeds capacity."""
        return self.current_occupancy > self.capacity

    def __repr__(self) -> str:
        return f"<HousingUnit {self.code}: {self.current_occupancy}/{self.capacity}>"


class Classification(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Security classification assessment for an inmate.

    Classification scoring (each factor 1-5 points):
    - charge_severity: Seriousness of current charges
    - prior_record: Criminal history
    - institutional_behavior: Conduct while incarcerated
    - escape_risk: Flight risk assessment
    - violence_risk: Risk of violent behavior

    Total Score Classification:
    - >= 20: MAXIMUM security
    - >= 12: MEDIUM security
    - < 12: MINIMUM security
    """
    __tablename__ = 'classifications'

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    classification_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )

    security_level: Mapped[SecurityLevel] = mapped_column(
        ENUM(SecurityLevel, name='security_level_enum', create_type=False),
        nullable=False
    )

    # Classification scores (JSONB for flexibility)
    scores: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Scoring factors: charge_severity, prior_record, institutional_behavior, escape_risk, violence_risk (each 1-5)"
    )

    total_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sum of all score factors"
    )

    review_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next scheduled review date"
    )

    classified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who performed classification"
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Classification notes and rationale"
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the active classification"
    )

    __table_args__ = (
        Index('ix_classifications_inmate', 'inmate_id'),
        Index('ix_classifications_current', 'inmate_id', 'is_current'),
        Index('ix_classifications_review', 'review_date'),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='classifications', lazy='selectin')

    def __repr__(self) -> str:
        return f"<Classification {self.inmate_id}: {self.security_level.value} (score={self.total_score})>"


class HousingAssignment(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Inmate housing assignment record.

    Tracks which inmate is assigned to which housing unit,
    including cell and bed numbers for detailed tracking.
    """
    __tablename__ = 'housing_assignments'

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    housing_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('housing_units.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    cell_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Cell number within unit"
    )

    bed_number: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Bed designation (A, B, etc.)"
    )

    assigned_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When assignment ended"
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the active assignment"
    )

    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who made assignment"
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Reason for assignment/transfer"
    )

    __table_args__ = (
        Index('ix_housing_assignments_inmate', 'inmate_id'),
        Index('ix_housing_assignments_unit', 'housing_unit_id'),
        Index('ix_housing_assignments_current', 'inmate_id', 'is_current'),
        Index('ix_housing_assignments_dates', 'assigned_date', 'end_date'),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='housing_assignments', lazy='selectin')
    housing_unit = relationship('HousingUnit', back_populates='assignments', lazy='selectin')

    def __repr__(self) -> str:
        status = "current" if self.is_current else "ended"
        return f"<HousingAssignment {self.inmate_id} -> {self.housing_unit_id} ({status})>"
