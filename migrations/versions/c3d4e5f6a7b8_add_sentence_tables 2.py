"""add_sentence_tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-05

Creates sentences and sentence_adjustments tables.
Updates sentence_type_enum with new values.
Creates adjustment_type_enum.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create/Update PostgreSQL ENUM types
    # ========================================================================

    # Create sentence_type_enum (with all values including new ones)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sentence_type_enum') THEN
                CREATE TYPE sentence_type_enum AS ENUM (
                    'IMPRISONMENT',
                    'LIFE',
                    'DEATH',
                    'SUSPENDED',
                    'TIME_SERVED',
                    'PROBATION',
                    'FINE'
                );
            ELSE
                -- Add new values if they don't exist
                BEGIN
                    ALTER TYPE sentence_type_enum ADD VALUE IF NOT EXISTS 'PROBATION';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
                BEGIN
                    ALTER TYPE sentence_type_enum ADD VALUE IF NOT EXISTS 'FINE';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
            END IF;
        END$$;
    """)

    # Create adjustment_type_enum
    op.execute("""
        CREATE TYPE adjustment_type_enum AS ENUM (
            'GOOD_TIME',
            'REMISSION',
            'TIME_SERVED_CREDIT',
            'CLEMENCY_REDUCTION',
            'COURT_MODIFICATION'
        );
    """)

    # ========================================================================
    # Create sentences table
    # ========================================================================
    op.create_table(
        'sentences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('court_case_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('court_cases.id', ondelete='CASCADE'), nullable=False),
        # Sentence date and type
        sa.Column('sentence_date', sa.Date, nullable=False),
        sa.Column('sentence_type', postgresql.ENUM(
            'IMPRISONMENT', 'LIFE', 'DEATH', 'SUSPENDED',
            'TIME_SERVED', 'PROBATION', 'FINE',
            name='sentence_type_enum', create_type=False
        ), nullable=False),
        # Term details
        sa.Column('original_term_months', sa.Integer, nullable=True),
        sa.Column('life_sentence', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_death_sentence', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('minimum_term_months', sa.Integer, nullable=True),
        # Dates
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('expected_release_date', sa.Date, nullable=True),
        sa.Column('actual_release_date', sa.Date, nullable=True),
        # Time credits
        sa.Column('time_served_days', sa.Integer, nullable=False, server_default='0'),
        sa.Column('good_time_days', sa.Integer, nullable=False, server_default='0'),
        # Court personnel
        sa.Column('sentencing_judge', sa.String(200), nullable=True),
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

    # Indexes for sentences
    op.create_index('ix_sentences_inmate', 'sentences', ['inmate_id'])
    op.create_index('ix_sentences_case', 'sentences', ['court_case_id'])
    op.create_index('ix_sentences_type', 'sentences', ['sentence_type'])
    op.create_index('ix_sentences_release', 'sentences', ['expected_release_date'])
    op.create_index('ix_sentences_death', 'sentences', ['is_death_sentence'],
                    postgresql_where=sa.text("is_death_sentence = true"))

    # ========================================================================
    # Create sentence_adjustments table
    # ========================================================================
    op.create_table(
        'sentence_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key to sentence
        sa.Column('sentence_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('sentences.id', ondelete='CASCADE'), nullable=False),
        # Adjustment type
        sa.Column('adjustment_type', postgresql.ENUM(
            'GOOD_TIME', 'REMISSION', 'TIME_SERVED_CREDIT',
            'CLEMENCY_REDUCTION', 'COURT_MODIFICATION',
            name='adjustment_type_enum', create_type=False
        ), nullable=False),
        # Days adjustment
        sa.Column('days', sa.Integer, nullable=False),
        # Effective date
        sa.Column('effective_date', sa.Date, nullable=False),
        # Reason and documentation
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('document_reference', sa.String(100), nullable=True),
        # Approved by
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
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

    # Indexes for sentence_adjustments
    op.create_index('ix_sentence_adjustments_sentence', 'sentence_adjustments', ['sentence_id'])
    op.create_index('ix_sentence_adjustments_type', 'sentence_adjustments', ['adjustment_type'])
    op.create_index('ix_sentence_adjustments_date', 'sentence_adjustments', ['effective_date'])

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['sentences', 'sentence_adjustments']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['sentence_adjustments', 'sentences']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes
    op.drop_index('ix_sentence_adjustments_date', 'sentence_adjustments')
    op.drop_index('ix_sentence_adjustments_type', 'sentence_adjustments')
    op.drop_index('ix_sentence_adjustments_sentence', 'sentence_adjustments')

    op.drop_index('ix_sentences_death', 'sentences')
    op.drop_index('ix_sentences_release', 'sentences')
    op.drop_index('ix_sentences_type', 'sentences')
    op.drop_index('ix_sentences_case', 'sentences')
    op.drop_index('ix_sentences_inmate', 'sentences')

    # Drop tables
    op.drop_table('sentence_adjustments')
    op.drop_table('sentences')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS adjustment_type_enum")
    # Note: Don't drop sentence_type_enum as it may be used elsewhere
