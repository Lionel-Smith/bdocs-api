"""add_btvi_certifications

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-01-05

Creates btvi_certifications table and related enums.
Seeds 9 BTVI vocational programme types.

BTVI (Bahamas Technical and Vocational Institute) provides
industry-recognized certifications for rehabilitation.
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create btvi_cert_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'btvi_cert_type_enum') THEN
                CREATE TYPE btvi_cert_type_enum AS ENUM (
                    'AUTOMOTIVE',
                    'ELECTRICAL',
                    'PLUMBING',
                    'CARPENTRY',
                    'WELDING',
                    'CULINARY',
                    'COSMETOLOGY',
                    'HVAC',
                    'MASONRY'
                );
            END IF;
        END$$;
    """)

    # Create skill_level_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'skill_level_enum') THEN
                CREATE TYPE skill_level_enum AS ENUM (
                    'BASIC',
                    'INTERMEDIATE',
                    'ADVANCED',
                    'MASTER'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create btvi_certifications table
    # ========================================================================
    op.create_table(
        'btvi_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('programme_enrollment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('programme_enrollments.id', ondelete='SET NULL'), nullable=True),
        # Certification identification
        sa.Column('certification_number', sa.String(20), unique=True, nullable=False),
        # Certification type
        sa.Column('certification_type', postgresql.ENUM(
            'AUTOMOTIVE', 'ELECTRICAL', 'PLUMBING', 'CARPENTRY',
            'WELDING', 'CULINARY', 'COSMETOLOGY', 'HVAC', 'MASONRY',
            name='btvi_cert_type_enum', create_type=False
        ), nullable=False),
        # Dates
        sa.Column('issued_date', sa.Date, nullable=False),
        sa.Column('expiry_date', sa.Date, nullable=True),
        # Issuing authority
        sa.Column('issuing_authority', sa.String(200), nullable=False,
                  server_default='Bahamas Technical and Vocational Institute (BTVI)'),
        # Skill level
        sa.Column('skill_level', postgresql.ENUM(
            'BASIC', 'INTERMEDIATE', 'ADVANCED', 'MASTER',
            name='skill_level_enum', create_type=False
        ), nullable=False),
        # Training details
        sa.Column('hours_training', sa.Integer, nullable=False),
        sa.Column('assessment_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('instructor_name', sa.String(200), nullable=False),
        # Verification
        sa.Column('verification_url', sa.String(500), nullable=True),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
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

    # Indexes for btvi_certifications
    op.create_index('ix_btvi_certifications_inmate', 'btvi_certifications', ['inmate_id'])
    op.create_index('ix_btvi_certifications_enrollment', 'btvi_certifications', ['programme_enrollment_id'])
    op.create_index('ix_btvi_certifications_number', 'btvi_certifications', ['certification_number'])
    op.create_index('ix_btvi_certifications_type', 'btvi_certifications', ['certification_type'])
    op.create_index('ix_btvi_certifications_level', 'btvi_certifications', ['skill_level'])
    op.create_index('ix_btvi_certifications_issued', 'btvi_certifications', ['issued_date'])
    op.create_index('ix_btvi_certifications_verified', 'btvi_certifications', ['is_verified'])
    op.create_index('ix_btvi_certifications_type_level', 'btvi_certifications',
                    ['certification_type', 'skill_level'])

    # ========================================================================
    # Attach audit trigger
    # ========================================================================
    op.execute("""
        DROP TRIGGER IF EXISTS btvi_certifications_audit_trigger ON btvi_certifications;
        CREATE TRIGGER btvi_certifications_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON btvi_certifications
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)

    # ========================================================================
    # Seed 9 BTVI Programme Types
    # ========================================================================
    # Insert programmes for each BTVI certification type
    btvi_programmes = [
        {
            'code': 'BTVI-AUTO-001',
            'name': 'BTVI Automotive Technology',
            'description': 'Comprehensive automotive repair and maintenance training including engine diagnostics, brake systems, electrical systems, and vehicle inspection. Prepares inmates for ASE certification.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 16,
            'max_participants': 15,
        },
        {
            'code': 'BTVI-ELEC-001',
            'name': 'BTVI Electrical Installation',
            'description': 'Residential and commercial electrical installation training including wiring, circuit design, safety codes, and troubleshooting. Aligns with Bahamas Electrical Contractors Association standards.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 20,
            'max_participants': 12,
        },
        {
            'code': 'BTVI-PLMB-001',
            'name': 'BTVI Plumbing Technology',
            'description': 'Plumbing installation and repair training covering pipe fitting, fixture installation, water systems, and building codes. Includes both residential and light commercial applications.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 14,
            'max_participants': 12,
        },
        {
            'code': 'BTVI-CARP-001',
            'name': 'BTVI Carpentry & Joinery',
            'description': 'Wood construction and cabinetry training including framing, finishing, furniture making, and blueprint reading. Emphasizes hurricane-resistant construction techniques for The Bahamas.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 16,
            'max_participants': 15,
        },
        {
            'code': 'BTVI-WELD-001',
            'name': 'BTVI Welding Technology',
            'description': 'Metal welding and fabrication training including MIG, TIG, and stick welding processes. Covers structural welding, pipe welding, and metal fabrication. AWS certification preparation.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 12,
            'max_participants': 10,
        },
        {
            'code': 'BTVI-CULN-001',
            'name': 'BTVI Culinary Arts',
            'description': 'Professional food preparation and kitchen management training including cooking techniques, food safety, menu planning, and cost control. ServSafe certification included.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 12,
            'max_participants': 12,
        },
        {
            'code': 'BTVI-COSM-001',
            'name': 'BTVI Cosmetology',
            'description': 'Hair styling and beauty services training including cutting, coloring, chemical treatments, and salon management. Prepares for Bahamas Cosmetology Board licensing.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 24,
            'max_participants': 10,
        },
        {
            'code': 'BTVI-HVAC-001',
            'name': 'BTVI HVAC Technology',
            'description': 'Heating, ventilation, and air conditioning training critical for The Bahamas climate. Covers installation, maintenance, refrigerant handling, and energy efficiency. EPA 608 certification preparation.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 16,
            'max_participants': 12,
        },
        {
            'code': 'BTVI-MASN-001',
            'name': 'BTVI Masonry & Concrete',
            'description': 'Block and brick laying, concrete work, and construction techniques. Covers foundations, walls, decorative masonry, and reinforcement. Essential skills for Bahamian construction industry.',
            'category': 'VOCATIONAL',
            'provider': 'Bahamas Technical and Vocational Institute (BTVI)',
            'duration_weeks': 14,
            'max_participants': 15,
        },
    ]

    # Insert each programme
    for prog in btvi_programmes:
        prog_id = str(uuid.uuid4())
        op.execute(f"""
            INSERT INTO programmes (
                id, code, name, description, category, provider,
                duration_weeks, max_participants, is_active, is_deleted,
                inserted_date
            ) VALUES (
                '{prog_id}',
                '{prog['code']}',
                '{prog['name']}',
                '{prog['description'].replace("'", "''")}',
                '{prog['category']}',
                '{prog['provider']}',
                {prog['duration_weeks']},
                {prog['max_participants']},
                true,
                false,
                NOW()
            )
            ON CONFLICT (code) DO NOTHING;
        """)


def downgrade() -> None:
    # Delete seeded programmes
    op.execute("""
        DELETE FROM programmes WHERE code LIKE 'BTVI-%';
    """)

    # Drop audit trigger
    op.execute("DROP TRIGGER IF EXISTS btvi_certifications_audit_trigger ON btvi_certifications")

    # Drop indexes
    op.drop_index('ix_btvi_certifications_type_level', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_verified', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_issued', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_level', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_type', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_number', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_enrollment', 'btvi_certifications')
    op.drop_index('ix_btvi_certifications_inmate', 'btvi_certifications')

    # Drop table
    op.drop_table('btvi_certifications')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS skill_level_enum")
    op.execute("DROP TYPE IF EXISTS btvi_cert_type_enum")
