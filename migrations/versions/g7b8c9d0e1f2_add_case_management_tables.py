"""add_case_management_tables

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-01-05

Creates case_assignments, case_notes, and rehabilitation_goals tables.
Creates note_type_enum, goal_type_enum, and goal_status_enum.

Case management is central to rehabilitation success.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create note_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'note_type_enum') THEN
                CREATE TYPE note_type_enum AS ENUM (
                    'INITIAL_ASSESSMENT',
                    'PROGRESS_UPDATE',
                    'INCIDENT_REPORT',
                    'PROGRAMME_REVIEW',
                    'RELEASE_PLANNING',
                    'GENERAL'
                );
            END IF;
        END$$;
    """)

    # Create goal_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goal_type_enum') THEN
                CREATE TYPE goal_type_enum AS ENUM (
                    'EDUCATION',
                    'VOCATIONAL',
                    'BEHAVIORAL',
                    'SUBSTANCE_ABUSE',
                    'FAMILY_REUNIFICATION',
                    'EMPLOYMENT',
                    'HOUSING'
                );
            END IF;
        END$$;
    """)

    # Create goal_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goal_status_enum') THEN
                CREATE TYPE goal_status_enum AS ENUM (
                    'NOT_STARTED',
                    'IN_PROGRESS',
                    'COMPLETED',
                    'DEFERRED',
                    'CANCELLED'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create case_assignments table
    # ========================================================================
    op.create_table(
        'case_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_officer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Assignment dates
        sa.Column('assigned_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        # Notes
        sa.Column('caseload_notes', sa.Text, nullable=True),
        # Assigned by
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
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

    # Indexes for case_assignments
    op.create_index('ix_case_assignments_inmate', 'case_assignments', ['inmate_id'])
    op.create_index('ix_case_assignments_officer', 'case_assignments', ['case_officer_id'])
    op.create_index('ix_case_assignments_active', 'case_assignments', ['is_active'])
    op.create_index('ix_case_assignments_assigned', 'case_assignments', ['assigned_date'])
    # Unique partial index: one active assignment per inmate
    op.create_index(
        'ix_case_assignments_unique_active',
        'case_assignments',
        ['inmate_id'],
        unique=True,
        postgresql_where=sa.text("is_active = true AND is_deleted = false")
    )

    # ========================================================================
    # Create case_notes table
    # ========================================================================
    op.create_table(
        'case_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('case_assignment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('case_assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Note details
        sa.Column('note_date', sa.Date, nullable=False),
        sa.Column('note_type', postgresql.ENUM(
            'INITIAL_ASSESSMENT', 'PROGRESS_UPDATE', 'INCIDENT_REPORT',
            'PROGRAMME_REVIEW', 'RELEASE_PLANNING', 'GENERAL',
            name='note_type_enum', create_type=False
        ), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        # Confidentiality
        sa.Column('is_confidential', sa.Boolean, nullable=False, server_default='false'),
        # Follow-up
        sa.Column('follow_up_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('follow_up_date', sa.Date, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Audit fields (no soft delete - notes are permanent)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for case_notes
    op.create_index('ix_case_notes_assignment', 'case_notes', ['case_assignment_id'])
    op.create_index('ix_case_notes_inmate', 'case_notes', ['inmate_id'])
    op.create_index('ix_case_notes_date', 'case_notes', ['note_date'])
    op.create_index('ix_case_notes_type', 'case_notes', ['note_type'])
    # Partial index for follow-ups
    op.create_index(
        'ix_case_notes_followup',
        'case_notes',
        ['follow_up_required', 'follow_up_date'],
        postgresql_where=sa.text("follow_up_required = true")
    )

    # ========================================================================
    # Create rehabilitation_goals table
    # ========================================================================
    op.create_table(
        'rehabilitation_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Goal details
        sa.Column('goal_type', postgresql.ENUM(
            'EDUCATION', 'VOCATIONAL', 'BEHAVIORAL', 'SUBSTANCE_ABUSE',
            'FAMILY_REUNIFICATION', 'EMPLOYMENT', 'HOUSING',
            name='goal_type_enum', create_type=False
        ), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        # Timeline
        sa.Column('target_date', sa.Date, nullable=False),
        # Status and progress
        sa.Column('status', postgresql.ENUM(
            'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'DEFERRED', 'CANCELLED',
            name='goal_status_enum', create_type=False
        ), nullable=False, server_default='NOT_STARTED'),
        sa.Column('progress_percentage', sa.Integer, nullable=False, server_default='0'),
        # Completion
        sa.Column('completion_date', sa.Date, nullable=True),
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

    # Check constraint for progress percentage
    op.execute("""
        ALTER TABLE rehabilitation_goals
        ADD CONSTRAINT ck_rehabilitation_goals_progress_range
        CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
    """)

    # Indexes for rehabilitation_goals
    op.create_index('ix_rehabilitation_goals_inmate', 'rehabilitation_goals', ['inmate_id'])
    op.create_index('ix_rehabilitation_goals_type', 'rehabilitation_goals', ['goal_type'])
    op.create_index('ix_rehabilitation_goals_status', 'rehabilitation_goals', ['status'])
    op.create_index('ix_rehabilitation_goals_target', 'rehabilitation_goals', ['target_date'])
    # Partial index for overdue goals
    op.create_index(
        'ix_rehabilitation_goals_overdue',
        'rehabilitation_goals',
        ['target_date', 'status'],
        postgresql_where=sa.text("status IN ('NOT_STARTED', 'IN_PROGRESS') AND is_deleted = false")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['case_assignments', 'case_notes', 'rehabilitation_goals']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['rehabilitation_goals', 'case_notes', 'case_assignments']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop check constraint
    op.execute("ALTER TABLE rehabilitation_goals DROP CONSTRAINT IF EXISTS ck_rehabilitation_goals_progress_range")

    # Drop indexes for rehabilitation_goals
    op.drop_index('ix_rehabilitation_goals_overdue', 'rehabilitation_goals')
    op.drop_index('ix_rehabilitation_goals_target', 'rehabilitation_goals')
    op.drop_index('ix_rehabilitation_goals_status', 'rehabilitation_goals')
    op.drop_index('ix_rehabilitation_goals_type', 'rehabilitation_goals')
    op.drop_index('ix_rehabilitation_goals_inmate', 'rehabilitation_goals')

    # Drop indexes for case_notes
    op.drop_index('ix_case_notes_followup', 'case_notes')
    op.drop_index('ix_case_notes_type', 'case_notes')
    op.drop_index('ix_case_notes_date', 'case_notes')
    op.drop_index('ix_case_notes_inmate', 'case_notes')
    op.drop_index('ix_case_notes_assignment', 'case_notes')

    # Drop indexes for case_assignments
    op.drop_index('ix_case_assignments_unique_active', 'case_assignments')
    op.drop_index('ix_case_assignments_assigned', 'case_assignments')
    op.drop_index('ix_case_assignments_active', 'case_assignments')
    op.drop_index('ix_case_assignments_officer', 'case_assignments')
    op.drop_index('ix_case_assignments_inmate', 'case_assignments')

    # Drop tables
    op.drop_table('rehabilitation_goals')
    op.drop_table('case_notes')
    op.drop_table('case_assignments')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS goal_status_enum")
    op.execute("DROP TYPE IF EXISTS goal_type_enum")
    op.execute("DROP TYPE IF EXISTS note_type_enum")
