"""
Reports Module Models - Report definitions and execution tracking.

This module provides a framework for generating various reports
across all BDOCS modules including population, incidents, programmes,
healthcare, and compliance.

Two core entities:
- ReportDefinition: Template/configuration for report types
- ReportExecution: Individual report generation records

Report definitions are seeded and rarely modified. Each execution
tracks a specific generation request with parameters and output.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Integer, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, AuditMixin
from src.common.enums import ReportCategory, OutputFormat, ReportStatus


class ReportDefinition(AsyncBase, UUIDMixin, AuditMixin):
    """
    Report definition/template.

    Defines available report types with their parameters, category,
    and output format. Report codes follow pattern: RPT-{CATEGORY}-{NUMBER}
    (e.g., RPT-POP-001 for population report #1).

    These records are typically seeded and rarely modified.
    """
    __tablename__ = 'report_definitions'

    # Report identification
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique report code (e.g., 'RPT-POP-001')"
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable report name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of report contents"
    )

    # Classification
    category: Mapped[ReportCategory] = mapped_column(
        ENUM(ReportCategory, name='report_category_enum', create_type=False),
        nullable=False,
        comment="Report category for organization"
    )

    # Parameters schema (JSON Schema format)
    parameters_schema: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON Schema defining required/optional parameters"
    )

    # Output configuration
    output_format: Mapped[OutputFormat] = mapped_column(
        ENUM(OutputFormat, name='output_format_enum', create_type=False),
        nullable=False,
        default=OutputFormat.PDF,
        comment="Default output format for this report"
    )

    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this report runs on a schedule"
    )

    schedule_cron: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Cron expression for scheduled reports (e.g., '0 6 * * *')"
    )

    # Tracking
    last_generated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this report was last successfully generated"
    )

    # Created by
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_report_definitions_category', 'category'),
        Index('ix_report_definitions_scheduled', 'is_scheduled'),
    )

    # Relationships
    creator = relationship(
        'User',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    executions = relationship(
        'ReportExecution',
        back_populates='definition',
        lazy='selectin',
        order_by='desc(ReportExecution.started_at)'
    )

    def __repr__(self) -> str:
        return f"<ReportDefinition {self.code}: {self.name}>"


class ReportExecution(AsyncBase, UUIDMixin, AuditMixin):
    """
    Report execution record.

    Tracks individual report generation requests including parameters,
    status, timing, and output file location.

    Workflow: QUEUED → GENERATING → COMPLETED/FAILED
    """
    __tablename__ = 'report_executions'

    # Reference to definition
    report_definition_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('report_definitions.id', ondelete='CASCADE'),
        nullable=False
    )

    # Parameters used for this execution
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Parameters used for this execution"
    )

    # Status tracking
    status: Mapped[ReportStatus] = mapped_column(
        ENUM(ReportStatus, name='report_status_enum', create_type=False),
        nullable=False,
        default=ReportStatus.QUEUED
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When execution started"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When execution completed (success or failure)"
    )

    # Output file
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to generated report file"
    )

    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Size of generated file in bytes"
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if generation failed"
    )

    # Requested by
    requested_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_report_executions_definition', 'report_definition_id'),
        Index('ix_report_executions_status', 'status'),
        Index('ix_report_executions_started', 'started_at'),
        Index('ix_report_executions_requested', 'requested_by'),
        # Partial index for active executions
        Index(
            'ix_report_executions_active',
            'status', 'started_at',
            postgresql_where='status IN (\'QUEUED\', \'GENERATING\')'
        ),
    )

    # Relationships
    definition = relationship(
        'ReportDefinition',
        back_populates='executions',
        lazy='selectin'
    )

    requester = relationship(
        'User',
        foreign_keys=[requested_by],
        lazy='selectin'
    )

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate execution duration in seconds."""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds())
        return None

    @property
    def is_complete(self) -> bool:
        """Check if execution has finished (success or failure)."""
        return self.status in [ReportStatus.COMPLETED, ReportStatus.FAILED]

    def __repr__(self) -> str:
        return f"<ReportExecution {self.definition.code if self.definition else 'unknown'} [{self.status.value}]>"
