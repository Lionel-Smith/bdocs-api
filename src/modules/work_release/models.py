"""
Work Release Models - Structured reintegration through employment.

Work release allows MINIMUM security inmates to work for approved
employers while serving their sentence. This supports:
- Gradual reintegration into society
- Job skill development
- Financial responsibility (savings, restitution)
- Reduced recidivism

Three core entities:
- WorkReleaseEmployer: Approved employers with MOU agreements
- WorkReleaseAssignment: Inmate work assignments
- WorkReleaseLog: Daily departure/return tracking

CRITICAL: Only MINIMUM security inmates are eligible for work release.
"""
from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal
import uuid

from sqlalchemy import String, Date, DateTime, Time, Boolean, Text, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import WorkReleaseStatus, LogStatus


class WorkReleaseEmployer(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Approved employer for work release programme.

    Employers must:
    - Be vetted and approved by BDOCS
    - Sign a Memorandum of Understanding (MOU)
    - Provide appropriate supervision
    - Report any issues immediately

    Phone format: (242) XXX-XXXX (Bahamas)
    """
    __tablename__ = 'work_release_employers'

    # Business information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Business/employer name"
    )

    business_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of business (construction, restaurant, etc.)"
    )

    # Contact information
    contact_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Primary contact person"
    )

    contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Format: (242) XXX-XXXX"
    )

    contact_email: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Contact email address"
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Business address"
    )

    # Approval status
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether employer is approved for work release"
    )

    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of approval"
    )

    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who approved employer"
    )

    # MOU (Memorandum of Understanding)
    mou_signed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether MOU has been signed"
    )

    mou_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="MOU expiration date (requires renewal)"
    )

    # Notes and status
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about employer"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether employer is currently accepting work release inmates"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_work_release_employers_name', 'name'),
        Index('ix_work_release_employers_approved', 'is_approved'),
        Index('ix_work_release_employers_active', 'is_active'),
        Index('ix_work_release_employers_mou', 'mou_signed', 'mou_expiry_date'),
    )

    # Relationships
    assignments = relationship(
        'WorkReleaseAssignment',
        back_populates='employer',
        lazy='selectin'
    )

    @property
    def is_mou_valid(self) -> bool:
        """Check if MOU is signed and not expired."""
        if not self.mou_signed:
            return False
        if self.mou_expiry_date and self.mou_expiry_date < date.today():
            return False
        return True

    @property
    def can_accept_inmates(self) -> bool:
        """Check if employer can accept new work release inmates."""
        return self.is_approved and self.is_active and self.is_mou_valid

    def __repr__(self) -> str:
        status = "approved" if self.is_approved else "pending"
        return f"<WorkReleaseEmployer {self.name} ({status})>"


class WorkReleaseAssignment(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Work release assignment linking an inmate to an employer.

    CRITICAL: Only MINIMUM security inmates are eligible.

    Workflow: PENDING_APPROVAL → APPROVED → ACTIVE → COMPLETED
    Alternative paths: SUSPENDED, TERMINATED

    Work schedule stored as JSONB for flexibility:
    {"monday": {"start": "08:00", "end": "17:00"}, ...}
    """
    __tablename__ = 'work_release_assignments'

    # Foreign keys
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('work_release_employers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )

    # Position details
    position_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Job title/position"
    )

    # Assignment dates
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Assignment start date"
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Assignment end date (null if ongoing)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        ENUM(
            'PENDING_APPROVAL', 'APPROVED', 'ACTIVE',
            'SUSPENDED', 'COMPLETED', 'TERMINATED',
            name='work_release_status_enum',
            create_type=False
        ),
        nullable=False,
        default=WorkReleaseStatus.PENDING_APPROVAL.value
    )

    # Compensation
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Hourly pay rate in BSD"
    )

    # Schedule (JSONB for flexibility)
    work_schedule: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Weekly schedule as JSON"
    )

    # Supervisor at workplace
    supervisor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="On-site supervisor name"
    )

    supervisor_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Supervisor phone (242) XXX-XXXX"
    )

    # Approval
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who approved assignment"
    )

    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of approval"
    )

    # Termination
    termination_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for early termination (if applicable)"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Assignment notes"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created assignment"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_work_release_assignments_inmate', 'inmate_id'),
        Index('ix_work_release_assignments_employer', 'employer_id'),
        Index('ix_work_release_assignments_status', 'status'),
        Index('ix_work_release_assignments_dates', 'start_date', 'end_date'),
        # Partial index for active assignments
        Index('ix_work_release_assignments_active', 'status',
              postgresql_where="status = 'ACTIVE' AND is_deleted = false"),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='work_release_assignments', lazy='selectin')
    employer = relationship('WorkReleaseEmployer', back_populates='assignments', lazy='selectin')
    logs = relationship(
        'WorkReleaseLog',
        back_populates='assignment',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='WorkReleaseLog.log_date.desc()'
    )

    def __repr__(self) -> str:
        return f"<WorkReleaseAssignment {self.inmate_id} -> {self.position_title} ({self.status})>"


class WorkReleaseLog(AsyncBase, UUIDMixin, AuditMixin):
    """
    Daily log entry for work release departure and return.

    Tracks:
    - Departure time
    - Expected return time (based on schedule)
    - Actual return time
    - Late returns and no-shows

    No soft delete - logs are permanent security records.
    """
    __tablename__ = 'work_release_logs'

    # Foreign key to assignment
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('work_release_assignments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Log date
    log_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of work release"
    )

    # Times
    departure_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Time inmate departed facility"
    )

    expected_return_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Expected return time"
    )

    actual_return_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Actual return time (null if not yet returned)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        ENUM(
            'DEPARTED', 'RETURNED_ON_TIME', 'RETURNED_LATE',
            'DID_NOT_RETURN', 'EXCUSED',
            name='log_status_enum',
            create_type=False
        ),
        nullable=False,
        default=LogStatus.DEPARTED.value
    )

    # Verification
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who verified return"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes (especially for late/no-return)"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_work_release_logs_assignment', 'assignment_id'),
        Index('ix_work_release_logs_date', 'log_date'),
        Index('ix_work_release_logs_status', 'status'),
        # Partial index for unresolved logs (departed but not returned)
        Index('ix_work_release_logs_unresolved', 'status', 'log_date',
              postgresql_where="status = 'DEPARTED'"),
        # Unique: one log per assignment per day
        Index('ix_work_release_logs_unique_day', 'assignment_id', 'log_date',
              unique=True),
    )

    # Relationships
    assignment = relationship('WorkReleaseAssignment', back_populates='logs', lazy='selectin')

    @property
    def is_late(self) -> bool:
        """Check if return was late."""
        if not self.actual_return_time:
            return False
        return self.actual_return_time > self.expected_return_time

    @property
    def minutes_late(self) -> Optional[int]:
        """Calculate minutes late (if applicable)."""
        if not self.actual_return_time or not self.is_late:
            return None
        expected_minutes = self.expected_return_time.hour * 60 + self.expected_return_time.minute
        actual_minutes = self.actual_return_time.hour * 60 + self.actual_return_time.minute
        return actual_minutes - expected_minutes

    def __repr__(self) -> str:
        return f"<WorkReleaseLog {self.log_date} ({self.status})>"
