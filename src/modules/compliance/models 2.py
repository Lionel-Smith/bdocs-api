"""
ACA Compliance Reporting Models - Standards tracking and audit management for BDOCS.

This module handles ACA (American Correctional Association) compliance standards,
audits, and findings for BDOCS facilities.

Reference: ACA Performance-Based Standards for Adult Correctional Institutions

Three core entities:
- ACAStandard: Reference library of compliance standards
- ComplianceAudit: Audit records (self-assessment, mock, official)
- AuditFinding: Individual standard findings within an audit
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Date, DateTime, Integer, Boolean, Text, Numeric, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, AuditMixin
from src.common.enums import (
    ACACategory, AuditType, AuditStatus, ComplianceStatus
)


class ACAStandard(AsyncBase, UUIDMixin, AuditMixin):
    """
    ACA Standard reference record.

    Contains the standard requirements from ACA's Performance-Based
    Standards manual. Standards are numbered like '4-4001'.

    These records are typically seeded and rarely modified.
    """
    __tablename__ = 'aca_standards'

    # Standard identification
    standard_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="ACA standard number (e.g., '4-4001')"
    )

    # Classification
    category: Mapped[ACACategory] = mapped_column(
        ENUM(ACACategory, name='aca_category_enum', create_type=False),
        nullable=False
    )

    # Description
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Brief title of the standard"
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full description of requirements"
    )

    # Requirements
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Mandatory standards must be met for accreditation"
    )

    # Evidence documentation needed
    evidence_required: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {type, description} for required evidence"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_aca_standards_category', 'category'),
        Index('ix_aca_standards_mandatory', 'is_mandatory'),
    )

    # Relationships
    findings = relationship(
        'AuditFinding',
        back_populates='standard',
        lazy='selectin'
    )

    def __repr__(self) -> str:
        return f"<ACAStandard {self.standard_number}: {self.title[:50]}>"


class ComplianceAudit(AsyncBase, UUIDMixin, AuditMixin):
    """
    Compliance audit record.

    Tracks audit events from self-assessments to official ACA audits.
    Contains overall score and links to individual findings.
    """
    __tablename__ = 'compliance_audits'

    # Audit details
    audit_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    auditor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of auditor or audit team lead"
    )

    # Audit type
    audit_type: Mapped[AuditType] = mapped_column(
        ENUM(AuditType, name='audit_type_enum', create_type=False),
        nullable=False
    )

    # Status
    status: Mapped[AuditStatus] = mapped_column(
        ENUM(AuditStatus, name='audit_status_enum', create_type=False),
        nullable=False,
        default=AuditStatus.SCHEDULED
    )

    # Results
    overall_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Compliance percentage (0-100)"
    )

    findings_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Executive summary of audit findings"
    )

    corrective_actions_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of corrective actions identified"
    )

    # Next audit
    next_audit_date: Mapped[Optional[date]] = mapped_column(
        Date,
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
        Index('ix_compliance_audits_date', 'audit_date'),
        Index('ix_compliance_audits_type', 'audit_type'),
        Index('ix_compliance_audits_status', 'status'),
    )

    # Relationships
    creator = relationship(
        'User',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    findings = relationship(
        'AuditFinding',
        back_populates='audit',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<ComplianceAudit {self.audit_date} {self.audit_type.value} [{self.status.value}]>"


class AuditFinding(AsyncBase, UUIDMixin, AuditMixin):
    """
    Individual audit finding for a specific standard.

    Links an audit to a standard with compliance status and
    any required corrective actions.
    """
    __tablename__ = 'audit_findings'

    # References
    audit_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('compliance_audits.id', ondelete='CASCADE'),
        nullable=False
    )

    standard_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('aca_standards.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Compliance status
    compliance_status: Mapped[ComplianceStatus] = mapped_column(
        ENUM(ComplianceStatus, name='compliance_status_enum', create_type=False),
        nullable=False
    )

    # Evidence
    evidence_provided: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of evidence reviewed"
    )

    # Findings
    finding_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Auditor notes and observations"
    )

    # Corrective action (if non-compliant or partial)
    corrective_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Required corrective action"
    )

    corrective_action_due: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Due date for corrective action"
    )

    corrective_action_completed: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date corrective action was completed"
    )

    # Verification
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Staff who verified corrective action completion"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_audit_findings_audit', 'audit_id'),
        Index('ix_audit_findings_standard', 'standard_id'),
        Index('ix_audit_findings_status', 'compliance_status'),
        Index('ix_audit_findings_due', 'corrective_action_due'),
        # Partial index for overdue corrective actions
        Index(
            'ix_audit_findings_overdue',
            'corrective_action_due', 'corrective_action_completed',
            postgresql_where='corrective_action_due IS NOT NULL AND corrective_action_completed IS NULL'
        ),
    )

    # Relationships
    audit = relationship(
        'ComplianceAudit',
        back_populates='findings',
        lazy='selectin'
    )

    standard = relationship(
        'ACAStandard',
        back_populates='findings',
        lazy='selectin'
    )

    verifier = relationship(
        'User',
        foreign_keys=[verified_by],
        lazy='selectin'
    )

    @property
    def is_overdue(self) -> bool:
        """Check if corrective action is overdue."""
        if not self.corrective_action_due:
            return False
        if self.corrective_action_completed:
            return False
        return date.today() > self.corrective_action_due

    @property
    def requires_corrective_action(self) -> bool:
        """Check if finding requires corrective action."""
        return self.compliance_status in [
            ComplianceStatus.NON_COMPLIANT,
            ComplianceStatus.PARTIAL
        ]

    def __repr__(self) -> str:
        return f"<AuditFinding {self.standard_id} [{self.compliance_status.value}]>"
