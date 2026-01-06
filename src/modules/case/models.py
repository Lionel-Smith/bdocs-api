"""
Case Management Models - Case officer assignments and rehabilitation tracking.

Case management is central to rehabilitation success. Each inmate
is assigned a case officer who:
- Conducts assessments and tracks progress
- Documents interactions via case notes
- Sets and monitors rehabilitation goals
- Coordinates release planning

Three core entities:
- CaseAssignment: Links inmates to case officers (one active per inmate)
- CaseNote: Documented interactions and assessments
- RehabilitationGoal: SMART goals for successful reintegration
"""
from datetime import datetime, date
from typing import Optional
import uuid

from sqlalchemy import String, Date, DateTime, Integer, Boolean, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import NoteType, GoalType, GoalStatus


class CaseAssignment(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Case officer assignment for an inmate.

    Each inmate has exactly one active case officer at a time.
    When a new officer is assigned, the previous assignment is ended.

    The unique partial index ensures only one active assignment per inmate.
    """
    __tablename__ = 'case_assignments'

    # Foreign keys
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    case_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="FK to users table (case officer)"
    )

    # Assignment dates
    assigned_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date officer was assigned to inmate"
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date assignment ended (null if active)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the current active assignment"
    )

    # Notes
    caseload_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about the assignment (special considerations, etc.)"
    )

    # Assigned by
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who made the assignment"
    )

    # Table indexes and constraints
    __table_args__ = (
        Index('ix_case_assignments_inmate', 'inmate_id'),
        Index('ix_case_assignments_officer', 'case_officer_id'),
        Index('ix_case_assignments_active', 'is_active'),
        Index('ix_case_assignments_assigned', 'assigned_date'),
        # Unique partial index: one active assignment per inmate
        Index('ix_case_assignments_unique_active', 'inmate_id',
              unique=True,
              postgresql_where="is_active = true AND is_deleted = false"),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='case_assignments', lazy='selectin')
    case_notes = relationship(
        'CaseNote',
        back_populates='case_assignment',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "ended"
        return f"<CaseAssignment {self.inmate_id} -> {self.case_officer_id} ({status})>"


class CaseNote(AsyncBase, UUIDMixin, AuditMixin):
    """
    Case note documenting interactions and assessments.

    Case notes create a comprehensive record of an inmate's
    progress, incidents, and rehabilitation journey. Notes
    can be confidential (restricted access) and may require follow-up.

    Note: No soft delete - case notes are permanent legal records.
    """
    __tablename__ = 'case_notes'

    # Foreign keys
    case_assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('case_assignments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Denormalized for efficient queries"
    )

    # Note details
    note_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of note/interaction"
    )

    note_type: Mapped[str] = mapped_column(
        ENUM(
            'INITIAL_ASSESSMENT', 'PROGRESS_UPDATE', 'INCIDENT_REPORT',
            'PROGRAMME_REVIEW', 'RELEASE_PLANNING', 'GENERAL',
            name='note_type_enum',
            create_type=False
        ),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Note content"
    )

    # Confidentiality
    is_confidential: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="If true, restricted access (e.g., medical, legal)"
    )

    # Follow-up tracking
    follow_up_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether follow-up action is needed"
    )

    follow_up_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Target date for follow-up (if required)"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created the note"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_case_notes_assignment', 'case_assignment_id'),
        Index('ix_case_notes_inmate', 'inmate_id'),
        Index('ix_case_notes_date', 'note_date'),
        Index('ix_case_notes_type', 'note_type'),
        Index('ix_case_notes_followup', 'follow_up_required', 'follow_up_date',
              postgresql_where="follow_up_required = true"),
    )

    # Relationships
    case_assignment = relationship('CaseAssignment', back_populates='case_notes', lazy='selectin')
    inmate = relationship('Inmate', back_populates='case_notes', lazy='selectin')

    def __repr__(self) -> str:
        return f"<CaseNote {self.note_type} {self.note_date}>"


class RehabilitationGoal(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Rehabilitation goal for an inmate.

    Goals follow the SMART framework:
    - Specific: Clear goal type and title
    - Measurable: Progress percentage (0-100)
    - Achievable: Realistic targets
    - Relevant: Aligned with rehabilitation needs
    - Time-bound: Target completion date

    Goals track progress toward successful reintegration.
    """
    __tablename__ = 'rehabilitation_goals'

    # Foreign key to inmate
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Goal details
    goal_type: Mapped[str] = mapped_column(
        ENUM(
            'EDUCATION', 'VOCATIONAL', 'BEHAVIORAL', 'SUBSTANCE_ABUSE',
            'FAMILY_REUNIFICATION', 'EMPLOYMENT', 'HOUSING',
            name='goal_type_enum',
            create_type=False
        ),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Brief goal title"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed goal description"
    )

    # Timeline
    target_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Target completion date"
    )

    # Status and progress
    status: Mapped[str] = mapped_column(
        ENUM(
            'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'DEFERRED', 'CANCELLED',
            name='goal_status_enum',
            create_type=False
        ),
        nullable=False,
        default=GoalStatus.NOT_STARTED.value
    )

    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Progress toward goal (0-100)"
    )

    # Completion
    completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual completion date (if completed)"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Progress notes and observations"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created the goal"
    )

    # Table indexes and constraints
    __table_args__ = (
        Index('ix_rehabilitation_goals_inmate', 'inmate_id'),
        Index('ix_rehabilitation_goals_type', 'goal_type'),
        Index('ix_rehabilitation_goals_status', 'status'),
        Index('ix_rehabilitation_goals_target', 'target_date'),
        # Partial index for overdue goals
        Index('ix_rehabilitation_goals_overdue', 'target_date', 'status',
              postgresql_where="status IN ('NOT_STARTED', 'IN_PROGRESS') AND is_deleted = false"),
        # Check constraint for progress
        CheckConstraint(
            'progress_percentage >= 0 AND progress_percentage <= 100',
            name='ck_rehabilitation_goals_progress_range'
        ),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='rehabilitation_goals', lazy='selectin')

    @property
    def is_overdue(self) -> bool:
        """Check if goal is past target date and not completed."""
        if self.status in [GoalStatus.COMPLETED.value, GoalStatus.CANCELLED.value]:
            return False
        return date.today() > self.target_date

    def __repr__(self) -> str:
        return f"<RehabilitationGoal {self.goal_type}: {self.title} ({self.status})>"
