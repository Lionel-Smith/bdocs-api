"""add_healthcare_management_tables

Revision ID: m3h4i5j6k7l8
Revises: l2g3h4i5j6k7
Create Date: 2026-01-05

Creates medical_records, medical_encounters, and medication_administrations tables.
Creates blood_type_enum, encounter_type_enum, provider_type_enum,
route_type_enum, and med_admin_status_enum.

Phase 3: Operations & Security - Healthcare Management.

HIPAA NOTE: These tables contain Protected Health Information (PHI).
Access must be restricted to authorized medical personnel.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'm3h4i5j6k7l8'
down_revision: Union[str, None] = 'l2g3h4i5j6k7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create blood_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'blood_type_enum') THEN
                CREATE TYPE blood_type_enum AS ENUM (
                    'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN'
                );
            END IF;
        END$$;
    """)

    # Create encounter_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'encounter_type_enum') THEN
                CREATE TYPE encounter_type_enum AS ENUM (
                    'INTAKE_SCREENING',
                    'SICK_CALL',
                    'EMERGENCY',
                    'SCHEDULED',
                    'MENTAL_HEALTH',
                    'DENTAL',
                    'FOLLOW_UP'
                );
            END IF;
        END$$;
    """)

    # Create provider_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'provider_type_enum') THEN
                CREATE TYPE provider_type_enum AS ENUM (
                    'PHYSICIAN',
                    'NURSE',
                    'MENTAL_HEALTH',
                    'DENTIST',
                    'PARAMEDIC'
                );
            END IF;
        END$$;
    """)

    # Create route_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'route_type_enum') THEN
                CREATE TYPE route_type_enum AS ENUM (
                    'ORAL',
                    'INJECTION',
                    'TOPICAL',
                    'INHALED'
                );
            END IF;
        END$$;
    """)

    # Create med_admin_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'med_admin_status_enum') THEN
                CREATE TYPE med_admin_status_enum AS ENUM (
                    'SCHEDULED',
                    'ADMINISTERED',
                    'REFUSED',
                    'MISSED',
                    'HELD'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create medical_records table
    # ========================================================================
    op.create_table(
        'medical_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # One-to-one with inmate
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'),
                  unique=True, nullable=False),
        # Blood type
        sa.Column('blood_type', postgresql.ENUM(
            'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN',
            name='blood_type_enum', create_type=False
        ), nullable=True),
        # Health data (JSONB arrays)
        sa.Column('allergies', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('chronic_conditions', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('current_medications', postgresql.JSONB, nullable=True, server_default='[]'),
        # Emergency contact
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        # Physical examination schedule
        sa.Column('last_physical_date', sa.Date, nullable=True),
        sa.Column('next_physical_due', sa.Date, nullable=True),
        # Mental health flags - CRITICAL
        sa.Column('mental_health_flag', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('suicide_watch', sa.Boolean, nullable=False, server_default='false'),
        # Dietary and disability
        sa.Column('dietary_restrictions', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('disability_accommodations', sa.Text, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields (no soft delete for medical records - legal retention)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for medical_records
    op.create_index('ix_medical_records_inmate', 'medical_records', ['inmate_id'])
    op.create_index('ix_medical_records_blood_type', 'medical_records', ['blood_type'])
    op.create_index('ix_medical_records_mental_health', 'medical_records', ['mental_health_flag'])
    op.create_index('ix_medical_records_suicide_watch', 'medical_records', ['suicide_watch'])
    op.create_index('ix_medical_records_next_physical', 'medical_records', ['next_physical_due'])

    # ========================================================================
    # Create medical_encounters table
    # ========================================================================
    op.create_table(
        'medical_encounters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Inmate reference
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Encounter details
        sa.Column('encounter_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('encounter_type', postgresql.ENUM(
            'INTAKE_SCREENING', 'SICK_CALL', 'EMERGENCY', 'SCHEDULED',
            'MENTAL_HEALTH', 'DENTAL', 'FOLLOW_UP',
            name='encounter_type_enum', create_type=False
        ), nullable=False),
        # Chief complaint
        sa.Column('chief_complaint', sa.Text, nullable=False),
        # Vitals
        sa.Column('vitals', postgresql.JSONB, nullable=True),
        # Clinical findings
        sa.Column('diagnosis', sa.Text, nullable=True),
        sa.Column('treatment', sa.Text, nullable=True),
        sa.Column('medications_prescribed', postgresql.JSONB, nullable=True, server_default='[]'),
        # Follow-up
        sa.Column('follow_up_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('follow_up_date', sa.Date, nullable=True),
        # Provider
        sa.Column('provider_name', sa.String(200), nullable=False),
        sa.Column('provider_type', postgresql.ENUM(
            'PHYSICIAN', 'NURSE', 'MENTAL_HEALTH', 'DENTIST', 'PARAMEDIC',
            name='provider_type_enum', create_type=False
        ), nullable=False),
        # Location
        sa.Column('location', sa.String(100), nullable=False, server_default='Medical Unit'),
        # External referral
        sa.Column('referred_external', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('external_facility', sa.String(200), nullable=True),
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

    # Indexes for medical_encounters
    op.create_index('ix_medical_encounters_inmate', 'medical_encounters', ['inmate_id'])
    op.create_index('ix_medical_encounters_date', 'medical_encounters', ['encounter_date'])
    op.create_index('ix_medical_encounters_type', 'medical_encounters', ['encounter_type'])
    op.create_index('ix_medical_encounters_provider_type', 'medical_encounters', ['provider_type'])
    op.create_index('ix_medical_encounters_follow_up', 'medical_encounters', ['follow_up_date'])
    op.create_index('ix_medical_encounters_external', 'medical_encounters', ['referred_external'])

    # ========================================================================
    # Create medication_administrations table
    # ========================================================================
    op.create_table(
        'medication_administrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Inmate reference
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        # Medication details
        sa.Column('medication_name', sa.String(200), nullable=False),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('route', postgresql.ENUM(
            'ORAL', 'INJECTION', 'TOPICAL', 'INHALED',
            name='route_type_enum', create_type=False
        ), nullable=False, server_default='ORAL'),
        # Scheduling
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        # Administration
        sa.Column('administered_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('administered_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'ADMINISTERED', 'REFUSED', 'MISSED', 'HELD',
            name='med_admin_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Refusal documentation
        sa.Column('refusal_witnessed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for medication_administrations
    op.create_index('ix_med_admin_inmate', 'medication_administrations', ['inmate_id'])
    op.create_index('ix_med_admin_scheduled', 'medication_administrations', ['scheduled_time'])
    op.create_index('ix_med_admin_status', 'medication_administrations', ['status'])
    op.create_index('ix_med_admin_medication', 'medication_administrations', ['medication_name'])
    # Partial index for pending medications
    op.create_index(
        'ix_med_admin_pending',
        'medication_administrations',
        ['scheduled_time', 'status'],
        postgresql_where=sa.text("status = 'SCHEDULED'")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['medical_records', 'medical_encounters', 'medication_administrations']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['medication_administrations', 'medical_encounters', 'medical_records']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for medication_administrations
    op.drop_index('ix_med_admin_pending', 'medication_administrations')
    op.drop_index('ix_med_admin_medication', 'medication_administrations')
    op.drop_index('ix_med_admin_status', 'medication_administrations')
    op.drop_index('ix_med_admin_scheduled', 'medication_administrations')
    op.drop_index('ix_med_admin_inmate', 'medication_administrations')

    # Drop indexes for medical_encounters
    op.drop_index('ix_medical_encounters_external', 'medical_encounters')
    op.drop_index('ix_medical_encounters_follow_up', 'medical_encounters')
    op.drop_index('ix_medical_encounters_provider_type', 'medical_encounters')
    op.drop_index('ix_medical_encounters_type', 'medical_encounters')
    op.drop_index('ix_medical_encounters_date', 'medical_encounters')
    op.drop_index('ix_medical_encounters_inmate', 'medical_encounters')

    # Drop indexes for medical_records
    op.drop_index('ix_medical_records_next_physical', 'medical_records')
    op.drop_index('ix_medical_records_suicide_watch', 'medical_records')
    op.drop_index('ix_medical_records_mental_health', 'medical_records')
    op.drop_index('ix_medical_records_blood_type', 'medical_records')
    op.drop_index('ix_medical_records_inmate', 'medical_records')

    # Drop tables
    op.drop_table('medication_administrations')
    op.drop_table('medical_encounters')
    op.drop_table('medical_records')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS med_admin_status_enum")
    op.execute("DROP TYPE IF EXISTS route_type_enum")
    op.execute("DROP TYPE IF EXISTS provider_type_enum")
    op.execute("DROP TYPE IF EXISTS encounter_type_enum")
    op.execute("DROP TYPE IF EXISTS blood_type_enum")
