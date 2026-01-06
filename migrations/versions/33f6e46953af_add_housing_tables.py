"""add_housing_tables

Revision ID: 33f6e46953af
Revises: eb30eeec74ef
Create Date: 2026-01-05

Creates housing_units, classifications, and housing_assignments tables.
Seeds 11 Fox Hill Correctional Facility housing units.
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '33f6e46953af'
down_revision: Union[str, None] = 'eb30eeec74ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fox Hill Correctional Facility Housing Units Seed Data
FOX_HILL_UNITS = [
    # Maximum Security
    {"code": "MAX-A", "name": "Maximum Security Block A", "security_level": "MAXIMUM", "capacity": 120, "gender": "MALE"},
    {"code": "MAX-B", "name": "Maximum Security Block B", "security_level": "MAXIMUM", "capacity": 120, "gender": "MALE"},
    {"code": "MAX-C", "name": "Maximum Security Block C", "security_level": "MAXIMUM", "capacity": 100, "gender": "MALE"},
    # Medium Security
    {"code": "MED-A", "name": "Medium Security Block A", "security_level": "MEDIUM", "capacity": 150, "gender": "MALE"},
    {"code": "MED-B", "name": "Medium Security Block B", "security_level": "MEDIUM", "capacity": 150, "gender": "MALE"},
    {"code": "MED-C", "name": "Medium Security Block C", "security_level": "MEDIUM", "capacity": 150, "gender": "MALE"},
    # Minimum Security
    {"code": "MIN-A", "name": "Minimum Security Block A", "security_level": "MINIMUM", "capacity": 100, "gender": "MALE"},
    {"code": "MIN-B", "name": "Minimum Security Block B", "security_level": "MINIMUM", "capacity": 100, "gender": "MALE"},
    # Female Unit
    {"code": "FEM-1", "name": "Female Detention Unit", "security_level": "MEDIUM", "capacity": 50, "gender": "FEMALE"},
    # Remand (Pre-trial)
    {"code": "REM-1", "name": "Remand Detention Unit", "security_level": "MEDIUM", "capacity": 200, "gender": None},
    # Juvenile
    {"code": "JUV-1", "name": "Juvenile Detention Unit", "security_level": "MEDIUM", "capacity": 30, "gender": None, "is_juvenile": True},
]


def upgrade() -> None:
    # ========================================================================
    # Create housing_units table
    # ========================================================================
    op.create_table(
        'housing_units',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(10), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('security_level', postgresql.ENUM('MAXIMUM', 'MEDIUM', 'MINIMUM', name='security_level_enum', create_type=False), nullable=False),
        sa.Column('capacity', sa.Integer, nullable=False),
        sa.Column('current_occupancy', sa.Integer, nullable=False, server_default='0'),
        sa.Column('gender_restriction', postgresql.ENUM('MALE', 'FEMALE', name='gender_enum', create_type=False), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_juvenile', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('description', sa.Text, nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_housing_units_code', 'housing_units', ['code'])
    op.create_index('ix_housing_units_security', 'housing_units', ['security_level'])
    op.create_index('ix_housing_units_active', 'housing_units', ['is_active'])

    # ========================================================================
    # Create classifications table
    # ========================================================================
    op.create_table(
        'classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('classification_date', sa.Date, nullable=False),
        sa.Column('security_level', postgresql.ENUM('MAXIMUM', 'MEDIUM', 'MINIMUM', name='security_level_enum', create_type=False), nullable=False),
        sa.Column('scores', postgresql.JSONB, nullable=False),
        sa.Column('total_score', sa.Integer, nullable=False),
        sa.Column('review_date', sa.Date, nullable=True),
        sa.Column('classified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        # Soft delete
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(100), nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_classifications_inmate', 'classifications', ['inmate_id'])
    op.create_index('ix_classifications_current', 'classifications', ['inmate_id', 'is_current'])
    op.create_index('ix_classifications_review', 'classifications', ['review_date'])

    # ========================================================================
    # Create housing_assignments table
    # ========================================================================
    op.create_table(
        'housing_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inmate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inmates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('housing_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('housing_units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cell_number', sa.String(20), nullable=True),
        sa.Column('bed_number', sa.String(10), nullable=True),
        sa.Column('assigned_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.String(500), nullable=True),
        # Soft delete
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(100), nullable=True),
        # Audit fields
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_housing_assignments_inmate', 'housing_assignments', ['inmate_id'])
    op.create_index('ix_housing_assignments_unit', 'housing_assignments', ['housing_unit_id'])
    op.create_index('ix_housing_assignments_current', 'housing_assignments', ['inmate_id', 'is_current'])
    op.create_index('ix_housing_assignments_dates', 'housing_assignments', ['assigned_date', 'end_date'])

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['housing_units', 'classifications', 'housing_assignments']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)

    # ========================================================================
    # Seed Fox Hill Housing Units
    # ========================================================================
    for unit in FOX_HILL_UNITS:
        unit_id = str(uuid.uuid4())
        gender = f"'{unit['gender']}'" if unit.get('gender') else 'NULL'
        is_juvenile = 'true' if unit.get('is_juvenile') else 'false'

        op.execute(f"""
            INSERT INTO housing_units (id, code, name, security_level, capacity, current_occupancy, gender_restriction, is_active, is_juvenile, inserted_by)
            VALUES (
                '{unit_id}',
                '{unit['code']}',
                '{unit['name']}',
                '{unit['security_level']}',
                {unit['capacity']},
                0,
                {gender},
                true,
                {is_juvenile},
                'system'
            );
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['housing_assignments', 'classifications', 'housing_units']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes
    op.drop_index('ix_housing_assignments_dates', 'housing_assignments')
    op.drop_index('ix_housing_assignments_current', 'housing_assignments')
    op.drop_index('ix_housing_assignments_unit', 'housing_assignments')
    op.drop_index('ix_housing_assignments_inmate', 'housing_assignments')

    op.drop_index('ix_classifications_review', 'classifications')
    op.drop_index('ix_classifications_current', 'classifications')
    op.drop_index('ix_classifications_inmate', 'classifications')

    op.drop_index('ix_housing_units_active', 'housing_units')
    op.drop_index('ix_housing_units_security', 'housing_units')
    op.drop_index('ix_housing_units_code', 'housing_units')

    # Drop tables (order matters due to FKs)
    op.drop_table('housing_assignments')
    op.drop_table('classifications')
    op.drop_table('housing_units')
