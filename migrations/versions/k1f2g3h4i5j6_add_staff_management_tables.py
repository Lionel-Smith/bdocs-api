"""add_staff_management_tables

Revision ID: k1f2g3h4i5j6
Revises: j0e1f2g3h4i5
Create Date: 2026-01-05

Creates staff, staff_shifts, and staff_training tables.
Creates staff_rank_enum, department_enum, staff_status_enum,
shift_type_enum, shift_status_enum, and training_type_enum.

Phase 3: Operations & Security - Staff Management.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k1f2g3h4i5j6'
down_revision: Union[str, None] = 'j0e1f2g3h4i5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # Create PostgreSQL ENUM types
    # ========================================================================

    # Create staff_rank_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'staff_rank_enum') THEN
                CREATE TYPE staff_rank_enum AS ENUM (
                    'SUPERINTENDENT',
                    'DEPUTY_SUPERINTENDENT',
                    'ASSISTANT_SUPERINTENDENT',
                    'CHIEF_OFFICER',
                    'SENIOR_OFFICER',
                    'OFFICER',
                    'RECRUIT'
                );
            END IF;
        END$$;
    """)

    # Create department_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'department_enum') THEN
                CREATE TYPE department_enum AS ENUM (
                    'ADMINISTRATION',
                    'SECURITY',
                    'PROGRAMMES',
                    'MEDICAL',
                    'RECORDS',
                    'MAINTENANCE',
                    'KITCHEN'
                );
            END IF;
        END$$;
    """)

    # Create staff_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'staff_status_enum') THEN
                CREATE TYPE staff_status_enum AS ENUM (
                    'ACTIVE',
                    'ON_LEAVE',
                    'SUSPENDED',
                    'TERMINATED'
                );
            END IF;
        END$$;
    """)

    # Create shift_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shift_type_enum') THEN
                CREATE TYPE shift_type_enum AS ENUM (
                    'DAY',
                    'EVENING',
                    'NIGHT'
                );
            END IF;
        END$$;
    """)

    # Create shift_status_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shift_status_enum') THEN
                CREATE TYPE shift_status_enum AS ENUM (
                    'SCHEDULED',
                    'IN_PROGRESS',
                    'COMPLETED',
                    'ABSENT',
                    'SWAPPED'
                );
            END IF;
        END$$;
    """)

    # Create training_type_enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'training_type_enum') THEN
                CREATE TYPE training_type_enum AS ENUM (
                    'ORIENTATION',
                    'USE_OF_FORCE',
                    'FIRST_AID',
                    'CPR',
                    'FIREARMS',
                    'CRISIS_INTERVENTION',
                    'ACA_STANDARDS',
                    'DEFENSIVE_TACTICS'
                );
            END IF;
        END$$;
    """)

    # ========================================================================
    # Create staff table
    # ========================================================================
    op.create_table(
        'staff',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Link to auth users
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), unique=True, nullable=False),
        # Employee identification
        sa.Column('employee_number', sa.String(10), unique=True, nullable=False),
        # Personal information
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        # Position
        sa.Column('rank', postgresql.ENUM(
            'SUPERINTENDENT', 'DEPUTY_SUPERINTENDENT', 'ASSISTANT_SUPERINTENDENT',
            'CHIEF_OFFICER', 'SENIOR_OFFICER', 'OFFICER', 'RECRUIT',
            name='staff_rank_enum', create_type=False
        ), nullable=False, server_default='OFFICER'),
        sa.Column('department', postgresql.ENUM(
            'ADMINISTRATION', 'SECURITY', 'PROGRAMMES', 'MEDICAL',
            'RECORDS', 'MAINTENANCE', 'KITCHEN',
            name='department_enum', create_type=False
        ), nullable=False, server_default='SECURITY'),
        # Employment
        sa.Column('hire_date', sa.Date, nullable=False),
        sa.Column('status', postgresql.ENUM(
            'ACTIVE', 'ON_LEAVE', 'SUSPENDED', 'TERMINATED',
            name='staff_status_enum', create_type=False
        ), nullable=False, server_default='ACTIVE'),
        # Contact
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        # Certifications
        sa.Column('certifications', postgresql.JSONB, nullable=True, server_default='[]'),
        # Active flag
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
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

    # Indexes for staff
    op.create_index('ix_staff_employee_number', 'staff', ['employee_number'])
    op.create_index('ix_staff_user_id', 'staff', ['user_id'])
    op.create_index('ix_staff_name', 'staff', ['last_name', 'first_name'])
    op.create_index('ix_staff_rank', 'staff', ['rank'])
    op.create_index('ix_staff_department', 'staff', ['department'])
    op.create_index('ix_staff_status', 'staff', ['status'])
    op.create_index('ix_staff_active', 'staff', ['is_active'])

    # ========================================================================
    # Create staff_shifts table
    # ========================================================================
    op.create_table(
        'staff_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Staff assignment
        sa.Column('staff_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        # Shift date and type
        sa.Column('shift_date', sa.Date, nullable=False),
        sa.Column('shift_type', postgresql.ENUM(
            'DAY', 'EVENING', 'NIGHT',
            name='shift_type_enum', create_type=False
        ), nullable=False),
        # Shift times
        sa.Column('start_time', sa.Time, nullable=False),
        sa.Column('end_time', sa.Time, nullable=False),
        # Post assignment
        sa.Column('housing_unit_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('housing_units.id', ondelete='SET NULL'), nullable=True),
        # Status
        sa.Column('status', postgresql.ENUM(
            'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'ABSENT', 'SWAPPED',
            name='shift_status_enum', create_type=False
        ), nullable=False, server_default='SCHEDULED'),
        # Notes
        sa.Column('notes', sa.Text, nullable=True),
        # Created by
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('staff.id', ondelete='RESTRICT'), nullable=False),
        # Audit fields (no soft delete for shifts)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for staff_shifts
    op.create_index('ix_staff_shifts_staff', 'staff_shifts', ['staff_id'])
    op.create_index('ix_staff_shifts_date', 'staff_shifts', ['shift_date'])
    op.create_index('ix_staff_shifts_type', 'staff_shifts', ['shift_type'])
    op.create_index('ix_staff_shifts_status', 'staff_shifts', ['status'])
    op.create_index('ix_staff_shifts_housing', 'staff_shifts', ['housing_unit_id'])
    op.create_index('ix_staff_shifts_schedule', 'staff_shifts', ['shift_date', 'shift_type', 'status'])
    op.create_index('ix_staff_shifts_created_by', 'staff_shifts', ['created_by'])

    # ========================================================================
    # Create staff_training table
    # ========================================================================
    op.create_table(
        'staff_training',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        # Staff reference
        sa.Column('staff_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        # Training type
        sa.Column('training_type', postgresql.ENUM(
            'ORIENTATION', 'USE_OF_FORCE', 'FIRST_AID', 'CPR',
            'FIREARMS', 'CRISIS_INTERVENTION', 'ACA_STANDARDS', 'DEFENSIVE_TACTICS',
            name='training_type_enum', create_type=False
        ), nullable=False),
        # Dates
        sa.Column('training_date', sa.Date, nullable=False),
        sa.Column('expiry_date', sa.Date, nullable=True),
        # Duration
        sa.Column('hours', sa.Integer, nullable=False),
        # Instructor
        sa.Column('instructor', sa.String(200), nullable=False),
        # Certification
        sa.Column('certification_number', sa.String(50), nullable=True),
        # Current status
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        # Audit fields (no soft delete for training records)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for staff_training
    op.create_index('ix_staff_training_staff', 'staff_training', ['staff_id'])
    op.create_index('ix_staff_training_type', 'staff_training', ['training_type'])
    op.create_index('ix_staff_training_expiry', 'staff_training', ['expiry_date'])
    op.create_index('ix_staff_training_current', 'staff_training', ['is_current'])
    # Partial index for expiring certifications
    op.create_index(
        'ix_staff_training_expiring',
        'staff_training',
        ['expiry_date', 'is_current'],
        postgresql_where=sa.text("is_current = true AND expiry_date IS NOT NULL")
    )

    # ========================================================================
    # Attach audit triggers
    # ========================================================================
    for table in ['staff', 'staff_shifts', 'staff_training']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table};
            CREATE TRIGGER {table}_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    # Drop audit triggers
    for table in ['staff_training', 'staff_shifts', 'staff']:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_audit_trigger ON {table}")

    # Drop indexes for staff_training
    op.drop_index('ix_staff_training_expiring', 'staff_training')
    op.drop_index('ix_staff_training_current', 'staff_training')
    op.drop_index('ix_staff_training_expiry', 'staff_training')
    op.drop_index('ix_staff_training_type', 'staff_training')
    op.drop_index('ix_staff_training_staff', 'staff_training')

    # Drop indexes for staff_shifts
    op.drop_index('ix_staff_shifts_created_by', 'staff_shifts')
    op.drop_index('ix_staff_shifts_schedule', 'staff_shifts')
    op.drop_index('ix_staff_shifts_housing', 'staff_shifts')
    op.drop_index('ix_staff_shifts_status', 'staff_shifts')
    op.drop_index('ix_staff_shifts_type', 'staff_shifts')
    op.drop_index('ix_staff_shifts_date', 'staff_shifts')
    op.drop_index('ix_staff_shifts_staff', 'staff_shifts')

    # Drop indexes for staff
    op.drop_index('ix_staff_active', 'staff')
    op.drop_index('ix_staff_status', 'staff')
    op.drop_index('ix_staff_department', 'staff')
    op.drop_index('ix_staff_rank', 'staff')
    op.drop_index('ix_staff_name', 'staff')
    op.drop_index('ix_staff_user_id', 'staff')
    op.drop_index('ix_staff_employee_number', 'staff')

    # Drop tables
    op.drop_table('staff_training')
    op.drop_table('staff_shifts')
    op.drop_table('staff')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS training_type_enum")
    op.execute("DROP TYPE IF EXISTS shift_status_enum")
    op.execute("DROP TYPE IF EXISTS shift_type_enum")
    op.execute("DROP TYPE IF EXISTS staff_status_enum")
    op.execute("DROP TYPE IF EXISTS department_enum")
    op.execute("DROP TYPE IF EXISTS staff_rank_enum")
