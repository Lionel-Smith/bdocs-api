"""
Visitation Management Models - Visitor tracking and visit scheduling for BDOCS.

This module handles visitor approval, visit scheduling, and visit logging
for inmate visitation at BDOCS facilities.

Three core entities:
- ApprovedVisitor: Visitor registry with background check status
- VisitSchedule: Scheduled visits with conflict prevention
- VisitLog: Actual visit records including security checks
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Date, Time, DateTime, Integer, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import (
    Relationship, IDType, CheckStatus,
    VisitType, VisitStatus
)


class ApprovedVisitor(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Approved visitor registry for BDOCS.

    Visitors must be registered and approved before scheduling visits.
    Background checks are required for approval.

    Each visitor is registered for a specific inmate - the same person
    visiting different inmates requires separate registrations.
    """
    __tablename__ = 'approved_visitors'

    # Link to inmate
    inmate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    relationship: Mapped[Relationship] = mapped_column(
        ENUM(Relationship, name='relationship_enum', create_type=False),
        nullable=False
    )

    # Contact information
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Format: (242) XXX-XXXX"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Identification
    id_type: Mapped[IDType] = mapped_column(
        ENUM(IDType, name='id_type_enum', create_type=False),
        nullable=False
    )

    id_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ID document number"
    )

    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    photo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to visitor photo"
    )

    # Background check
    background_check_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date background check was conducted"
    )

    background_check_status: Mapped[CheckStatus] = mapped_column(
        ENUM(CheckStatus, name='check_status_enum', create_type=False),
        nullable=False,
        default=CheckStatus.PENDING
    )

    # Approval status
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    approved_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )

    denied_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for denial if applicable"
    )

    # Active status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # Table indexes
    __table_args__ = (
        Index('ix_approved_visitors_inmate', 'inmate_id'),
        Index('ix_approved_visitors_name', 'last_name', 'first_name'),
        Index('ix_approved_visitors_status', 'background_check_status'),
        Index('ix_approved_visitors_approved', 'is_approved'),
        Index('ix_approved_visitors_active', 'is_active'),
        # Unique constraint: one visitor per inmate per ID number
        Index(
            'ix_approved_visitors_unique',
            'inmate_id', 'id_type', 'id_number',
            unique=True,
            postgresql_where='is_deleted = false'
        ),
    )

    @property
    def full_name(self) -> str:
        """Return full name in 'Last, First' format."""
        return f"{self.last_name}, {self.first_name}"

    @property
    def age(self) -> int:
        """Calculate current age from date of birth."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    # Relationships
    inmate = relationship(
        'Inmate',
        lazy='selectin'
    )

    approver = relationship(
        'User',
        foreign_keys=[approved_by],
        lazy='selectin'
    )

    scheduled_visits = relationship(
        'VisitSchedule',
        back_populates='visitor',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<ApprovedVisitor {self.full_name} for Inmate {self.inmate_id}>"


class VisitSchedule(AsyncBase, UUIDMixin, AuditMixin):
    """
    Scheduled visit record.

    Manages visit scheduling with conflict prevention and status tracking.
    Legal and clergy visits may have special privileges.
    """
    __tablename__ = 'visit_schedules'

    # References
    inmate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False
    )

    visitor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('approved_visitors.id', ondelete='CASCADE'),
        nullable=False
    )

    # Schedule
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)

    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="Visit duration in minutes"
    )

    # Visit type
    visit_type: Mapped[VisitType] = mapped_column(
        ENUM(VisitType, name='visit_type_enum', create_type=False),
        nullable=False,
        default=VisitType.GENERAL
    )

    # Status
    status: Mapped[VisitStatus] = mapped_column(
        ENUM(VisitStatus, name='visit_status_enum', create_type=False),
        nullable=False,
        default=VisitStatus.SCHEDULED
    )

    # Location
    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Main Visitation Room",
        comment="Visitation area/room"
    )

    # Actual times
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Cancellation
    cancelled_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Created by
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_visit_schedules_inmate', 'inmate_id'),
        Index('ix_visit_schedules_visitor', 'visitor_id'),
        Index('ix_visit_schedules_date', 'scheduled_date'),
        Index('ix_visit_schedules_status', 'status'),
        Index('ix_visit_schedules_type', 'visit_type'),
        # Composite index for daily schedule queries
        Index('ix_visit_schedules_daily', 'scheduled_date', 'scheduled_time', 'status'),
    )

    # Relationships
    inmate = relationship(
        'Inmate',
        lazy='selectin'
    )

    visitor = relationship(
        'ApprovedVisitor',
        back_populates='scheduled_visits',
        lazy='selectin'
    )

    creator = relationship(
        'User',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    visit_log = relationship(
        'VisitLog',
        back_populates='visit_schedule',
        uselist=False,
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<VisitSchedule {self.scheduled_date} {self.scheduled_time} - {self.status.value}>"


class VisitLog(AsyncBase, UUIDMixin, AuditMixin):
    """
    Visit log - actual visit record with security details.

    Created when visitor checks in, records search results
    and any incidents that occurred during the visit.
    """
    __tablename__ = 'visit_logs'

    # Reference to scheduled visit
    visit_schedule_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('visit_schedules.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    # Check-in/out times
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    checked_out_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Security checks
    visitor_searched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    items_stored: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Personal items stored during visit"
    )

    contraband_found: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    # Incident reference (if contraband found or incident occurred)
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('incidents.id', ondelete='SET NULL'),
        nullable=True,
        comment="Linked incident if one occurred"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Processed by (staff who handled check-in)
    processed_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_visit_logs_schedule', 'visit_schedule_id'),
        Index('ix_visit_logs_checked_in', 'checked_in_at'),
        Index('ix_visit_logs_contraband', 'contraband_found'),
        Index('ix_visit_logs_incident', 'incident_id'),
        Index('ix_visit_logs_processed_by', 'processed_by'),
    )

    # Relationships
    visit_schedule = relationship(
        'VisitSchedule',
        back_populates='visit_log',
        lazy='selectin'
    )

    incident = relationship(
        'Incident',
        lazy='selectin'
    )

    processor = relationship(
        'User',
        foreign_keys=[processed_by],
        lazy='selectin'
    )

    @property
    def visit_duration_minutes(self) -> Optional[int]:
        """Calculate actual visit duration in minutes."""
        if self.checked_out_at and self.checked_in_at:
            delta = self.checked_out_at - self.checked_in_at
            return int(delta.total_seconds() / 60)
        return None

    def __repr__(self) -> str:
        return f"<VisitLog {self.visit_schedule_id} checked_in={self.checked_in_at}>"
