"""add_integration_tables

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m9
Create Date: 2026-01-05

Creates external_system_logs table for tracking all external API integrations.
Creates request_type_enum and integration_status_enum.

Phase 4: External Integration - RBPF connectivity stub.

NOTE: This is for the STUB implementation. The table structure supports
real integration when RBPF API becomes available.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'o5j6k7l8m9n0'
down_revision: Union[str, None] = 'n4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create request_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'request_type_enum') THEN
                CREATE TYPE request_type_enum AS ENUM (
                    'INMATE_LOOKUP',
                    'WARRANT_CHECK',
                    'CRIMINAL_HISTORY',
                    'BOOKING_NOTIFICATION',
                    'RELEASE_NOTIFICATION'
                );
            END IF;
        END$$;
    """)

    # Create integration_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integration_status_enum') THEN
                CREATE TYPE integration_status_enum AS ENUM (
                    'PENDING',
                    'SUCCESS',
                    'FAILED',
                    'TIMEOUT'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create external_system_logs table
    # ========================================================================
    op.create_table(
        'external_system_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # System identification
        sa.Column('system_name', sa.String(50), nullable=False,
                  comment="Name of external system (e.g., 'RBPF', 'COURTS')"),
        # Request type
        sa.Column('request_type', postgresql.ENUM(
            'INMATE_LOOKUP', 'WARRANT_CHECK', 'CRIMINAL_HISTORY',
            'BOOKING_NOTIFICATION', 'RELEASE_NOTIFICATION',
            name='request_type_enum', create_type=False
        ), nullable=False, comment="Type of integration request"),
        # Request/Response payloads
        sa.Column('request_payload', postgresql.JSONB, nullable=False,
                  comment="Request data sent to external system"),
        sa.Column('response_payload', postgresql.JSONB, nullable=True,
                  comment="Response data received from external system"),
        # Status tracking
        sa.Column('status', postgresql.ENUM(
            'PENDING', 'SUCCESS', 'FAILED', 'TIMEOUT',
            name='integration_status_enum', create_type=False
        ), nullable=False, server_default='PENDING',
                  comment="Current status of the request"),
        # Timing
        sa.Column('request_time', sa.DateTime(timezone=True), nullable=False,
                  comment="When the request was initiated"),
        sa.Column('response_time', sa.DateTime(timezone=True), nullable=True,
                  comment="When the response was received"),
        # Error tracking
        sa.Column('error_message', sa.Text, nullable=True,
                  comment="Error message if request failed"),
        # Correlation
        sa.Column('correlation_id', postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID for tracking related requests"),
        # Who initiated
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False,
                  comment="Staff member who initiated the request"),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for external_system_logs
    op.create_index('ix_ext_sys_logs_system', 'external_system_logs', ['system_name'])
    op.create_index('ix_ext_sys_logs_request_type', 'external_system_logs', ['request_type'])
    op.create_index('ix_ext_sys_logs_status', 'external_system_logs', ['status'])
    op.create_index('ix_ext_sys_logs_request_time', 'external_system_logs', ['request_time'])
    op.create_index('ix_ext_sys_logs_correlation', 'external_system_logs', ['correlation_id'])
    op.create_index('ix_ext_sys_logs_initiated_by', 'external_system_logs', ['initiated_by'])

    # Composite index for common query pattern (system + time range)
    op.create_index(
        'ix_ext_sys_logs_system_time',
        'external_system_logs',
        ['system_name', 'request_time']
    )

    # Partial index for pending requests (for monitoring)
    op.create_index(
        'ix_ext_sys_logs_pending',
        'external_system_logs',
        ['system_name', 'request_time'],
        postgresql_where=sa.text("status = 'PENDING'")
    )

    # Partial index for failed/timeout requests (for alerting)
    op.create_index(
        'ix_ext_sys_logs_failed',
        'external_system_logs',
        ['system_name', 'request_time'],
        postgresql_where=sa.text("status IN ('FAILED', 'TIMEOUT')")
    )

    # ========================================================================
    # Attach audit trigger
    # ========================================================================
    op.execute("""
        DROP TRIGGER IF EXISTS external_system_logs_audit_trigger ON external_system_logs;
        CREATE TRIGGER external_system_logs_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON external_system_logs
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)


def downgrade() -> None:
    # Drop audit trigger
    op.execute("DROP TRIGGER IF EXISTS external_system_logs_audit_trigger ON external_system_logs")

    # Drop indexes
    op.drop_index('ix_ext_sys_logs_failed', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_pending', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_system_time', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_initiated_by', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_correlation', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_request_time', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_status', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_request_type', 'external_system_logs')
    op.drop_index('ix_ext_sys_logs_system', 'external_system_logs')

    # Drop table
    op.drop_table('external_system_logs')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS integration_status_enum")
    op.execute("DROP TYPE IF EXISTS request_type_enum")
