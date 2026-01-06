"""
Court Models - Court cases and appearances for BDOCS.

Two core entities:
- CourtCase: Criminal case record
- CourtAppearance: Scheduled court dates with outcomes
"""
from datetime import datetime, date
from typing import Optional, List
import uuid

from sqlalchemy import String, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import CourtType, CaseStatus, AppearanceType, AppearanceOutcome


class CourtCase(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Court case record for an inmate.

    Tracks the criminal case through the Bahamian court system.
    Case number format varies by court:
    - Magistrates: MC-YYYY-NNNNN
    - Supreme: SC-YYYY-NNNNN
    """
    __tablename__ = 'court_cases'

    # Foreign key to inmate
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Case identification
    case_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Court case number (e.g., MC-2026-00123)"
    )

    # Court type
    court_type: Mapped[str] = mapped_column(
        ENUM(
            'MAGISTRATES', 'SUPREME', 'COURT_OF_APPEAL', 'PRIVY_COUNCIL', 'CORONERS',
            name='court_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Charges (JSONB array for flexibility)
    charges: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of charge objects: [{offense, statute, count, plea}]"
    )

    # Case dates
    filing_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date case was filed"
    )

    # Case status
    status: Mapped[str] = mapped_column(
        ENUM(
            'PENDING', 'ACTIVE', 'ADJUDICATED', 'DISMISSED', 'APPEALED',
            name='case_status_enum',
            create_type=False
        ),
        nullable=False,
        default=CaseStatus.PENDING.value
    )

    # Court personnel
    presiding_judge: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of presiding judge/magistrate"
    )

    prosecutor: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Prosecuting attorney"
    )

    defense_attorney: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Defense attorney"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Table indexes
    __table_args__ = (
        Index('ix_court_cases_inmate', 'inmate_id'),
        Index('ix_court_cases_status', 'status'),
        Index('ix_court_cases_court_type', 'court_type'),
        Index('ix_court_cases_filing_date', 'filing_date'),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='court_cases', lazy='selectin')
    appearances = relationship(
        'CourtAppearance',
        back_populates='court_case',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    sentences = relationship(
        'Sentence',
        back_populates='court_case',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<CourtCase {self.case_number} ({self.status})>"


class CourtAppearance(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Court appearance record.

    Tracks scheduled court dates, their outcomes, and links to
    movement records for transport coordination.
    """
    __tablename__ = 'court_appearances'

    # Foreign keys
    court_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('court_cases.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Appearance details
    appearance_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Scheduled date/time of appearance"
    )

    appearance_type: Mapped[str] = mapped_column(
        ENUM(
            'ARRAIGNMENT', 'BAIL_HEARING', 'TRIAL', 'SENTENCING', 'APPEAL', 'MOTION',
            name='appearance_type_enum',
            create_type=False
        ),
        nullable=False
    )

    court_location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Court location/address"
    )

    # Outcome (nullable until appearance occurs)
    outcome: Mapped[Optional[str]] = mapped_column(
        ENUM(
            'ADJOURNED', 'BAIL_GRANTED', 'BAIL_DENIED', 'CONVICTED',
            'ACQUITTED', 'SENTENCED', 'REMANDED',
            name='appearance_outcome_enum',
            create_type=False
        ),
        nullable=True,
        comment="Outcome of appearance (set after occurrence)"
    )

    # Next appearance date (if adjourned)
    next_appearance_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date of next scheduled appearance"
    )

    # Link to movement for transport coordination
    movement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('movements.id', ondelete='SET NULL'),
        nullable=True,
        comment="Associated movement record for transport"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who scheduled appearance"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_court_appearances_case', 'court_case_id'),
        Index('ix_court_appearances_inmate', 'inmate_id'),
        Index('ix_court_appearances_date', 'appearance_date'),
        Index('ix_court_appearances_upcoming', 'appearance_date', 'outcome',
              postgresql_where="outcome IS NULL"),
    )

    # Relationships
    court_case = relationship('CourtCase', back_populates='appearances', lazy='selectin')
    inmate = relationship('Inmate', back_populates='court_appearances', lazy='selectin')
    # Movement for transport - use foreign_keys since there's bidirectional FKs
    movement = relationship('Movement', lazy='selectin', foreign_keys=[movement_id])

    def __repr__(self) -> str:
        return f"<CourtAppearance {self.appearance_type} on {self.appearance_date.date()}>"
