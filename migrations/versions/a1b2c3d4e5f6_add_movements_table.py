"""add_movements_table

Revision ID: a1b2c3d4e5f6
Revises: 33f6e46953af
Create Date: 2026-01-05

Creates movements table for inmate movement tracking.
Adds movement_type_enum and movement_status_enum PostgreSQL types.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '33f6e46953af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================
    op.execute("""
        CREATE TYPE movement_type_enum AS ENUM (
            'INTERNAL_TRANSFER',
            'COURT_TRANSPORT',
            'MEDICAL_TRANSPORT',
            'WORK_RELEASE',
            'TEMPORARY_RELEASE',
            'FURLOUGH',
            'EXTERNAL_APPOINTMENT',
            'RELEASE'
        );
    """)

    op.execute("""
        CREATE TYPE movement_status_enum AS ENUM (
            'SCHEDULED',
            'IN_PROGRESS',
            'COMPLETED',
            'CANCELLED'
        );
    """)

    # ========================================================================
    # Create movements table
    # ========================================================================
    op.create_table(
        'movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign Key to inmates
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Movement type and status (using ENUMs)
        sa.Column('movement_type', postgresql.ENUM(
            'INTERNAL_TRANSFER', 'COURT_TRANSPORT', 'MEDICAL_TRANSPORT',
            'WORK_RELEASE', 'TEMPORARY_RELEASE', 'FURLOUGH',
            'EXTERNAL_APPOINTMENT', 'RELEASE',
            name='movement_type_enum', create_type=False
        ), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED',
            name='movement_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Locations
        sa.Column('from_location', sa.String(200), nullable=False),
        sa.Column('to_location', sa.String(200), nullable=False),
        # Timestamps
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('departure_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('arrival_time', sa.DateTime(timezone=True), nullable=True),
        # Optional foreign keys
        sa.Column('escort_officer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('vehicle_id', sa.String(50), nullable=True),
        sa.Column('court_appearance_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Notes and created_by
        sa.Column('notes', sa.Text, nullable=True),
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

    # ========================================================================
    # Create indexes
    # ========================================================================
    op.create_index('ix_movements_inmate_id', 'movements', ['inmate_id'])
    op.create_index('ix_movements_status', 'movements', ['status'])
    op.create_index('ix_movements_type', 'movements', ['movement_type'])
    op.create_index('ix_movements_scheduled_time', 'movements', ['scheduled_time'])
    op.create_index('ix_movements_active', 'movements', ['inmate_id', 'status'],
                    postgresql_where=sa.text("status IN ('SCHEDULED', 'IN_PROGRESS')"))

    # ========================================================================
    # Attach audit trigger
    # ========================================================================
    op.execute("""
        DROP TRIGGER IF EXISTS movements_audit_trigger ON movements;
        CREATE TRIGGER movements_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON movements
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)


def downgrade() -> None:
    # Drop audit trigger
    op.execute("DROP TRIGGER IF EXISTS movements_audit_trigger ON movements")

    # Drop indexes
    op.drop_index('ix_movements_active', 'movements')
    op.drop_index('ix_movements_scheduled_time', 'movements')
    op.drop_index('ix_movements_type', 'movements')
    op.drop_index('ix_movements_status', 'movements')
    op.drop_index('ix_movements_inmate_id', 'movements')

    # Drop table
    op.drop_table('movements')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS movement_status_enum")
    op.execute("DROP TYPE IF EXISTS movement_type_enum")
