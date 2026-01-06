"""
Sentence Models - Sentence and adjustment tracking for BDOCS.

Two core entities:
- Sentence: Criminal sentence record linked to court case
- SentenceAdjustment: Modifications to sentence (good time, remission, etc.)

Key Bahamas considerations:
- Death penalty exists but rarely applied
- No parole system - uses Prerogative of Mercy
- Remission allows up to 1/3 reduction for good behavior
"""
from datetime import datetime, date
from typing import Optional
import uuid

from sqlalchemy import String, Integer, Boolean, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import SentenceType, AdjustmentType


class Sentence(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Sentence record for an inmate.

    Tracks the sentence imposed by the court, including:
    - Fixed-term imprisonment (in months)
    - Life sentences
    - Death sentences (capital cases)
    - Suspended sentences, probation, fines

    Release date calculation accounts for:
    - Original term
    - Time served credits
    - Good time credits
    - Remission (up to 1/3)
    - Any court modifications
    """
    __tablename__ = 'sentences'

    # Foreign keys
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    court_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('court_cases.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Sentence date and type
    sentence_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date sentence was imposed"
    )

    sentence_type: Mapped[str] = mapped_column(
        ENUM(
            'IMPRISONMENT', 'LIFE', 'DEATH', 'SUSPENDED',
            'TIME_SERVED', 'PROBATION', 'FINE',
            name='sentence_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Term details
    original_term_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Original sentence length in months (for fixed terms)"
    )

    life_sentence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this a life sentence?"
    )

    is_death_sentence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this a death sentence (capital case)?"
    )

    minimum_term_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum term for life/indeterminate sentences"
    )

    # Dates
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date sentence begins (may differ from sentence_date)"
    )

    expected_release_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Calculated expected release date"
    )

    actual_release_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual date of release"
    )

    # Time credits (in days)
    time_served_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Pre-trial detention days credited"
    )

    good_time_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Good behavior days credited"
    )

    # Court personnel
    sentencing_judge: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of sentencing judge"
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
        comment="User ID who created record"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_sentences_inmate', 'inmate_id'),
        Index('ix_sentences_case', 'court_case_id'),
        Index('ix_sentences_type', 'sentence_type'),
        Index('ix_sentences_release', 'expected_release_date'),
        Index('ix_sentences_death', 'is_death_sentence',
              postgresql_where="is_death_sentence = true"),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='sentences', lazy='selectin')
    court_case = relationship('CourtCase', back_populates='sentences', lazy='selectin')
    adjustments = relationship(
        'SentenceAdjustment',
        back_populates='sentence',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    clemency_petitions = relationship(
        'ClemencyPetition',
        back_populates='sentence',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        if self.life_sentence:
            term = "LIFE"
        elif self.is_death_sentence:
            term = "DEATH"
        elif self.original_term_months:
            term = f"{self.original_term_months}mo"
        else:
            term = self.sentence_type
        return f"<Sentence {term} inmate={self.inmate_id}>"


class SentenceAdjustment(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Sentence adjustment record.

    Tracks modifications to a sentence:
    - Good time credits (positive = days off)
    - Remission (up to 1/3 for good behavior)
    - Time served credits (pre-trial detention)
    - Clemency reductions (Prerogative of Mercy)
    - Court modifications (appeal outcomes, etc.)
    """
    __tablename__ = 'sentence_adjustments'

    # Foreign key to sentence
    sentence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('sentences.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Adjustment type
    adjustment_type: Mapped[str] = mapped_column(
        ENUM(
            'GOOD_TIME', 'REMISSION', 'TIME_SERVED_CREDIT',
            'CLEMENCY_REDUCTION', 'COURT_MODIFICATION',
            name='adjustment_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Days adjustment (positive = days off sentence, negative = days added)
    days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Days adjustment (positive = reduces sentence)"
    )

    # Effective date
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date adjustment takes effect"
    )

    # Reason and documentation
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reason for adjustment"
    )

    document_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reference to supporting document"
    )

    # Approved by
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who approved adjustment"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_sentence_adjustments_sentence', 'sentence_id'),
        Index('ix_sentence_adjustments_type', 'adjustment_type'),
        Index('ix_sentence_adjustments_date', 'effective_date'),
    )

    # Relationships
    sentence = relationship('Sentence', back_populates='adjustments', lazy='selectin')

    def __repr__(self) -> str:
        sign = "+" if self.days < 0 else "-"
        return f"<SentenceAdjustment {self.adjustment_type} {sign}{abs(self.days)}d>"
