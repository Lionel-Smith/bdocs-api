"""
BTVI Certification Models - Official vocational certifications for BDOCS.

BTVI (Bahamas Technical and Vocational Institute) is the primary
vocational training institution in The Bahamas. Certifications
earned through prison programmes can be linked to official BTVI
credentials, enhancing post-release employment prospects.

Key features:
- Unique certification numbers (BTVI-YYYY-NNNNN)
- Optional linkage to programme enrollments
- Skill level progression tracking
- External verification support
"""
from datetime import date
from typing import Optional
from decimal import Decimal
import uuid

from sqlalchemy import String, Date, Integer, Boolean, Text, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import BTVICertType, SkillLevel


class BTVICertification(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    BTVI vocational certification record.

    Certification number format: BTVI-YYYY-NNNNN
    Example: BTVI-2026-00001

    Can be linked to a programme enrollment for certifications
    earned through prison rehabilitation programmes, or standalone
    for prior certifications or external training.
    """
    __tablename__ = 'btvi_certifications'

    # Foreign keys
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Optional link to programme enrollment
    programme_enrollment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('programme_enrollments.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Link to programme enrollment if cert earned through prison programme"
    )

    # Certification identification
    certification_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Format: BTVI-YYYY-NNNNN"
    )

    # Certification type (trade)
    certification_type: Mapped[str] = mapped_column(
        ENUM(
            'AUTOMOTIVE', 'ELECTRICAL', 'PLUMBING', 'CARPENTRY',
            'WELDING', 'CULINARY', 'COSMETOLOGY', 'HVAC', 'MASONRY',
            name='btvi_cert_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Dates
    issued_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date certification was issued"
    )

    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expiration date (null for non-expiring certifications)"
    )

    # Issuing authority
    issuing_authority: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default='Bahamas Technical and Vocational Institute (BTVI)',
        comment="Issuing institution name"
    )

    # Skill level
    skill_level: Mapped[str] = mapped_column(
        ENUM(
            'BASIC', 'INTERMEDIATE', 'ADVANCED', 'MASTER',
            name='skill_level_enum',
            create_type=False
        ),
        nullable=False
    )

    # Training details
    hours_training: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total hours of training completed"
    )

    assessment_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Final assessment score (e.g., 85.50)"
    )

    instructor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of certifying instructor"
    )

    # Verification
    verification_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL for external verification"
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether certification has been externally verified"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about certification"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created certification record"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_btvi_certifications_inmate', 'inmate_id'),
        Index('ix_btvi_certifications_enrollment', 'programme_enrollment_id'),
        Index('ix_btvi_certifications_type', 'certification_type'),
        Index('ix_btvi_certifications_level', 'skill_level'),
        Index('ix_btvi_certifications_issued', 'issued_date'),
        Index('ix_btvi_certifications_verified', 'is_verified'),
        # Composite index for trade queries
        Index('ix_btvi_certifications_type_level', 'certification_type', 'skill_level'),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='btvi_certifications', lazy='selectin')
    programme_enrollment = relationship(
        'ProgrammeEnrollment',
        back_populates='btvi_certification',
        lazy='selectin'
    )

    @property
    def is_expired(self) -> bool:
        """Check if certification has expired."""
        if self.expiry_date is None:
            return False
        return date.today() > self.expiry_date

    @property
    def is_valid(self) -> bool:
        """Check if certification is currently valid."""
        return not self.is_expired and not self.is_deleted

    def __repr__(self) -> str:
        return f"<BTVICertification {self.certification_number}: {self.certification_type} ({self.skill_level})>"
