"""add_compliance_reporting_tables

Revision ID: n4i5j6k7l8m9
Revises: m3h4i5j6k7l8
Create Date: 2026-01-05

Creates aca_standards, compliance_audits, and audit_findings tables.
Creates aca_category_enum, audit_type_enum, audit_status_enum,
and compliance_status_enum.

Phase 4: ACA Compliance Reporting - Essential for maintaining accreditation.

Seeds 24 ACA standards covering all major categories.
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'n4i5j6k7l8m9'
down_revision: Union[str, None] = 'm3h4i5j6k7l8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create aca_category_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'aca_category_enum') THEN
                CREATE TYPE aca_category_enum AS ENUM (
                    'SAFETY',
                    'SECURITY',
                    'ORDER',
                    'CARE',
                    'PROGRAMS',
                    'JUSTICE',
                    'ADMINISTRATION',
                    'PHYSICAL_PLANT'
                );
            END IF;
        END$$;
    """)

    # Create audit_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_type_enum') THEN
                CREATE TYPE audit_type_enum AS ENUM (
                    'SELF_ASSESSMENT',
                    'MOCK',
                    'OFFICIAL'
                );
            END IF;
        END$$;
    """)

    # Create audit_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_status_enum') THEN
                CREATE TYPE audit_status_enum AS ENUM (
                    'SCHEDULED',
                    'IN_PROGRESS',
                    'COMPLETED',
                    'CANCELLED'
                );
            END IF;
        END$$;
    """)

    # Create compliance_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'compliance_status_enum') THEN
                CREATE TYPE compliance_status_enum AS ENUM (
                    'COMPLIANT',
                    'NON_COMPLIANT',
                    'PARTIAL',
                    'NOT_APPLICABLE'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create aca_standards table
    # ========================================================================
    op.create_table(
        'aca_standards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Standard identification
        sa.Column('standard_number', sa.String(20), unique=True, nullable=False),
        # Classification
        sa.Column('category', postgresql.ENUM(
            'SAFETY', 'SECURITY', 'ORDER', 'CARE', 'PROGRAMS',
            'JUSTICE', 'ADMINISTRATION', 'PHYSICAL_PLANT',
            name='aca_category_enum', create_type=False
        ), nullable=False),
        # Description
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        # Requirements
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='false'),
        # Evidence documentation
        sa.Column('evidence_required', postgresql.JSONB, nullable=True, server_default='[]'),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for aca_standards
    op.create_index('ix_aca_standards_number', 'aca_standards', ['standard_number'])
    op.create_index('ix_aca_standards_category', 'aca_standards', ['category'])
    op.create_index('ix_aca_standards_mandatory', 'aca_standards', ['is_mandatory'])

    # ========================================================================
    # Create compliance_audits table
    # ========================================================================
    op.create_table(
        'compliance_audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Audit details
        sa.Column('audit_date', sa.Date, nullable=False),
        sa.Column('auditor_name', sa.String(200), nullable=False),
        # Audit type
        sa.Column('audit_type', postgresql.ENUM(
            'SELF_ASSESSMENT', 'MOCK', 'OFFICIAL',
            name='audit_type_enum', create_type=False
        ), nullable=False),
        # Status
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED',
            name='audit_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Results
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('findings_summary', sa.Text, nullable=True),
        sa.Column('corrective_actions_required', sa.Integer, nullable=False, server_default='0'),
        # Next audit
        sa.Column('next_audit_date', sa.Date, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for compliance_audits
    op.create_index('ix_compliance_audits_date', 'compliance_audits', ['audit_date'])
    op.create_index('ix_compliance_audits_type', 'compliance_audits', ['audit_type'])
    op.create_index('ix_compliance_audits_status', 'compliance_audits', ['status'])

    # ========================================================================
    # Create audit_findings table
    # ========================================================================
    op.create_table(
        'audit_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # References
        sa.Column('audit_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_audits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('standard_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('aca_standards.id', ondelete='RESTRICT'), nullable=False),
        # Compliance status
        sa.Column('compliance_status', postgresql.ENUM(
            'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_APPLICABLE',
            name='compliance_status_enum', create_type=False
        ), nullable=False),
        # Evidence
        sa.Column('evidence_provided', sa.Text, nullable=True),
        # Findings
        sa.Column('finding_notes', sa.Text, nullable=True),
        # Corrective action
        sa.Column('corrective_action', sa.Text, nullable=True),
        sa.Column('corrective_action_due', sa.Date, nullable=True),
        sa.Column('corrective_action_completed', sa.Date, nullable=True),
        # Verification
        sa.Column('verified_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for audit_findings
    op.create_index('ix_audit_findings_audit', 'audit_findings', ['audit_id'])
    op.create_index('ix_audit_findings_standard', 'audit_findings', ['standard_id'])
    op.create_index('ix_audit_findings_status', 'audit_findings', ['compliance_status'])
    op.create_index('ix_audit_findings_due', 'audit_findings', ['corrective_action_due'])
    # Partial index for overdue corrective actions
    op.create_index(
        'ix_audit_findings_overdue',
        'audit_findings',
        ['corrective_action_due', 'corrective_action_completed'],
        postgresql_where=sa.text(
            "corrective_action_due IS NOT NULL AND corrective_action_completed IS NULL"
        )
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['aca_standards', 'compliance_audits', 'audit_findings']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)

    # ========================================================================
    # Seed ACA Standards (24 standards covering all categories)
    # ========================================================================
    seed_standards()


def seed_standards() -> None:
    """Seed essential ACA standards covering all categories."""

    standards = [
        # SAFETY (4 standards - Mandatory)
        {
            'standard_number': '4-4001',
            'category': 'SAFETY',
            'title': 'Emergency Plans',
            'description': 'The facility has written emergency plans that are reviewed annually and updated as needed. Plans cover fire, disturbances, escape, bomb threats, and natural disasters.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Written emergency plans'},
                {'type': 'record', 'description': 'Annual review documentation'},
                {'type': 'log', 'description': 'Drill records'}
            ]
        },
        {
            'standard_number': '4-4003',
            'category': 'SAFETY',
            'title': 'Fire Safety Inspections',
            'description': 'Fire safety inspections are conducted at least weekly by a trained staff member and annually by an authority with jurisdiction.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'record', 'description': 'Weekly inspection logs'},
                {'type': 'report', 'description': 'Annual fire authority inspection'}
            ]
        },
        {
            'standard_number': '4-4008',
            'category': 'SAFETY',
            'title': 'First Aid Training',
            'description': 'All staff who work in direct contact with inmates are trained in first aid and CPR.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'record', 'description': 'Staff training certificates'},
                {'type': 'log', 'description': 'Training completion records'}
            ]
        },

        # SECURITY (4 standards)
        {
            'standard_number': '4-4015',
            'category': 'SECURITY',
            'title': 'Inmate Count Procedures',
            'description': 'Written policy requires at least five inmate counts per 24 hours with at least one standing count.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Count procedures policy'},
                {'type': 'log', 'description': 'Count verification logs'}
            ]
        },
        {
            'standard_number': '4-4021',
            'category': 'SECURITY',
            'title': 'Key Control',
            'description': 'The facility has a comprehensive key control system with documented procedures.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Key control policy'},
                {'type': 'log', 'description': 'Key inventory records'}
            ]
        },
        {
            'standard_number': '4-4027',
            'category': 'SECURITY',
            'title': 'Tool Control',
            'description': 'There is a written policy and procedure for tool control that includes inventory, storage, and issuance.',
            'is_mandatory': False,
            'evidence_required': [
                {'type': 'policy', 'description': 'Tool control policy'},
                {'type': 'record', 'description': 'Tool inventory records'}
            ]
        },
        {
            'standard_number': '4-4033',
            'category': 'SECURITY',
            'title': 'Use of Force Policy',
            'description': 'Written policy governs the use of force and requires documentation and review of all incidents.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Use of force policy'},
                {'type': 'record', 'description': 'Use of force incident reports'}
            ]
        },

        # ORDER (3 standards)
        {
            'standard_number': '4-4044',
            'category': 'ORDER',
            'title': 'Rules of Conduct',
            'description': 'Written rules of inmate conduct specify acts prohibited and penalties that may be imposed.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Inmate rulebook'},
                {'type': 'record', 'description': 'Distribution acknowledgments'}
            ]
        },
        {
            'standard_number': '4-4049',
            'category': 'ORDER',
            'title': 'Disciplinary Procedures',
            'description': 'Written policy provides for a fair and impartial hearing for inmates charged with rule violations.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Disciplinary procedures'},
                {'type': 'record', 'description': 'Hearing documentation'}
            ]
        },
        {
            'standard_number': '4-4055',
            'category': 'ORDER',
            'title': 'Grievance Procedures',
            'description': 'A formal grievance procedure is available to all inmates with documented responses.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Grievance procedures'},
                {'type': 'log', 'description': 'Grievance tracking records'}
            ]
        },

        # CARE (4 standards)
        {
            'standard_number': '4-4061',
            'category': 'CARE',
            'title': 'Health Care Screening',
            'description': 'All inmates receive health screening upon arrival at the facility by a qualified health care professional.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Intake screening procedures'},
                {'type': 'record', 'description': 'Screening forms'}
            ]
        },
        {
            'standard_number': '4-4065',
            'category': 'CARE',
            'title': 'Mental Health Screening',
            'description': 'Inmates are screened for mental health needs within 14 days of admission.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Mental health screening policy'},
                {'type': 'record', 'description': 'Screening documentation'}
            ]
        },
        {
            'standard_number': '4-4071',
            'category': 'CARE',
            'title': 'Suicide Prevention',
            'description': 'The facility has a suicide prevention and intervention program that is reviewed annually.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Suicide prevention policy'},
                {'type': 'record', 'description': 'Staff training records'},
                {'type': 'log', 'description': 'Watch log documentation'}
            ]
        },
        {
            'standard_number': '4-4077',
            'category': 'CARE',
            'title': 'Food Service',
            'description': 'Inmates are provided three nutritionally adequate meals daily with at least two served hot.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'record', 'description': 'Menu records'},
                {'type': 'record', 'description': 'Food service inspection reports'}
            ]
        },

        # PROGRAMS (3 standards)
        {
            'standard_number': '4-4083',
            'category': 'PROGRAMS',
            'title': 'Educational Programs',
            'description': 'Educational programs are available to meet the needs of the inmate population.',
            'is_mandatory': False,
            'evidence_required': [
                {'type': 'record', 'description': 'Program curriculum'},
                {'type': 'log', 'description': 'Enrollment records'}
            ]
        },
        {
            'standard_number': '4-4087',
            'category': 'PROGRAMS',
            'title': 'Vocational Training',
            'description': 'Vocational training programs are available and lead to marketable skills.',
            'is_mandatory': False,
            'evidence_required': [
                {'type': 'record', 'description': 'Program descriptions'},
                {'type': 'record', 'description': 'Completion certificates'}
            ]
        },
        {
            'standard_number': '4-4093',
            'category': 'PROGRAMS',
            'title': 'Library Services',
            'description': 'Library services are available to all inmates with adequate materials.',
            'is_mandatory': False,
            'evidence_required': [
                {'type': 'record', 'description': 'Library inventory'},
                {'type': 'log', 'description': 'Usage records'}
            ]
        },

        # JUSTICE (2 standards)
        {
            'standard_number': '4-4101',
            'category': 'JUSTICE',
            'title': 'Access to Courts',
            'description': 'Inmates have access to courts and are provided with materials and assistance.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Legal access policy'},
                {'type': 'record', 'description': 'Law library materials'}
            ]
        },
        {
            'standard_number': '4-4107',
            'category': 'JUSTICE',
            'title': 'Visitation',
            'description': 'Written policy provides for inmate visitation and is available to both visitors and inmates.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Visitation policy'},
                {'type': 'log', 'description': 'Visitor logs'}
            ]
        },

        # ADMINISTRATION (2 standards)
        {
            'standard_number': '4-4115',
            'category': 'ADMINISTRATION',
            'title': 'Staff Training',
            'description': 'All new employees receive at least 40 hours of orientation training during their first year.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'policy', 'description': 'Training policy'},
                {'type': 'record', 'description': 'Training completion records'}
            ]
        },
        {
            'standard_number': '4-4121',
            'category': 'ADMINISTRATION',
            'title': 'Policy Manual',
            'description': 'A comprehensive policy manual is available to all staff and reviewed annually.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'record', 'description': 'Policy manual'},
                {'type': 'record', 'description': 'Annual review documentation'}
            ]
        },

        # PHYSICAL_PLANT (2 standards)
        {
            'standard_number': '4-4131',
            'category': 'PHYSICAL_PLANT',
            'title': 'Living Space',
            'description': 'Inmates are provided with a minimum of 60 square feet of floor space in single cells.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'record', 'description': 'Facility floor plans'},
                {'type': 'record', 'description': 'Capacity calculations'}
            ]
        },
        {
            'standard_number': '4-4137',
            'category': 'PHYSICAL_PLANT',
            'title': 'Sanitation',
            'description': 'The facility is maintained in a clean and sanitary condition with documented inspections.',
            'is_mandatory': True,
            'evidence_required': [
                {'type': 'log', 'description': 'Sanitation inspection logs'},
                {'type': 'record', 'description': 'Cleaning schedules'}
            ]
        },
    ]

    # Insert standards
    for std in standards:
        std_id = str(uuid4())
        evidence = str(std['evidence_required']).replace("'", '"')  # Convert to JSON format

        op.execute(f"""
            INSERT INTO aca_standards (
                id, standard_number, category, title, description,
                is_mandatory, evidence_required, inserted_by
            ) VALUES (
                '{std_id}',
                '{std['standard_number']}',
                '{std['category']}',
                '{std['title'].replace("'", "''")}',
                '{std['description'].replace("'", "''")}',
                {str(std['is_mandatory']).lower()},
                '{evidence}'::jsonb,
                'system_seed'
            )
            ON CONFLICT (standard_number) DO NOTHING;
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['audit_findings', 'compliance_audits', 'aca_standards']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for audit_findings
    op.drop_index('ix_audit_findings_overdue', 'audit_findings')
    op.drop_index('ix_audit_findings_due', 'audit_findings')
    op.drop_index('ix_audit_findings_status', 'audit_findings')
    op.drop_index('ix_audit_findings_standard', 'audit_findings')
    op.drop_index('ix_audit_findings_audit', 'audit_findings')

    # Drop indexes for compliance_audits
    op.drop_index('ix_compliance_audits_status', 'compliance_audits')
    op.drop_index('ix_compliance_audits_type', 'compliance_audits')
    op.drop_index('ix_compliance_audits_date', 'compliance_audits')

    # Drop indexes for aca_standards
    op.drop_index('ix_aca_standards_mandatory', 'aca_standards')
    op.drop_index('ix_aca_standards_category', 'aca_standards')
    op.drop_index('ix_aca_standards_number', 'aca_standards')

    # Drop tables
    op.drop_table('audit_findings')
    op.drop_table('compliance_audits')
    op.drop_table('aca_standards')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS compliance_status_enum")
    op.execute("DROP TYPE IF EXISTS audit_status_enum")
    op.execute("DROP TYPE IF EXISTS audit_type_enum")
    op.execute("DROP TYPE IF EXISTS aca_category_enum")
