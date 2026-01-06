"""
Reentry Planning Models - Preparing inmates for successful release.

Reentry planning is critical for reducing recidivism. This module tracks:
- Comprehensive release preparation plans
- Checklist items across multiple domains
- External service referrals

Three core entities:
- ReentryPlan: Master plan with housing, employment, documentation status
- ReentryChecklist: Specific items to complete before release
- ReentryReferral: Referrals to external support services

Key Bahamas-specific elements:
- NIB (National Insurance Board) card requirement
- Local housing programme references
- Family-centric reintegration focus
"""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
import uuid

from sqlalchemy import String, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import PlanStatus, HousingPlan, ChecklistType, ServiceType, ReferralStatus


class ReentryPlan(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Master reentry/release preparation plan for an inmate.

    Only one active plan (non-COMPLETED) per inmate enforced by partial unique index.

    Workflow: DRAFT → IN_PROGRESS → READY → COMPLETED

    Readiness is calculated based on checklist completion percentage.
    A plan should reach READY status when all critical items are complete.
    """
    __tablename__ = 'reentry_plans'

    # Foreign key to inmate
    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Expected release date
    expected_release_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Projected release date"
    )

    # Plan status
    status: Mapped[str] = mapped_column(
        ENUM(
            'DRAFT', 'IN_PROGRESS', 'READY', 'COMPLETED',
            name='plan_status_enum',
            create_type=False
        ),
        nullable=False,
        default=PlanStatus.DRAFT.value
    )

    # Housing plan
    housing_plan: Mapped[str] = mapped_column(
        ENUM(
            'FAMILY', 'SHELTER', 'TRANSITIONAL', 'INDEPENDENT', 'UNKNOWN',
            name='housing_plan_enum',
            create_type=False
        ),
        nullable=False,
        default=HousingPlan.UNKNOWN.value
    )

    housing_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Post-release housing address"
    )

    # Employment plan
    employment_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Employment or job search plan"
    )

    # Documentation status (Bahamas-specific)
    has_id_documents: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Has valid government-issued ID"
    )

    has_birth_certificate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Has birth certificate"
    )

    has_nib_card: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Has National Insurance Board card (required for employment)"
    )

    # Transportation
    transportation_arranged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Transportation from facility arranged"
    )

    # Family contact
    family_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Primary family contact for release"
    )

    family_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Family contact phone (242) XXX-XXXX"
    )

    # Flexible JSONB fields
    support_services: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Planned support services as JSON array"
    )

    risk_factors: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Identified risk factors as JSON array"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional planning notes"
    )

    # Created and approved by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who created the plan"
    )

    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who approved the plan as READY"
    )

    approval_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date plan was approved as READY"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_reentry_plans_inmate', 'inmate_id'),
        Index('ix_reentry_plans_status', 'status'),
        Index('ix_reentry_plans_release_date', 'expected_release_date'),
        # Partial unique index: one active plan per inmate
        Index(
            'ix_reentry_plans_unique_active',
            'inmate_id',
            unique=True,
            postgresql_where="status NOT IN ('COMPLETED') AND is_deleted = false"
        ),
        # Partial index for upcoming releases
        Index(
            'ix_reentry_plans_upcoming',
            'expected_release_date', 'status',
            postgresql_where="status IN ('DRAFT', 'IN_PROGRESS', 'READY') AND is_deleted = false"
        ),
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='reentry_plans', lazy='selectin')
    checklist_items = relationship(
        'ReentryChecklist',
        back_populates='plan',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='ReentryChecklist.item_type'
    )
    referrals = relationship(
        'ReentryReferral',
        back_populates='plan',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='ReentryReferral.referral_date.desc()'
    )

    @property
    def days_until_release(self) -> int:
        """Calculate days until expected release."""
        delta = self.expected_release_date - date.today()
        return delta.days

    @property
    def is_overdue(self) -> bool:
        """Check if release date has passed without completion."""
        return (
            self.expected_release_date < date.today() and
            self.status != PlanStatus.COMPLETED.value
        )

    def __repr__(self) -> str:
        return f"<ReentryPlan {self.inmate_id} - {self.status} (release: {self.expected_release_date})>"


class ReentryChecklist(AsyncBase, UUIDMixin, AuditMixin):
    """
    Individual checklist item for reentry preparation.

    Items are categorized by type to ensure comprehensive preparation
    across all domains: documentation, housing, employment, etc.

    No soft delete - checklist items are permanent records.
    """
    __tablename__ = 'reentry_checklists'

    # Foreign key to plan
    reentry_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('reentry_plans.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Item type/category
    item_type: Mapped[str] = mapped_column(
        ENUM(
            'DOCUMENTATION', 'HOUSING', 'EMPLOYMENT', 'HEALTHCARE',
            'FAMILY', 'FINANCIAL', 'SUPERVISION',
            name='checklist_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Description of the item
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Specific task description"
    )

    # Completion status
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    completed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date item was completed"
    )

    completed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who marked item complete"
    )

    # Due date
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Target completion date"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about this item"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_reentry_checklists_plan', 'reentry_plan_id'),
        Index('ix_reentry_checklists_type', 'item_type'),
        Index('ix_reentry_checklists_completed', 'is_completed'),
        # Partial index for incomplete items
        Index(
            'ix_reentry_checklists_incomplete',
            'reentry_plan_id', 'due_date',
            postgresql_where="is_completed = false"
        ),
    )

    # Relationships
    plan = relationship('ReentryPlan', back_populates='checklist_items', lazy='selectin')

    @property
    def is_overdue(self) -> bool:
        """Check if incomplete item is past due date."""
        if self.is_completed or not self.due_date:
            return False
        return self.due_date < date.today()

    def __repr__(self) -> str:
        status = "✓" if self.is_completed else "○"
        return f"<ReentryChecklist [{status}] {self.item_type}: {self.description[:30]}>"


class ReentryReferral(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Referral to external support service for reentry support.

    Tracks referrals to community organizations, government programmes,
    and other support services that aid successful reintegration.

    Workflow: PENDING → ACCEPTED → IN_PROGRESS → COMPLETED
    Alternative: DECLINED
    """
    __tablename__ = 'reentry_referrals'

    # Foreign keys
    reentry_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('reentry_plans.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    inmate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Service type
    service_type: Mapped[str] = mapped_column(
        ENUM(
            'HOUSING_ASSISTANCE', 'JOB_PLACEMENT', 'SUBSTANCE_ABUSE',
            'MENTAL_HEALTH', 'FAMILY_COUNSELING', 'FINANCIAL_AID',
            'TRANSPORTATION', 'LEGAL_AID',
            name='service_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Provider information
    provider_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of service provider organization"
    )

    provider_contact: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Provider contact (phone/email)"
    )

    # Referral details
    referral_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date referral was made"
    )

    # Status
    status: Mapped[str] = mapped_column(
        ENUM(
            'PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'DECLINED',
            name='referral_status_enum',
            create_type=False
        ),
        nullable=False,
        default=ReferralStatus.PENDING.value
    )

    # Appointment
    appointment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled appointment date/time"
    )

    # Outcome
    outcome: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Outcome or result of referral"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about referral"
    )

    # Created by
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who created referral"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_reentry_referrals_plan', 'reentry_plan_id'),
        Index('ix_reentry_referrals_inmate', 'inmate_id'),
        Index('ix_reentry_referrals_type', 'service_type'),
        Index('ix_reentry_referrals_status', 'status'),
        Index('ix_reentry_referrals_date', 'referral_date'),
        # Partial index for active referrals
        Index(
            'ix_reentry_referrals_active',
            'status',
            postgresql_where="status IN ('PENDING', 'ACCEPTED', 'IN_PROGRESS') AND is_deleted = false"
        ),
    )

    # Relationships
    plan = relationship('ReentryPlan', back_populates='referrals', lazy='selectin')
    inmate = relationship('Inmate', back_populates='reentry_referrals', lazy='selectin')

    def __repr__(self) -> str:
        return f"<ReentryReferral {self.service_type} -> {self.provider_name} ({self.status})>"
