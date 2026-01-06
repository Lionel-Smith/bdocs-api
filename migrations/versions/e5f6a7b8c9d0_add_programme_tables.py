"""add_programme_tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-01-05

Creates programmes, programme_sessions, and programme_enrollments tables.
Creates programme_category_enum, session_status_enum, and enrollment_status_enum.

Phase 2 of BDOCS: Rehabilitation Programme Management
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create programme_category_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'programme_category_enum') THEN
                CREATE TYPE programme_category_enum AS ENUM (
                    'EDUCATIONAL',
                    'VOCATIONAL',
                    'THERAPEUTIC',
                    'RELIGIOUS',
                    'LIFE_SKILLS'
                );
            END IF;
        END$$;
    """)

    # Create session_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status_enum') THEN
                CREATE TYPE session_status_enum AS ENUM (
                    'SCHEDULED',
                    'COMPLETED',
                    'CANCELLED'
                );
            END IF;
        END$$;
    """)

    # Create enrollment_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'enrollment_status_enum') THEN
                CREATE TYPE enrollment_status_enum AS ENUM (
                    'ENROLLED',
                    'ACTIVE',
                    'COMPLETED',
                    'WITHDRAWN',
                    'SUSPENDED'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create programmes table
    # ========================================================================
    op.create_table(
        'programmes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Programme identification
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        # Category
        sa.Column('category', postgresql.ENUM(
            'EDUCATIONAL', 'VOCATIONAL', 'THERAPEUTIC', 'RELIGIOUS', 'LIFE_SKILLS',
            name='programme_category_enum', create_type=False
        ), nullable=False),
        # Provider
        sa.Column('provider', sa.String(200), nullable=False),
        # Programme structure
        sa.Column('duration_weeks', sa.Integer, nullable=False),
        sa.Column('max_participants', sa.Integer, nullable=False),
        # Eligibility
        sa.Column('eligibility_criteria', postgresql.JSONB, nullable=True),
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
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

    # Indexes for programmes
    op.create_index('ix_programmes_code', 'programmes', ['code'])
    op.create_index('ix_programmes_category', 'programmes', ['category'])
    op.create_index('ix_programmes_active', 'programmes', ['is_active'])
    op.create_index(
        'ix_programmes_active_category',
        'programmes',
        ['is_active', 'category'],
        postgresql_where=sa.text("is_deleted = false")
    )

    # ========================================================================
    # Create programme_sessions table
    # ========================================================================
    op.create_table(
        'programme_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key to programme
        sa.Column('programme_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False),
        # Session scheduling
        sa.Column('session_date', sa.Date, nullable=False),
        sa.Column('start_time', sa.Time, nullable=False),
        sa.Column('end_time', sa.Time, nullable=False),
        # Location and instructor
        sa.Column('location', sa.String(200), nullable=False),
        sa.Column('instructor_name', sa.String(200), nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'COMPLETED', 'CANCELLED',
            name='session_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Attendance
        sa.Column('attendance_count', sa.Integer, nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Audit fields (no soft delete - sessions are permanent records)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for programme_sessions
    op.create_index('ix_programme_sessions_programme', 'programme_sessions', ['programme_id'])
    op.create_index('ix_programme_sessions_date', 'programme_sessions', ['session_date'])
    op.create_index('ix_programme_sessions_status', 'programme_sessions', ['status'])
    op.create_index(
        'ix_programme_sessions_upcoming',
        'programme_sessions',
        ['session_date', 'status'],
        postgresql_where=sa.text("status = 'SCHEDULED'")
    )

    # ========================================================================
    # Create programme_enrollments table
    # ========================================================================
    op.create_table(
        'programme_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('programme_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Enrollment dates
        sa.Column('enrolled_date', sa.Date, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM(
            'ENROLLED', 'ACTIVE', 'COMPLETED', 'WITHDRAWN', 'SUSPENDED',
            name='enrollment_status_enum', create_type=False
        ), nullable=False, server_default='ENROLLED'),
        # Completion details
        sa.Column('completion_date', sa.Date, nullable=True),
        sa.Column('grade', sa.String(10), nullable=True),
        sa.Column('certificate_issued', sa.Boolean, nullable=False, server_default='false'),
        # Progress tracking
        sa.Column('hours_completed', sa.Integer, nullable=False, server_default='0'),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Enrolled by
        sa.Column('enrolled_by', postgresql.UUID(as_uuid=True), nullable=True),
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

    # Indexes for programme_enrollments
    op.create_index('ix_programme_enrollments_programme', 'programme_enrollments', ['programme_id'])
    op.create_index('ix_programme_enrollments_inmate', 'programme_enrollments', ['inmate_id'])
    op.create_index('ix_programme_enrollments_status', 'programme_enrollments', ['status'])
    op.create_index('ix_programme_enrollments_enrolled', 'programme_enrollments', ['enrolled_date'])
    # Unique partial index: one active enrollment per inmate per programme
    op.create_index(
        'ix_programme_enrollments_unique_active',
        'programme_enrollments',
        ['programme_id', 'inmate_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('ENROLLED', 'ACTIVE') AND is_deleted = false")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['programmes', 'programme_sessions', 'programme_enrollments']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['programme_enrollments', 'programme_sessions', 'programmes']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for programme_enrollments
    op.drop_index('ix_programme_enrollments_unique_active', 'programme_enrollments')
    op.drop_index('ix_programme_enrollments_enrolled', 'programme_enrollments')
    op.drop_index('ix_programme_enrollments_status', 'programme_enrollments')
    op.drop_index('ix_programme_enrollments_inmate', 'programme_enrollments')
    op.drop_index('ix_programme_enrollments_programme', 'programme_enrollments')

    # Drop indexes for programme_sessions
    op.drop_index('ix_programme_sessions_upcoming', 'programme_sessions')
    op.drop_index('ix_programme_sessions_status', 'programme_sessions')
    op.drop_index('ix_programme_sessions_date', 'programme_sessions')
    op.drop_index('ix_programme_sessions_programme', 'programme_sessions')

    # Drop indexes for programmes
    op.drop_index('ix_programmes_active_category', 'programmes')
    op.drop_index('ix_programmes_active', 'programmes')
    op.drop_index('ix_programmes_category', 'programmes')
    op.drop_index('ix_programmes_code', 'programmes')

    # Drop tables
    op.drop_table('programme_enrollments')
    op.drop_table('programme_sessions')
    op.drop_table('programmes')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS enrollment_status_enum")
    op.execute("DROP TYPE IF EXISTS session_status_enum")
    op.execute("DROP TYPE IF EXISTS programme_category_enum")
