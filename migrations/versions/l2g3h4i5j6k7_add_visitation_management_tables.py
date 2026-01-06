"""add_visitation_management_tables

Revision ID: l2g3h4i5j6k7
Revises: k1f2g3h4i5j6
Create Date: 2026-01-05

Creates approved_visitors, visit_schedules, and visit_logs tables.
Creates relationship_enum, id_type_enum, check_status_enum,
visit_type_enum, and visit_status_enum.

Phase 3: Operations & Security - Visitation Management.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l2g3h4i5j6k7'
down_revision: Union[str, None] = 'k1f2g3h4i5j6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create relationship_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relationship_enum') THEN
                CREATE TYPE relationship_enum AS ENUM (
                    'SPOUSE',
                    'PARENT',
                    'CHILD',
                    'SIBLING',
                    'GRANDPARENT',
                    'LEGAL_COUNSEL',
                    'CLERGY',
                    'OTHER'
                );
            END IF;
        END$$;
    """)

    # Create id_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'id_type_enum') THEN
                CREATE TYPE id_type_enum AS ENUM (
                    'PASSPORT',
                    'DRIVERS_LICENSE',
                    'NIB_CARD',
                    'VOTER_CARD'
                );
            END IF;
        END$$;
    """)

    # Create check_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'check_status_enum') THEN
                CREATE TYPE check_status_enum AS ENUM (
                    'PENDING',
                    'APPROVED',
                    'DENIED',
                    'EXPIRED'
                );
            END IF;
        END$$;
    """)

    # Create visit_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visit_type_enum') THEN
                CREATE TYPE visit_type_enum AS ENUM (
                    'GENERAL',
                    'LEGAL',
                    'CLERGY',
                    'FAMILY_SPECIAL',
                    'VIDEO'
                );
            END IF;
        END$$;
    """)

    # Create visit_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visit_status_enum') THEN
                CREATE TYPE visit_status_enum AS ENUM (
                    'SCHEDULED',
                    'CHECKED_IN',
                    'IN_PROGRESS',
                    'COMPLETED',
                    'CANCELLED',
                    'NO_SHOW'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create approved_visitors table
    # ========================================================================
    op.create_table(
        'approved_visitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Link to inmate
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Personal information
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('relationship', postgresql.ENUM(
            'SPOUSE', 'PARENT', 'CHILD', 'SIBLING', 'GRANDPARENT',
            'LEGAL_COUNSEL', 'CLERGY', 'OTHER',
            name='relationship_enum', create_type=False
        ), nullable=False),
        # Contact
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        # Identification
        sa.Column('id_type', postgresql.ENUM(
            'PASSPORT', 'DRIVERS_LICENSE', 'NIB_CARD', 'VOTER_CARD',
            name='id_type_enum', create_type=False
        ), nullable=False),
        sa.Column('id_number', sa.String(50), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('photo_url', sa.String(500), nullable=True),
        # Background check
        sa.Column('background_check_date', sa.Date, nullable=True),
        sa.Column('background_check_status', postgresql.ENUM(
            'PENDING', 'APPROVED', 'DENIED', 'EXPIRED',
            name='check_status_enum', create_type=False
        ), nullable=False, server_default='PENDING'),
        # Approval
        sa.Column('is_approved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('approval_date', sa.Date, nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('denied_reason', sa.Text, nullable=True),
        # Active status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
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

    # Indexes for approved_visitors
    op.create_index('ix_approved_visitors_inmate', 'approved_visitors', ['inmate_id'])
    op.create_index('ix_approved_visitors_name', 'approved_visitors', ['last_name', 'first_name'])
    op.create_index('ix_approved_visitors_status', 'approved_visitors', ['background_check_status'])
    op.create_index('ix_approved_visitors_approved', 'approved_visitors', ['is_approved'])
    op.create_index('ix_approved_visitors_active', 'approved_visitors', ['is_active'])
    # Partial unique index for visitor per inmate per ID
    op.create_index(
        'ix_approved_visitors_unique',
        'approved_visitors',
        ['inmate_id', 'id_type', 'id_number'],
        unique=True,
        postgresql_where=sa.text("is_deleted = false")
    )

    # ========================================================================
    # Create visit_schedules table
    # ========================================================================
    op.create_table(
        'visit_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # References
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('visitor_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('approved_visitors.id', ondelete='CASCADE'), nullable=False),
        # Schedule
        sa.Column('scheduled_date', sa.Date, nullable=False),
        sa.Column('scheduled_time', sa.Time, nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=False, server_default='60'),
        # Visit type
        sa.Column('visit_type', postgresql.ENUM(
            'GENERAL', 'LEGAL', 'CLERGY', 'FAMILY_SPECIAL', 'VIDEO',
            name='visit_type_enum', create_type=False
        ), nullable=False, server_default='GENERAL'),
        # Status
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW',
            name='visit_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Location
        sa.Column('location', sa.String(100), nullable=False, server_default='Main Visitation Room'),
        # Actual times
        sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True),
        # Cancellation
        sa.Column('cancelled_reason', sa.Text, nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for visit_schedules
    op.create_index('ix_visit_schedules_inmate', 'visit_schedules', ['inmate_id'])
    op.create_index('ix_visit_schedules_visitor', 'visit_schedules', ['visitor_id'])
    op.create_index('ix_visit_schedules_date', 'visit_schedules', ['scheduled_date'])
    op.create_index('ix_visit_schedules_status', 'visit_schedules', ['status'])
    op.create_index('ix_visit_schedules_type', 'visit_schedules', ['visit_type'])
    op.create_index('ix_visit_schedules_daily', 'visit_schedules',
                    ['scheduled_date', 'scheduled_time', 'status'])

    # ========================================================================
    # Create visit_logs table
    # ========================================================================
    op.create_table(
        'visit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Reference to schedule (one-to-one)
        sa.Column('visit_schedule_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('visit_schedules.id', ondelete='CASCADE'),
                  unique=True, nullable=False),
        # Check-in/out times
        sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('checked_out_at', sa.DateTime(timezone=True), nullable=True),
        # Security checks
        sa.Column('visitor_searched', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('items_stored', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('contraband_found', sa.Boolean, nullable=False, server_default='false'),
        # Incident reference
        sa.Column('incident_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('incidents.id', ondelete='SET NULL'), nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Processed by
        sa.Column('processed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for visit_logs
    op.create_index('ix_visit_logs_schedule', 'visit_logs', ['visit_schedule_id'])
    op.create_index('ix_visit_logs_checked_in', 'visit_logs', ['checked_in_at'])
    op.create_index('ix_visit_logs_contraband', 'visit_logs', ['contraband_found'])
    op.create_index('ix_visit_logs_incident', 'visit_logs', ['incident_id'])
    op.create_index('ix_visit_logs_processed_by', 'visit_logs', ['processed_by'])

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['approved_visitors', 'visit_schedules', 'visit_logs']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['visit_logs', 'visit_schedules', 'approved_visitors']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for visit_logs
    op.drop_index('ix_visit_logs_processed_by', 'visit_logs')
    op.drop_index('ix_visit_logs_incident', 'visit_logs')
    op.drop_index('ix_visit_logs_contraband', 'visit_logs')
    op.drop_index('ix_visit_logs_checked_in', 'visit_logs')
    op.drop_index('ix_visit_logs_schedule', 'visit_logs')

    # Drop indexes for visit_schedules
    op.drop_index('ix_visit_schedules_daily', 'visit_schedules')
    op.drop_index('ix_visit_schedules_type', 'visit_schedules')
    op.drop_index('ix_visit_schedules_status', 'visit_schedules')
    op.drop_index('ix_visit_schedules_date', 'visit_schedules')
    op.drop_index('ix_visit_schedules_visitor', 'visit_schedules')
    op.drop_index('ix_visit_schedules_inmate', 'visit_schedules')

    # Drop indexes for approved_visitors
    op.drop_index('ix_approved_visitors_unique', 'approved_visitors')
    op.drop_index('ix_approved_visitors_active', 'approved_visitors')
    op.drop_index('ix_approved_visitors_approved', 'approved_visitors')
    op.drop_index('ix_approved_visitors_status', 'approved_visitors')
    op.drop_index('ix_approved_visitors_name', 'approved_visitors')
    op.drop_index('ix_approved_visitors_inmate', 'approved_visitors')

    # Drop tables
    op.drop_table('visit_logs')
    op.drop_table('visit_schedules')
    op.drop_table('approved_visitors')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS visit_status_enum")
    op.execute("DROP TYPE IF EXISTS visit_type_enum")
    op.execute("DROP TYPE IF EXISTS check_status_enum")
    op.execute("DROP TYPE IF EXISTS id_type_enum")
    op.execute("DROP TYPE IF EXISTS relationship_enum")
