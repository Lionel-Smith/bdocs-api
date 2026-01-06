"""add_incident_management_tables

Revision ID: j0e1f2g3h4i5
Revises: i9d0e1f2g3h4
Create Date: 2026-01-05

Creates incidents, incident_involvements, and incident_attachments tables.
Creates incident_type_enum, incident_severity_enum, incident_status_enum,
and involvement_type_enum.

Phase 3: Operations & Security - Incident Management.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j0e1f2g3h4i5'
down_revision: Union[str, None] = 'i9d0e1f2g3h4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create incident_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_type_enum') THEN
                CREATE TYPE incident_type_enum AS ENUM (
                    'ASSAULT',
                    'CONTRABAND',
                    'ESCAPE_ATTEMPT',
                    'MEDICAL_EMERGENCY',
                    'FIRE',
                    'DISTURBANCE',
                    'PROPERTY_DAMAGE',
                    'DEATH',
                    'SUICIDE_ATTEMPT',
                    'DRUG_USE',
                    'WEAPON',
                    'OTHER'
                );
            END IF;
        END$$;
    """)

    # Create incident_severity_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_severity_enum') THEN
                CREATE TYPE incident_severity_enum AS ENUM (
                    'LOW',
                    'MEDIUM',
                    'HIGH',
                    'CRITICAL'
                );
            END IF;
        END$$;
    """)

    # Create incident_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_status_enum') THEN
                CREATE TYPE incident_status_enum AS ENUM (
                    'REPORTED',
                    'UNDER_INVESTIGATION',
                    'RESOLVED',
                    'CLOSED'
                );
            END IF;
        END$$;
    """)

    # Create involvement_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'involvement_type_enum') THEN
                CREATE TYPE involvement_type_enum AS ENUM (
                    'VICTIM',
                    'PERPETRATOR',
                    'WITNESS',
                    'RESPONDER',
                    'OTHER'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create incidents table
    # ========================================================================
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Incident number
        sa.Column('incident_number', sa.String(20), unique=True, nullable=False),
        # Classification
        sa.Column('incident_type', postgresql.ENUM(
            'ASSAULT', 'CONTRABAND', 'ESCAPE_ATTEMPT', 'MEDICAL_EMERGENCY',
            'FIRE', 'DISTURBANCE', 'PROPERTY_DAMAGE', 'DEATH',
            'SUICIDE_ATTEMPT', 'DRUG_USE', 'WEAPON', 'OTHER',
            name='incident_type_enum', create_type=False
        ), nullable=False),
        sa.Column('severity', postgresql.ENUM(
            'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
            name='incident_severity_enum', create_type=False
        ), nullable=False, server_default='MEDIUM'),
        sa.Column('status', postgresql.ENUM(
            'REPORTED', 'UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED',
            name='incident_status_enum', create_type=False
        ), nullable=False, server_default='REPORTED'),
        # When and where
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', sa.String(200), nullable=False),
        # Reporting
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reported_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Description
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('immediate_actions', sa.Text, nullable=True),
        # Impact
        sa.Column('injuries_reported', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('property_damage', sa.Boolean, nullable=False, server_default='false'),
        # External notification
        sa.Column('external_notification_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('external_notified', sa.Boolean, nullable=False, server_default='false'),
        # Resolution
        sa.Column('resolution', sa.Text, nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
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

    # Indexes for incidents
    op.create_index('ix_incidents_number', 'incidents', ['incident_number'])
    op.create_index('ix_incidents_type', 'incidents', ['incident_type'])
    op.create_index('ix_incidents_severity', 'incidents', ['severity'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_occurred', 'incidents', ['occurred_at'])
    op.create_index('ix_incidents_reported_by', 'incidents', ['reported_by'])
    # Partial index for open incidents
    op.create_index(
        'ix_incidents_open',
        'incidents',
        ['status', 'severity'],
        postgresql_where=sa.text("status IN ('REPORTED', 'UNDER_INVESTIGATION') AND is_deleted = false")
    )
    # Partial index for critical incidents
    op.create_index(
        'ix_incidents_critical',
        'incidents',
        ['severity', 'status'],
        postgresql_where=sa.text("severity = 'CRITICAL' AND is_deleted = false")
    )

    # ========================================================================
    # Create incident_involvements table
    # ========================================================================
    op.create_table(
        'incident_involvements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('incident_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        # Involvement type
        sa.Column('involvement_type', postgresql.ENUM(
            'VICTIM', 'PERPETRATOR', 'WITNESS', 'RESPONDER', 'OTHER',
            name='involvement_type_enum', create_type=False
        ), nullable=False),
        # Details
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('injuries', sa.Text, nullable=True),
        sa.Column('disciplinary_action_taken', sa.Boolean, nullable=False, server_default='false'),
        # Audit fields (no soft delete - permanent records)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for incident_involvements
    op.create_index('ix_incident_involvements_incident', 'incident_involvements', ['incident_id'])
    op.create_index('ix_incident_involvements_inmate', 'incident_involvements', ['inmate_id'])
    op.create_index('ix_incident_involvements_staff', 'incident_involvements', ['staff_id'])
    op.create_index('ix_incident_involvements_type', 'incident_involvements', ['involvement_type'])

    # ========================================================================
    # Create incident_attachments table
    # ========================================================================
    op.create_table(
        'incident_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign key
        sa.Column('incident_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        # File information
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        # Upload information
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Description
        sa.Column('description', sa.Text, nullable=True),
        # Audit fields (no soft delete - permanent records)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for incident_attachments
    op.create_index('ix_incident_attachments_incident', 'incident_attachments', ['incident_id'])
    op.create_index('ix_incident_attachments_uploaded', 'incident_attachments', ['uploaded_at'])

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['incidents', 'incident_involvements', 'incident_attachments']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['incident_attachments', 'incident_involvements', 'incidents']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for incident_attachments
    op.drop_index('ix_incident_attachments_uploaded', 'incident_attachments')
    op.drop_index('ix_incident_attachments_incident', 'incident_attachments')

    # Drop indexes for incident_involvements
    op.drop_index('ix_incident_involvements_type', 'incident_involvements')
    op.drop_index('ix_incident_involvements_staff', 'incident_involvements')
    op.drop_index('ix_incident_involvements_inmate', 'incident_involvements')
    op.drop_index('ix_incident_involvements_incident', 'incident_involvements')

    # Drop indexes for incidents
    op.drop_index('ix_incidents_critical', 'incidents')
    op.drop_index('ix_incidents_open', 'incidents')
    op.drop_index('ix_incidents_reported_by', 'incidents')
    op.drop_index('ix_incidents_occurred', 'incidents')
    op.drop_index('ix_incidents_status', 'incidents')
    op.drop_index('ix_incidents_severity', 'incidents')
    op.drop_index('ix_incidents_type', 'incidents')
    op.drop_index('ix_incidents_number', 'incidents')

    # Drop tables
    op.drop_table('incident_attachments')
    op.drop_table('incident_involvements')
    op.drop_table('incidents')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS involvement_type_enum")
    op.execute("DROP TYPE IF EXISTS incident_status_enum")
    op.execute("DROP TYPE IF EXISTS incident_severity_enum")
    op.execute("DROP TYPE IF EXISTS incident_type_enum")
