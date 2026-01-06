"""add_reports_tables

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2026-01-05

Creates report_definitions and report_executions tables for the Reports module.
Creates report_category_enum, output_format_enum, and report_status_enum.
Seeds 10 standard report definitions for population, incident, programme, and ACA reports.

Phase 5: Reports Module - Comprehensive reporting framework.
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p6k7l8m9n0o1'
down_revision: Union[str, None] = 'o5j6k7l8m9n0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create report_category_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_category_enum') THEN
                CREATE TYPE report_category_enum AS ENUM (
                    'POPULATION',
                    'INCIDENT',
                    'PROGRAMME',
                    'HEALTHCARE',
                    'COMPLIANCE',
                    'FINANCIAL',
                    'OPERATIONAL'
                );
            END IF;
        END$$;
    """)

    # Create output_format_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'output_format_enum') THEN
                CREATE TYPE output_format_enum AS ENUM (
                    'PDF',
                    'EXCEL',
                    'CSV',
                    'JSON'
                );
            END IF;
        END$$;
    """)

    # Create report_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_status_enum') THEN
                CREATE TYPE report_status_enum AS ENUM (
                    'QUEUED',
                    'GENERATING',
                    'COMPLETED',
                    'FAILED'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create report_definitions table
    # ========================================================================
    op.create_table(
        'report_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Report identification
        sa.Column('code', sa.String(20), unique=True, nullable=False,
                  comment="Unique report code (e.g., 'RPT-POP-001')"),
        sa.Column('name', sa.String(200), nullable=False,
                  comment="Human-readable report name"),
        sa.Column('description', sa.Text, nullable=True,
                  comment="Detailed description of report contents"),
        # Classification
        sa.Column('category', postgresql.ENUM(
            'POPULATION', 'INCIDENT', 'PROGRAMME', 'HEALTHCARE',
            'COMPLIANCE', 'FINANCIAL', 'OPERATIONAL',
            name='report_category_enum', create_type=False
        ), nullable=False, comment="Report category for organization"),
        # Parameters schema
        sa.Column('parameters_schema', postgresql.JSONB, nullable=True,
                  comment="JSON Schema defining required/optional parameters"),
        # Output configuration
        sa.Column('output_format', postgresql.ENUM(
            'PDF', 'EXCEL', 'CSV', 'JSON',
            name='output_format_enum', create_type=False
        ), nullable=False, server_default='PDF',
                  comment="Default output format for this report"),
        # Scheduling
        sa.Column('is_scheduled', sa.Boolean, nullable=False, server_default='false',
                  comment="Whether this report runs on a schedule"),
        sa.Column('schedule_cron', sa.String(50), nullable=True,
                  comment="Cron expression for scheduled reports"),
        # Tracking
        sa.Column('last_generated', sa.DateTime(timezone=True), nullable=True,
                  comment="When this report was last successfully generated"),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for report_definitions
    op.create_index('ix_report_definitions_code', 'report_definitions', ['code'])
    op.create_index('ix_report_definitions_category', 'report_definitions', ['category'])
    op.create_index('ix_report_definitions_scheduled', 'report_definitions', ['is_scheduled'])

    # ========================================================================
    # Create report_executions table
    # ========================================================================
    op.create_table(
        'report_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Reference to definition
        sa.Column('report_definition_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('report_definitions.id', ondelete='CASCADE'), nullable=False),
        # Parameters used
        sa.Column('parameters', postgresql.JSONB, nullable=True,
                  comment="Parameters used for this execution"),
        # Status tracking
        sa.Column('status', postgresql.ENUM(
            'QUEUED', 'GENERATING', 'COMPLETED', 'FAILED',
            name='report_status_enum', create_type=False
        ), nullable=False, server_default='QUEUED'),
        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False,
                  comment="When execution started"),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True,
                  comment="When execution completed (success or failure)"),
        # Output file
        sa.Column('file_path', sa.String(500), nullable=True,
                  comment="Path to generated report file"),
        sa.Column('file_size_bytes', sa.Integer, nullable=True,
                  comment="Size of generated file in bytes"),
        # Error tracking
        sa.Column('error_message', sa.Text, nullable=True,
                  comment="Error message if generation failed"),
        # Requested by
        sa.Column('requested_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for report_executions
    op.create_index('ix_report_executions_definition', 'report_executions', ['report_definition_id'])
    op.create_index('ix_report_executions_status', 'report_executions', ['status'])
    op.create_index('ix_report_executions_started', 'report_executions', ['started_at'])
    op.create_index('ix_report_executions_requested', 'report_executions', ['requested_by'])

    # Partial index for active executions (QUEUED or GENERATING)
    op.create_index(
        'ix_report_executions_active',
        'report_executions',
        ['status', 'started_at'],
        postgresql_where=sa.text("status IN ('QUEUED', 'GENERATING')")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    op.execute("""
        DROP TRIGGER IF EXISTS report_definitions_audit_trigger ON report_definitions;
        CREATE TRIGGER report_definitions_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON report_definitions
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS report_executions_audit_trigger ON report_executions;
        CREATE TRIGGER report_executions_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON report_executions
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)

    # ========================================================================
    # Seed report definitions (10 standard reports)
    # ========================================================================

    # Use system user UUID for created_by
    system_user_id = '00000000-0000-0000-0000-000000000001'

    # Population Reports (4)
    reports = [
        {
            'id': str(uuid4()),
            'code': 'RPT-POP-001',
            'name': 'Daily Population Summary',
            'description': 'Daily snapshot of total population with breakdown by status, security level, housing unit, and demographics.',
            'category': 'POPULATION',
            'output_format': 'PDF',
            'is_scheduled': True,
            'schedule_cron': '0 6 * * *',  # Daily at 6 AM
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'as_of_date': {'type': 'string', 'format': 'date'},
                    'facility_id': {'type': 'string', 'format': 'uuid'}
                }
            }
        },
        {
            'id': str(uuid4()),
            'code': 'RPT-POP-002',
            'name': 'Population by Security Level',
            'description': 'Detailed breakdown of population by security classification with historical trends.',
            'category': 'POPULATION',
            'output_format': 'EXCEL',
            'is_scheduled': False,
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'as_of_date': {'type': 'string', 'format': 'date'},
                    'include_trends': {'type': 'boolean', 'default': True}
                }
            }
        },
        {
            'id': str(uuid4()),
            'code': 'RPT-POP-003',
            'name': 'Housing Unit Occupancy',
            'description': 'Current occupancy by housing unit with capacity utilization metrics.',
            'category': 'POPULATION',
            'output_format': 'PDF',
            'is_scheduled': False,
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'as_of_date': {'type': 'string', 'format': 'date'}
                }
            }
        },
        # Incident Reports (2)
        {
            'id': str(uuid4()),
            'code': 'RPT-INC-001',
            'name': 'Incident Summary Report',
            'description': 'Summary of incidents within a date range by type, severity, and status.',
            'category': 'INCIDENT',
            'output_format': 'PDF',
            'is_scheduled': True,
            'schedule_cron': '0 7 * * 1',  # Weekly on Monday at 7 AM
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'severity_filter': {'type': 'array', 'items': {'type': 'string'}}
                },
                'required': ['start_date', 'end_date']
            }
        },
        {
            'id': str(uuid4()),
            'code': 'RPT-INC-002',
            'name': 'Incident Detail Report',
            'description': 'Detailed incident information including participants, actions taken, and outcomes.',
            'category': 'INCIDENT',
            'output_format': 'EXCEL',
            'is_scheduled': False,
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'include_details': {'type': 'boolean', 'default': True}
                },
                'required': ['start_date', 'end_date']
            }
        },
        # Programme Reports (2)
        {
            'id': str(uuid4()),
            'code': 'RPT-PRG-001',
            'name': 'Programme Enrollment Summary',
            'description': 'Overview of programme enrollment, completion rates, and participant demographics.',
            'category': 'PROGRAMME',
            'output_format': 'PDF',
            'is_scheduled': True,
            'schedule_cron': '0 8 1 * *',  # Monthly on 1st at 8 AM
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'programme_type': {'type': 'string'}
                }
            }
        },
        {
            'id': str(uuid4()),
            'code': 'RPT-PRG-002',
            'name': 'BTVI Certification Report',
            'description': 'Report on BTVI vocational certifications awarded, by programme and time period.',
            'category': 'PROGRAMME',
            'output_format': 'EXCEL',
            'is_scheduled': False,
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'certification_type': {'type': 'string'}
                }
            }
        },
        # ACA Compliance Reports (2)
        {
            'id': str(uuid4()),
            'code': 'RPT-ACA-001',
            'name': 'ACA Compliance Summary',
            'description': 'Overall ACA compliance status with scores by category and outstanding findings.',
            'category': 'COMPLIANCE',
            'output_format': 'PDF',
            'is_scheduled': False,
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'audit_id': {'type': 'string', 'format': 'uuid'},
                    'include_findings': {'type': 'boolean', 'default': True}
                }
            }
        },
        {
            'id': str(uuid4()),
            'code': 'RPT-ACA-002',
            'name': 'Corrective Actions Status',
            'description': 'Status of all corrective actions with due dates and responsible parties.',
            'category': 'COMPLIANCE',
            'output_format': 'EXCEL',
            'is_scheduled': True,
            'schedule_cron': '0 9 * * 5',  # Weekly on Friday at 9 AM
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'status_filter': {'type': 'array', 'items': {'type': 'string'}},
                    'include_overdue_only': {'type': 'boolean', 'default': False}
                }
            }
        },
        # Operational Report (1)
        {
            'id': str(uuid4()),
            'code': 'RPT-OPS-001',
            'name': 'Daily Operations Summary',
            'description': 'Combined daily summary including population, incidents, and key metrics.',
            'category': 'OPERATIONAL',
            'output_format': 'PDF',
            'is_scheduled': True,
            'schedule_cron': '0 6 * * *',  # Daily at 6 AM
            'parameters_schema': {
                'type': 'object',
                'properties': {
                    'as_of_date': {'type': 'string', 'format': 'date'}
                }
            }
        },
    ]

    for report in reports:
        params_json = str(report.get('parameters_schema', {})).replace("'", "''")
        schedule = f"'{report['schedule_cron']}'" if report.get('schedule_cron') else 'NULL'

        op.execute(f"""
            INSERT INTO report_definitions (
                id, code, name, description, category, parameters_schema,
                output_format, is_scheduled, schedule_cron, created_by,
                inserted_by, inserted_date
            ) VALUES (
                '{report['id']}',
                '{report['code']}',
                '{report['name'].replace("'", "''")}',
                '{report['description'].replace("'", "''")}',
                '{report['category']}',
                '{params_json}'::jsonb,
                '{report['output_format']}',
                {str(report['is_scheduled']).lower()},
                {schedule},
                '{system_user_id}',
                'migration',
                NOW()
            );
        """)


def downgrade() -> None:
    # Drop audit triggers
    op.execute("DROP TRIGGER IF EXISTS report_executions_audit_trigger ON report_executions")
    op.execute("DROP TRIGGER IF EXISTS report_definitions_audit_trigger ON report_definitions")

    # Drop indexes
    op.drop_index('ix_report_executions_active', 'report_executions')
    op.drop_index('ix_report_executions_requested', 'report_executions')
    op.drop_index('ix_report_executions_started', 'report_executions')
    op.drop_index('ix_report_executions_status', 'report_executions')
    op.drop_index('ix_report_executions_definition', 'report_executions')
    op.drop_index('ix_report_definitions_scheduled', 'report_definitions')
    op.drop_index('ix_report_definitions_category', 'report_definitions')
    op.drop_index('ix_report_definitions_code', 'report_definitions')

    # Drop tables
    op.drop_table('report_executions')
    op.drop_table('report_definitions')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS report_status_enum")
    op.execute("DROP TYPE IF EXISTS output_format_enum")
    op.execute("DROP TYPE IF EXISTS report_category_enum")
