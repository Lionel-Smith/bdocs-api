"""add_court_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-05

Creates court_cases and court_appearances tables.
Adds court-related PostgreSQL ENUM types.
Adds deferred FK from movements to court_appearances.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================
    op.execute("""
        CREATE TYPE court_type_enum AS ENUM (
            'MAGISTRATES',
            'SUPREME',
            'COURT_OF_APPEAL',
            'PRIVY_COUNCIL',
            'CORONERS'
        );
    """)

    op.execute("""
        CREATE TYPE case_status_enum AS ENUM (
            'PENDING',
            'ACTIVE',
            'ADJUDICATED',
            'DISMISSED',
            'APPEALED'
        );
    """)

    op.execute("""
        CREATE TYPE appearance_type_enum AS ENUM (
            'ARRAIGNMENT',
            'BAIL_HEARING',
            'TRIAL',
            'SENTENCING',
            'APPEAL',
            'MOTION'
        );
    """)

    op.execute("""
        CREATE TYPE appearance_outcome_enum AS ENUM (
            'ADJOURNED',
            'BAIL_GRANTED',
            'BAIL_DENIED',
            'CONVICTED',
            'ACQUITTED',
            'SENTENCED',
            'REMANDED'
        );
    """)

    # ========================================================================
    # Create court_cases table
    # ========================================================================
    op.create_table(
        'court_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key to inmates
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Case identification
        sa.Column('case_number', sa.String(50), unique=True, nullable=False),
        # Court type
        sa.Column('court_type', postgresql.ENUM(
            'MAGISTRATES', 'SUPREME', 'COURT_OF_APPEAL', 'PRIVY_COUNCIL', 'CORONERS',
            name='court_type_enum', create_type=False
        ), nullable=False),
        # Charges (JSONB array)
        sa.Column('charges', postgresql.JSONB, nullable=False, server_default='[]'),
        # Filing date
        sa.Column('filing_date', sa.Date, nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM(
            'PENDING', 'ACTIVE', 'ADJUDICATED', 'DISMISSED', 'APPEALED',
            name='case_status_enum', create_type=False
        ), nullable=False, server_default='PENDING'),
        # Court personnel
        sa.Column('presiding_judge', sa.String(200), nullable=True),
        sa.Column('prosecutor', sa.String(200), nullable=True),
        sa.Column('defense_attorney', sa.String(200), nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
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

    # Indexes for court_cases
    op.create_index('ix_court_cases_inmate', 'court_cases', ['inmate_id'])
    op.create_index('ix_court_cases_case_number', 'court_cases', ['case_number'])
    op.create_index('ix_court_cases_status', 'court_cases', ['status'])
    op.create_index('ix_court_cases_court_type', 'court_cases', ['court_type'])
    op.create_index('ix_court_cases_filing_date', 'court_cases', ['filing_date'])

    # ========================================================================
    # Create court_appearances table
    # ========================================================================
    op.create_table(
        'court_appearances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('court_case_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('court_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Appearance details
        sa.Column('appearance_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('appearance_type', postgresql.ENUM(
            'ARRAIGNMENT', 'BAIL_HEARING', 'TRIAL', 'SENTENCING', 'APPEAL', 'MOTION',
            name='appearance_type_enum', create_type=False
        ), nullable=False),
        sa.Column('court_location', sa.String(200), nullable=False),
        # Outcome
        sa.Column('outcome', postgresql.ENUM(
            'ADJOURNED', 'BAIL_GRANTED', 'BAIL_DENIED', 'CONVICTED',
            'ACQUITTED', 'SENTENCED', 'REMANDED',
            name='appearance_outcome_enum', create_type=False
        ), nullable=True),
        # Next appearance
        sa.Column('next_appearance_date', sa.DateTime(timezone=True), nullable=True),
        # Link to movement
        sa.Column('movement_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('movements.id', ondelete='SET NULL'), nullable=True),
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

    # Indexes for court_appearances
    op.create_index('ix_court_appearances_case', 'court_appearances', ['court_case_id'])
    op.create_index('ix_court_appearances_inmate', 'court_appearances', ['inmate_id'])
    op.create_index('ix_court_appearances_date', 'court_appearances', ['appearance_date'])
    op.create_index('ix_court_appearances_movement', 'court_appearances', ['movement_id'])
    # Partial index for upcoming appearances (no outcome yet)
    op.create_index('ix_court_appearances_upcoming', 'court_appearances',
                    ['appearance_date', 'outcome'],
                    postgresql_where=sa.text("outcome IS NULL"))

    # ========================================================================
    # Add deferred FK from movements to court_appearances
    # ========================================================================
    op.execute("""
        ALTER TABLE movements
        ADD CONSTRAINT movements_court_appearance_id_fkey
        FOREIGN KEY (court_appearance_id)
        REFERENCES court_appearances(id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;
    """)

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['court_cases', 'court_appearances']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['court_appearances', 'court_cases']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop deferred FK from movements
    op.execute("ALTER TABLE movements DROP CONSTRAINT IF EXISTS movements_court_appearance_id_fkey")

    # Drop indexes
    op.drop_index('ix_court_appearances_upcoming', 'court_appearances')
    op.drop_index('ix_court_appearances_movement', 'court_appearances')
    op.drop_index('ix_court_appearances_date', 'court_appearances')
    op.drop_index('ix_court_appearances_inmate', 'court_appearances')
    op.drop_index('ix_court_appearances_case', 'court_appearances')

    op.drop_index('ix_court_cases_filing_date', 'court_cases')
    op.drop_index('ix_court_cases_court_type', 'court_cases')
    op.drop_index('ix_court_cases_status', 'court_cases')
    op.drop_index('ix_court_cases_case_number', 'court_cases')
    op.drop_index('ix_court_cases_inmate', 'court_cases')

    # Drop tables
    op.drop_table('court_appearances')
    op.drop_table('court_cases')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS appearance_outcome_enum")
    op.execute("DROP TYPE IF EXISTS appearance_type_enum")
    op.execute("DROP TYPE IF EXISTS case_status_enum")
    op.execute("DROP TYPE IF EXISTS court_type_enum")
