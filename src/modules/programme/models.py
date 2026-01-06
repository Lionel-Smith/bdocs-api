"""
Programme Models - Rehabilitation programmes for BDOCS.

The Bahamas Department of Correctional Services offers rehabilitation
programmes to support inmate reintegration into society.

Three core entities:
- Programme: Definition of a rehabilitation programme
- ProgrammeSession: Individual sessions within a programme
- ProgrammeEnrollment: Inmate participation in programmes
"""
from datetime import datetime, date, time
from typing import Optional, List
import uuid

from sqlalchemy import String, Date, DateTime, Time, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import ProgrammeCategory, SessionStatus, EnrollmentStatus


class Programme(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Rehabilitation programme definition.

    Programme code format: PRG-XXX (e.g., PRG-EDU, PRG-VOC)

    Each programme can have multiple sessions and enrollments.
    Eligibility criteria stored as JSONB for flexible rules.
    """
    __tablename__ = 'programmes'

    # Programme identification
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique programme code (e.g., PRG-EDU-001)"
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Programme name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed programme description"
    )

    # Category
    category: Mapped[str] = mapped_column(
        ENUM(
            'EDUCATIONAL', 'VOCATIONAL', 'THERAPEUTIC', 'RELIGIOUS', 'LIFE_SKILLS',
            name='programme_category_enum',
            create_type=False
        ),
        nullable=False
    )

    # Provider
    provider: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Internal department or external organization name"
    )

    # Programme structure
    duration_weeks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Programme duration in weeks"
    )

    max_participants: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum number of participants per cohort"
    )

    # Eligibility
    eligibility_criteria: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Flexible eligibility rules as JSON"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether programme is currently accepting enrollments"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created programme record"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_programmes_category', 'category'),
        Index('ix_programmes_active', 'is_active'),
        Index('ix_programmes_active_category', 'is_active', 'category',
              postgresql_where="is_deleted = false"),
    )

    # Relationships
    sessions = relationship(
        'ProgrammeSession',
        back_populates='programme',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='ProgrammeSession.session_date.desc()'
    )

    enrollments = relationship(
        'ProgrammeEnrollment',
        back_populates='programme',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Programme {self.code}: {self.name}>"


class ProgrammeSession(AsyncBase, UUIDMixin, AuditMixin):
    """
    Individual session within a programme.

    Tracks scheduled sessions, attendance, and completion.
    Sessions do not use soft delete - completed sessions are permanent records.
    """
    __tablename__ = 'programme_sessions'

    # Foreign key to programme
    programme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('programmes.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session scheduling
    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of session"
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Session start time"
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Session end time"
    )

    # Location and instructor
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Session location (e.g., Education Wing Room 3)"
    )

    instructor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Instructor or facilitator name"
    )

    # Status
    status: Mapped[str] = mapped_column(
        ENUM(
            'SCHEDULED', 'COMPLETED', 'CANCELLED',
            name='session_status_enum',
            create_type=False
        ),
        nullable=False,
        default=SessionStatus.SCHEDULED.value
    )

    # Attendance
    attendance_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of inmates who attended"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Session notes or observations"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_programme_sessions_programme', 'programme_id'),
        Index('ix_programme_sessions_date', 'session_date'),
        Index('ix_programme_sessions_status', 'status'),
        Index('ix_programme_sessions_upcoming', 'session_date', 'status',
              postgresql_where="status = 'SCHEDULED'"),
    )

    # Relationships
    programme = relationship('Programme', back_populates='sessions', lazy='selectin')

    def __repr__(self) -> str:
        return f"<ProgrammeSession {self.session_date} ({self.status})>"


class ProgrammeEnrollment(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Inmate enrollment in a programme.

    Tracks participation from enrollment through completion.
    Includes grade, hours completed, and certificate issuance.

    Status workflow: ENROLLED → ACTIVE → COMPLETED
    Alternative paths: WITHDRAWN, SUSPENDED
    """
    __tablename__ = 'programme_enrollments'

    # Foreign keys
    programme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('programmes.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Enrollment dates
    enrolled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of enrollment"
    )

    # Status
    status: Mapped[str] = mapped_column(
        ENUM(
            'ENROLLED', 'ACTIVE', 'COMPLETED', 'WITHDRAWN', 'SUSPENDED',
            name='enrollment_status_enum',
            create_type=False
        ),
        nullable=False,
        default=EnrollmentStatus.ENROLLED.value
    )

    # Completion details
    completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of completion (if completed)"
    )

    grade: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Final grade (e.g., A, B, Pass, Fail)"
    )

    certificate_issued: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether completion certificate was issued"
    )

    # Progress tracking
    hours_completed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total programme hours completed"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Enrollment notes (progress, issues, etc.)"
    )

    # Enrolled by
    enrolled_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who enrolled the inmate"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_programme_enrollments_programme', 'programme_id'),
        Index('ix_programme_enrollments_inmate', 'inmate_id'),
        Index('ix_programme_enrollments_status', 'status'),
        Index('ix_programme_enrollments_enrolled', 'enrolled_date'),
        # Unique constraint: one active enrollment per inmate per programme
        Index('ix_programme_enrollments_unique_active', 'programme_id', 'inmate_id',
              unique=True,
              postgresql_where="status IN ('ENROLLED', 'ACTIVE') AND is_deleted = false"),
    )

    # Relationships
    programme = relationship('Programme', back_populates='enrollments', lazy='selectin')
    inmate = relationship('Inmate', back_populates='programme_enrollments', lazy='selectin')
    btvi_certification = relationship(
        'BTVICertification',
        back_populates='programme_enrollment',
        lazy='selectin',
        uselist=False  # One-to-one: one enrollment -> one certification
    )

    def __repr__(self) -> str:
        return f"<ProgrammeEnrollment {self.programme_id} - {self.inmate_id} ({self.status})>"
