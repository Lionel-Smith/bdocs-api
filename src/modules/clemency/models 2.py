"""
Clemency Models - Prerogative of Mercy petitions for BDOCS.

CRITICAL: The Bahamas has NO parole system.
Release before sentence completion is only possible through:
1. Prerogative of Mercy (clemency via Governor-General)
2. Statutory remission (up to 1/3 for good behavior)

Constitutional basis: Articles 90-92 of The Bahamas Constitution

Workflow:
SUBMITTED → UNDER_REVIEW → COMMITTEE_SCHEDULED →
AWAITING_MINISTER → GOVERNOR_GENERAL → GRANTED/DENIED

Two core entities:
- ClemencyPetition: The clemency application
- ClemencyStatusHistory: Audit trail of status changes
"""
from datetime import datetime, date
from typing import Optional, List
import uuid

from sqlalchemy import String, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import PetitionType, PetitionStatus


class ClemencyPetition(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Clemency (Prerogative of Mercy) petition.

    Petition number format: CP-YYYY-NNNNN
    Example: CP-2026-00001

    The petition follows a strict constitutional workflow
    through the Advisory Committee and Minister to the
    Governor-General who makes the final decision.
    """
    __tablename__ = 'clemency_petitions'

    # Foreign keys
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    sentence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('sentences.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Petition identification
    petition_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Format: CP-YYYY-NNNNN"
    )

    # Petition type and status
    petition_type: Mapped[str] = mapped_column(
        ENUM(
            'COMMUTATION', 'PARDON', 'REMISSION', 'REPRIEVE',
            name='petition_type_enum',
            create_type=False
        ),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum',
            create_type=False
        ),
        nullable=False,
        default=PetitionStatus.SUBMITTED.value
    )

    # Filing details
    filed_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date petition was filed"
    )

    petitioner_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of person filing petition"
    )

    petitioner_relationship: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Relationship to inmate (self, family, attorney, etc.)"
    )

    # Grounds and documentation
    grounds_for_clemency: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reasons and arguments for clemency"
    )

    supporting_documents: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of document references [{name, type, url, date}]"
    )

    # Victim notification (required for certain offenses)
    victim_notification_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date victim was notified of petition"
    )

    victim_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Victim's response/statement"
    )

    # Advisory Committee review
    committee_review_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of Advisory Committee review"
    )

    committee_recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Committee's recommendation"
    )

    # Minister review
    minister_review_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date Minister reviewed petition"
    )

    minister_recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Minister's recommendation to Governor-General"
    )

    # Governor-General decision
    governor_general_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date presented to Governor-General"
    )

    decision_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of final decision"
    )

    decision_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes on final decision"
    )

    # For granted petitions - sentence reduction in days
    granted_reduction_days: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Days reduced from sentence if granted"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created petition record"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_clemency_petitions_inmate', 'inmate_id'),
        Index('ix_clemency_petitions_sentence', 'sentence_id'),
        Index('ix_clemency_petitions_status', 'status'),
        Index('ix_clemency_petitions_type', 'petition_type'),
        Index('ix_clemency_petitions_filed', 'filed_date'),
        Index('ix_clemency_petitions_pending', 'status',
              postgresql_where="status NOT IN ('GRANTED', 'DENIED', 'WITHDRAWN')"),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='clemency_petitions', lazy='selectin')
    sentence = relationship('Sentence', back_populates='clemency_petitions', lazy='selectin')
    status_history = relationship(
        'ClemencyStatusHistory',
        back_populates='petition',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='ClemencyStatusHistory.changed_date.desc()'
    )

    def __repr__(self) -> str:
        return f"<ClemencyPetition {self.petition_number} ({self.status})>"


class ClemencyStatusHistory(AsyncBase, UUIDMixin, AuditMixin):
    """
    Status transition history for clemency petitions.

    Records every status change with timestamp, user, and notes.
    This is separate from the general audit log for legal documentation.
    """
    __tablename__ = 'clemency_status_history'

    # Foreign key to petition
    petition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('clemency_petitions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Status transition
    from_status: Mapped[Optional[str]] = mapped_column(
        ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum',
            create_type=False
        ),
        nullable=True,
        comment="Previous status (null for initial submission)"
    )

    to_status: Mapped[str] = mapped_column(
        ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum',
            create_type=False
        ),
        nullable=False,
        comment="New status"
    )

    # Timestamp
    changed_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When status changed"
    )

    # Changed by
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who made the change"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about the status change"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_clemency_history_petition', 'petition_id'),
        Index('ix_clemency_history_date', 'changed_date'),
    )

    # Relationships
    petition = relationship('ClemencyPetition', back_populates='status_history', lazy='selectin')

    def __repr__(self) -> str:
        return f"<ClemencyStatusHistory {self.from_status} → {self.to_status}>"
