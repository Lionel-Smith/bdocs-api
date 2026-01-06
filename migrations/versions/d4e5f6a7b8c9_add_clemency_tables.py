"""add_clemency_tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-05

Creates clemency_petitions and clemency_status_history tables.
Creates petition_type_enum and petition_status_enum.

IMPORTANT: The Bahamas has NO parole system. This implements the
Prerogative of Mercy workflow per Articles 90-92 of The Bahamas Constitution.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create petition_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'petition_type_enum') THEN
                CREATE TYPE petition_type_enum AS ENUM (
                    'COMMUTATION',
                    'PARDON',
                    'REMISSION',
                    'REPRIEVE'
                );
            END IF;
        END$$;
    """)

    # Create petition_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'petition_status_enum') THEN
                CREATE TYPE petition_status_enum AS ENUM (
                    'SUBMITTED',
                    'UNDER_REVIEW',
                    'COMMITTEE_SCHEDULED',
                    'AWAITING_MINISTER',
                    'GOVERNOR_GENERAL',
                    'GRANTED',
                    'DENIED',
                    'WITHDRAWN',
                    'DEFERRED'
                );
            ELSE
                -- Add GOVERNOR_GENERAL if it doesn't exist
                BEGIN
                    ALTER TYPE petition_status_enum ADD VALUE IF NOT EXISTS 'GOVERNOR_GENERAL'
                        AFTER 'AWAITING_MINISTER';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create clemency_petitions table
    # ========================================================================
    op.create_table(
        'clemency_petitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sentence_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('sentences.id', ondelete='CASCADE'), nullable=False),
        # Petition identification
        sa.Column('petition_number', sa.String(20), unique=True, nullable=False),
        # Petition type and status
        sa.Column('petition_type', postgresql.ENUM(
            'COMMUTATION', 'PARDON', 'REMISSION', 'REPRIEVE',
            name='petition_type_enum', create_type=False
        ), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum', create_type=False
        ), nullable=False, server_default='SUBMITTED'),
        # Filing details
        sa.Column('filed_date', sa.Date, nullable=False),
        sa.Column('petitioner_name', sa.String(200), nullable=False),
        sa.Column('petitioner_relationship', sa.String(100), nullable=False),
        # Grounds and documentation
        sa.Column('grounds_for_clemency', sa.Text, nullable=False),
        sa.Column('supporting_documents', postgresql.JSONB, nullable=True),
        # Victim notification
        sa.Column('victim_notification_date', sa.Date, nullable=True),
        sa.Column('victim_response', sa.Text, nullable=True),
        # Advisory Committee review
        sa.Column('committee_review_date', sa.Date, nullable=True),
        sa.Column('committee_recommendation', sa.Text, nullable=True),
        # Minister review
        sa.Column('minister_review_date', sa.Date, nullable=True),
        sa.Column('minister_recommendation', sa.Text, nullable=True),
        # Governor-General decision
        sa.Column('governor_general_date', sa.Date, nullable=True),
        sa.Column('decision_date', sa.Date, nullable=True),
        sa.Column('decision_notes', sa.Text, nullable=True),
        # For granted petitions
        sa.Column('granted_reduction_days', sa.Integer, nullable=True),
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

    # Indexes for clemency_petitions
    op.create_index('ix_clemency_petitions_inmate', 'clemency_petitions', ['inmate_id'])
    op.create_index('ix_clemency_petitions_sentence', 'clemency_petitions', ['sentence_id'])
    op.create_index('ix_clemency_petitions_number', 'clemency_petitions', ['petition_number'])
    op.create_index('ix_clemency_petitions_status', 'clemency_petitions', ['status'])
    op.create_index('ix_clemency_petitions_type', 'clemency_petitions', ['petition_type'])
    op.create_index('ix_clemency_petitions_filed', 'clemency_petitions', ['filed_date'])
    # Partial index for pending petitions (common query)
    op.create_index(
        'ix_clemency_petitions_pending',
        'clemency_petitions',
        ['status'],
        postgresql_where=sa.text("status NOT IN ('GRANTED', 'DENIED', 'WITHDRAWN')")
    )

    # ========================================================================
    # Create clemency_status_history table
    # ========================================================================
    op.create_table(
        'clemency_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key to petition
        sa.Column('petition_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('clemency_petitions.id', ondelete='CASCADE'), nullable=False),
        # Status transition
        sa.Column('from_status', postgresql.ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum', create_type=False
        ), nullable=True),  # Null for initial submission
        sa.Column('to_status', postgresql.ENUM(
            'SUBMITTED', 'UNDER_REVIEW', 'COMMITTEE_SCHEDULED',
            'AWAITING_MINISTER', 'GOVERNOR_GENERAL',
            'GRANTED', 'DENIED', 'WITHDRAWN', 'DEFERRED',
            name='petition_status_enum', create_type=False
        ), nullable=False),
        # Timestamp
        sa.Column('changed_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Changed by
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Audit fields (no soft delete - history is permanent)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for clemency_status_history
    op.create_index('ix_clemency_history_petition', 'clemency_status_history', ['petition_id'])
    op.create_index('ix_clemency_history_date', 'clemency_status_history', ['changed_date'])

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['clemency_petitions', 'clemency_status_history']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['clemency_status_history', 'clemency_petitions']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for clemency_status_history
    op.drop_index('ix_clemency_history_date', 'clemency_status_history')
    op.drop_index('ix_clemency_history_petition', 'clemency_status_history')

    # Drop indexes for clemency_petitions
    op.drop_index('ix_clemency_petitions_pending', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_filed', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_type', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_status', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_number', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_sentence', 'clemency_petitions')
    op.drop_index('ix_clemency_petitions_inmate', 'clemency_petitions')

    # Drop tables
    op.drop_table('clemency_status_history')
    op.drop_table('clemency_petitions')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS petition_status_enum")
    op.execute("DROP TYPE IF EXISTS petition_type_enum")
