"""add_reentry_planning_tables

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2026-01-05

Creates reentry_plans, reentry_checklists, and reentry_referrals tables.
Creates plan_status_enum, housing_plan_enum, checklist_type_enum,
service_type_enum, and referral_status_enum.

Reentry planning is critical for reducing recidivism through comprehensive
release preparation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i9d0e1f2g3h4'
down_revision: Union[str, None] = 'h8c9d0e1f2g3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create plan_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plan_status_enum') THEN
                CREATE TYPE plan_status_enum AS ENUM (
                    'DRAFT',
                    'IN_PROGRESS',
                    'READY',
                    'COMPLETED'
                );
            END IF;
        END$$;
    """)

    # Create housing_plan_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'housing_plan_enum') THEN
                CREATE TYPE housing_plan_enum AS ENUM (
                    'FAMILY',
                    'SHELTER',
                    'TRANSITIONAL',
                    'INDEPENDENT',
                    'UNKNOWN'
                );
            END IF;
        END$$;
    """)

    # Create checklist_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_type_enum') THEN
                CREATE TYPE checklist_type_enum AS ENUM (
                    'DOCUMENTATION',
                    'HOUSING',
                    'EMPLOYMENT',
                    'HEALTHCARE',
                    'FAMILY',
                    'FINANCIAL',
                    'SUPERVISION'
                );
            END IF;
        END$$;
    """)

    # Create service_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_type_enum') THEN
                CREATE TYPE service_type_enum AS ENUM (
                    'HOUSING_ASSISTANCE',
                    'JOB_PLACEMENT',
                    'SUBSTANCE_ABUSE',
                    'MENTAL_HEALTH',
                    'FAMILY_COUNSELING',
                    'FINANCIAL_AID',
                    'TRANSPORTATION',
                    'LEGAL_AID'
                );
            END IF;
        END$$;
    """)

    # Create referral_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'referral_status_enum') THEN
                CREATE TYPE referral_status_enum AS ENUM (
                    'PENDING',
                    'ACCEPTED',
                    'IN_PROGRESS',
                    'COMPLETED',
                    'DECLINED'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create reentry_plans table
    # ========================================================================
    op.create_table(
        'reentry_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Expected release
        sa.Column('expected_release_date', sa.Date, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM(
            'DRAFT', 'IN_PROGRESS', 'READY', 'COMPLETED',
            name='plan_status_enum', create_type=False
        ), nullable=False, server_default='DRAFT'),
        # Housing
        sa.Column('housing_plan', postgresql.ENUM(
            'FAMILY', 'SHELTER', 'TRANSITIONAL', 'INDEPENDENT', 'UNKNOWN',
            name='housing_plan_enum', create_type=False
        ), nullable=False, server_default='UNKNOWN'),
        sa.Column('housing_address', sa.Text, nullable=True),
        # Employment
        sa.Column('employment_plan', sa.Text, nullable=True),
        # Documentation (Bahamas-specific)
        sa.Column('has_id_documents', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('has_birth_certificate', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('has_nib_card', sa.Boolean, nullable=False, server_default='false'),
        # Transportation
        sa.Column('transportation_arranged', sa.Boolean, nullable=False, server_default='false'),
        # Family contact
        sa.Column('family_contact_name', sa.String(200), nullable=True),
        sa.Column('family_contact_phone', sa.String(20), nullable=True),
        # JSONB fields
        sa.Column('support_services', postgresql.JSONB, nullable=True),
        sa.Column('risk_factors', postgresql.JSONB, nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Created and approved by
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_date', sa.Date, nullable=True),
        # Soft delete fields
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(100), nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for reentry_plans
    op.create_index('ix_reentry_plans_inmate', 'reentry_plans', ['inmate_id'])
    op.create_index('ix_reentry_plans_status', 'reentry_plans', ['status'])
    op.create_index('ix_reentry_plans_release_date', 'reentry_plans', ['expected_release_date'])
    # Partial unique index: one active plan per inmate
    op.create_index(
        'ix_reentry_plans_unique_active',
        'reentry_plans',
        ['inmate_id'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('COMPLETED') AND is_deleted = false")
    )
    # Partial index for upcoming releases
    op.create_index(
        'ix_reentry_plans_upcoming',
        'reentry_plans',
        ['expected_release_date', 'status'],
        postgresql_where=sa.text("status IN ('DRAFT', 'IN_PROGRESS', 'READY') AND is_deleted = false")
    )

    # ========================================================================
    # Create reentry_checklists table
    # ========================================================================
    op.create_table(
        'reentry_checklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key
        sa.Column('reentry_plan_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('reentry_plans.id', ondelete='CASCADE'), nullable=False),
        # Item type
        sa.Column('item_type', postgresql.ENUM(
            'DOCUMENTATION', 'HOUSING', 'EMPLOYMENT', 'HEALTHCARE',
            'FAMILY', 'FINANCIAL', 'SUPERVISION',
            name='checklist_type_enum', create_type=False
        ), nullable=False),
        # Description
        sa.Column('description', sa.Text, nullable=False),
        # Completion
        sa.Column('is_completed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('completed_date', sa.Date, nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Due date
        sa.Column('due_date', sa.Date, nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Audit fields (no soft delete - checklist items are permanent)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for reentry_checklists
    op.create_index('ix_reentry_checklists_plan', 'reentry_checklists', ['reentry_plan_id'])
    op.create_index('ix_reentry_checklists_type', 'reentry_checklists', ['item_type'])
    op.create_index('ix_reentry_checklists_completed', 'reentry_checklists', ['is_completed'])
    # Partial index for incomplete items
    op.create_index(
        'ix_reentry_checklists_incomplete',
        'reentry_checklists',
        ['reentry_plan_id', 'due_date'],
        postgresql_where=sa.text("is_completed = false")
    )

    # ========================================================================
    # Create reentry_referrals table
    # ========================================================================
    op.create_table(
        'reentry_referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('reentry_plan_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('reentry_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Service type
        sa.Column('service_type', postgresql.ENUM(
            'HOUSING_ASSISTANCE', 'JOB_PLACEMENT', 'SUBSTANCE_ABUSE',
            'MENTAL_HEALTH', 'FAMILY_COUNSELING', 'FINANCIAL_AID',
            'TRANSPORTATION', 'LEGAL_AID',
            name='service_type_enum', create_type=False
        ), nullable=False),
        # Provider
        sa.Column('provider_name', sa.String(200), nullable=False),
        sa.Column('provider_contact', sa.String(200), nullable=False),
        # Referral details
        sa.Column('referral_date', sa.Date, nullable=False),
        sa.Column('status', postgresql.ENUM(
            'PENDING', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'DECLINED',
            name='referral_status_enum', create_type=False
        ), nullable=False, server_default='PENDING'),
        # Appointment
        sa.Column('appointment_date', sa.DateTime(timezone=True), nullable=True),
        # Outcome
        sa.Column('outcome', sa.Text, nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Soft delete fields
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(100), nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for reentry_referrals
    op.create_index('ix_reentry_referrals_plan', 'reentry_referrals', ['reentry_plan_id'])
    op.create_index('ix_reentry_referrals_inmate', 'reentry_referrals', ['inmate_id'])
    op.create_index('ix_reentry_referrals_type', 'reentry_referrals', ['service_type'])
    op.create_index('ix_reentry_referrals_status', 'reentry_referrals', ['status'])
    op.create_index('ix_reentry_referrals_date', 'reentry_referrals', ['referral_date'])
    # Partial index for active referrals
    op.create_index(
        'ix_reentry_referrals_active',
        'reentry_referrals',
        ['status'],
        postgresql_where=sa.text("status IN ('PENDING', 'ACCEPTED', 'IN_PROGRESS') AND is_deleted = false")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['reentry_plans', 'reentry_checklists', 'reentry_referrals']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['reentry_referrals', 'reentry_checklists', 'reentry_plans']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for reentry_referrals
    op.drop_index('ix_reentry_referrals_active', 'reentry_referrals')
    op.drop_index('ix_reentry_referrals_date', 'reentry_referrals')
    op.drop_index('ix_reentry_referrals_status', 'reentry_referrals')
    op.drop_index('ix_reentry_referrals_type', 'reentry_referrals')
    op.drop_index('ix_reentry_referrals_inmate', 'reentry_referrals')
    op.drop_index('ix_reentry_referrals_plan', 'reentry_referrals')

    # Drop indexes for reentry_checklists
    op.drop_index('ix_reentry_checklists_incomplete', 'reentry_checklists')
    op.drop_index('ix_reentry_checklists_completed', 'reentry_checklists')
    op.drop_index('ix_reentry_checklists_type', 'reentry_checklists')
    op.drop_index('ix_reentry_checklists_plan', 'reentry_checklists')

    # Drop indexes for reentry_plans
    op.drop_index('ix_reentry_plans_upcoming', 'reentry_plans')
    op.drop_index('ix_reentry_plans_unique_active', 'reentry_plans')
    op.drop_index('ix_reentry_plans_release_date', 'reentry_plans')
    op.drop_index('ix_reentry_plans_status', 'reentry_plans')
    op.drop_index('ix_reentry_plans_inmate', 'reentry_plans')

    # Drop tables
    op.drop_table('reentry_referrals')
    op.drop_table('reentry_checklists')
    op.drop_table('reentry_plans')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS referral_status_enum")
    op.execute("DROP TYPE IF EXISTS service_type_enum")
    op.execute("DROP TYPE IF EXISTS checklist_type_enum")
    op.execute("DROP TYPE IF EXISTS housing_plan_enum")
    op.execute("DROP TYPE IF EXISTS plan_status_enum")
