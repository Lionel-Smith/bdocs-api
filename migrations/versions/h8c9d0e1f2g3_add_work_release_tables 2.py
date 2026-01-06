"""add_work_release_tables

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2026-01-05

Creates work_release_employers, work_release_assignments, and work_release_logs tables.
Creates work_release_status_enum and log_status_enum.

Work release allows MINIMUM security inmates to work for approved employers.
CRITICAL: Only MINIMUM security level inmates are eligible.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h8c9d0e1f2g3'
down_revision: Union[str, None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create work_release_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'work_release_status_enum') THEN
                CREATE TYPE work_release_status_enum AS ENUM (
                    'PENDING_APPROVAL',
                    'APPROVED',
                    'ACTIVE',
                    'SUSPENDED',
                    'COMPLETED',
                    'TERMINATED'
                );
            END IF;
        END$$;
    """)

    # Create log_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'log_status_enum') THEN
                CREATE TYPE log_status_enum AS ENUM (
                    'DEPARTED',
                    'RETURNED_ON_TIME',
                    'RETURNED_LATE',
                    'DID_NOT_RETURN',
                    'EXCUSED'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create work_release_employers table
    # ========================================================================
    op.create_table(
        'work_release_employers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Business information
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('business_type', sa.String(100), nullable=False),
        # Contact information
        sa.Column('contact_name', sa.String(200), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=False),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text, nullable=False),
        # Approval status
        sa.Column('is_approved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('approval_date', sa.Date, nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        # MOU (Memorandum of Understanding)
        sa.Column('mou_signed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('mou_expiry_date', sa.Date, nullable=True),
        # Notes and status
        sa.Column('notes', sa.Text, nullable=True),
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

    # Indexes for work_release_employers
    op.create_index('ix_work_release_employers_name', 'work_release_employers', ['name'])
    op.create_index('ix_work_release_employers_approved', 'work_release_employers', ['is_approved'])
    op.create_index('ix_work_release_employers_active', 'work_release_employers', ['is_active'])
    op.create_index('ix_work_release_employers_mou', 'work_release_employers', ['mou_signed', 'mou_expiry_date'])

    # ========================================================================
    # Create work_release_assignments table
    # ========================================================================
    op.create_table(
        'work_release_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('work_release_employers.id', ondelete='RESTRICT'), nullable=False),
        # Position details
        sa.Column('position_title', sa.String(200), nullable=False),
        # Assignment dates
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM(
            'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'SUSPENDED', 'COMPLETED', 'TERMINATED',
            name='work_release_status_enum', create_type=False
        ), nullable=False, server_default='PENDING_APPROVAL'),
        # Compensation
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        # Schedule (JSONB for flexibility)
        sa.Column('work_schedule', postgresql.JSONB, nullable=True),
        # Supervisor at workplace
        sa.Column('supervisor_name', sa.String(200), nullable=False),
        sa.Column('supervisor_phone', sa.String(20), nullable=False),
        # Approval
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_date', sa.Date, nullable=True),
        # Termination
        sa.Column('termination_reason', sa.Text, nullable=True),
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

    # Indexes for work_release_assignments
    op.create_index('ix_work_release_assignments_inmate', 'work_release_assignments', ['inmate_id'])
    op.create_index('ix_work_release_assignments_employer', 'work_release_assignments', ['employer_id'])
    op.create_index('ix_work_release_assignments_status', 'work_release_assignments', ['status'])
    op.create_index('ix_work_release_assignments_dates', 'work_release_assignments', ['start_date', 'end_date'])
    # Partial index for active assignments
    op.create_index(
        'ix_work_release_assignments_active',
        'work_release_assignments',
        ['status'],
        postgresql_where=sa.text("status = 'ACTIVE' AND is_deleted = false")
    )

    # ========================================================================
    # Create work_release_logs table
    # ========================================================================
    op.create_table(
        'work_release_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key to assignment
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('work_release_assignments.id', ondelete='CASCADE'), nullable=False),
        # Log date
        sa.Column('log_date', sa.Date, nullable=False),
        # Times
        sa.Column('departure_time', sa.Time, nullable=False),
        sa.Column('expected_return_time', sa.Time, nullable=False),
        sa.Column('actual_return_time', sa.Time, nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM(
            'DEPARTED', 'RETURNED_ON_TIME', 'RETURNED_LATE', 'DID_NOT_RETURN', 'EXCUSED',
            name='log_status_enum', create_type=False
        ), nullable=False, server_default='DEPARTED'),
        # Verification
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Audit fields (no soft delete - logs are permanent security records)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for work_release_logs
    op.create_index('ix_work_release_logs_assignment', 'work_release_logs', ['assignment_id'])
    op.create_index('ix_work_release_logs_date', 'work_release_logs', ['log_date'])
    op.create_index('ix_work_release_logs_status', 'work_release_logs', ['status'])
    # Partial index for unresolved logs (departed but not returned)
    op.create_index(
        'ix_work_release_logs_unresolved',
        'work_release_logs',
        ['status', 'log_date'],
        postgresql_where=sa.text("status = 'DEPARTED'")
    )
    # Unique: one log per assignment per day
    op.create_index(
        'ix_work_release_logs_unique_day',
        'work_release_logs',
        ['assignment_id', 'log_date'],
        unique=True
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['work_release_employers', 'work_release_assignments', 'work_release_logs']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['work_release_logs', 'work_release_assignments', 'work_release_employers']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for work_release_logs
    op.drop_index('ix_work_release_logs_unique_day', 'work_release_logs')
    op.drop_index('ix_work_release_logs_unresolved', 'work_release_logs')
    op.drop_index('ix_work_release_logs_status', 'work_release_logs')
    op.drop_index('ix_work_release_logs_date', 'work_release_logs')
    op.drop_index('ix_work_release_logs_assignment', 'work_release_logs')

    # Drop indexes for work_release_assignments
    op.drop_index('ix_work_release_assignments_active', 'work_release_assignments')
    op.drop_index('ix_work_release_assignments_dates', 'work_release_assignments')
    op.drop_index('ix_work_release_assignments_status', 'work_release_assignments')
    op.drop_index('ix_work_release_assignments_employer', 'work_release_assignments')
    op.drop_index('ix_work_release_assignments_inmate', 'work_release_assignments')

    # Drop indexes for work_release_employers
    op.drop_index('ix_work_release_employers_mou', 'work_release_employers')
    op.drop_index('ix_work_release_employers_active', 'work_release_employers')
    op.drop_index('ix_work_release_employers_approved', 'work_release_employers')
    op.drop_index('ix_work_release_employers_name', 'work_release_employers')

    # Drop tables
    op.drop_table('work_release_logs')
    op.drop_table('work_release_assignments')
    op.drop_table('work_release_employers')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS log_status_enum")
    op.execute("DROP TYPE IF EXISTS work_release_status_enum")
