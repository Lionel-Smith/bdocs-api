"""add_inmates_table

Revision ID: eb30eeec74ef
Revises: 11409d2c9826
Create Date: 2026-01-05 03:46:33.827659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'eb30eeec74ef'
down_revision: Union[str, None] = '11409d2c9826'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    gender_enum = postgresql.ENUM('MALE', 'FEMALE', name='gender_enum', create_type=False)
    gender_enum.create(op.get_bind(), checkfirst=True)

    inmate_status_enum = postgresql.ENUM(
        'REMAND', 'SENTENCED', 'RELEASED', 'TRANSFERRED', 'DECEASED',
        name='inmate_status_enum', create_type=False
    )
    inmate_status_enum.create(op.get_bind(), checkfirst=True)

    security_level_enum = postgresql.ENUM(
        'MAXIMUM', 'MEDIUM', 'MINIMUM',
        name='security_level_enum', create_type=False
    )
    security_level_enum.create(op.get_bind(), checkfirst=True)

    # Create inmates table
    op.create_table(
        'inmates',
        # Primary key (from UUIDMixin)
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Booking information
        sa.Column('booking_number', sa.String(20), unique=True, nullable=False),
        sa.Column('nib_number', sa.String(20), nullable=True),

        # Personal information
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('aliases', postgresql.JSONB, nullable=True),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('gender', gender_enum, nullable=False),
        sa.Column('nationality', sa.String(100), nullable=False, server_default='Bahamian'),
        sa.Column('island_of_origin', sa.String(50), nullable=True),

        # Physical description
        sa.Column('height_cm', sa.Integer, nullable=True),
        sa.Column('weight_kg', sa.Float, nullable=True),
        sa.Column('eye_color', sa.String(30), nullable=True),
        sa.Column('hair_color', sa.String(30), nullable=True),
        sa.Column('distinguishing_marks', sa.Text, nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),

        # Classification
        sa.Column('status', inmate_status_enum, nullable=False, server_default='REMAND'),
        sa.Column('security_level', security_level_enum, nullable=False, server_default='MEDIUM'),

        # Dates
        sa.Column('admission_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('release_date', sa.DateTime(timezone=True), nullable=True),

        # Emergency contact
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(50), nullable=True),

        # Soft delete (from SoftDeleteMixin)
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(100), nullable=True),

        # Audit fields (from AuditMixin)
        sa.Column('inserted_by', sa.String(100), nullable=True),
        sa.Column('inserted_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('updated_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('ix_inmates_booking_number', 'inmates', ['booking_number'])
    op.create_index('ix_inmates_nib_number', 'inmates', ['nib_number'])
    op.create_index('ix_inmates_name', 'inmates', ['last_name', 'first_name'])
    op.create_index('ix_inmates_status', 'inmates', ['status'])
    op.create_index('ix_inmates_admission', 'inmates', ['admission_date'])
    op.create_index('ix_inmates_security', 'inmates', ['security_level'])

    # Attach audit trigger for ACA compliance
    op.execute("""
        DROP TRIGGER IF EXISTS inmates_audit_trigger ON inmates;
        CREATE TRIGGER inmates_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON inmates
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """)


def downgrade() -> None:
    # Drop audit trigger
    op.execute("DROP TRIGGER IF EXISTS inmates_audit_trigger ON inmates")

    # Drop indexes
    op.drop_index('ix_inmates_security', 'inmates')
    op.drop_index('ix_inmates_admission', 'inmates')
    op.drop_index('ix_inmates_status', 'inmates')
    op.drop_index('ix_inmates_name', 'inmates')
    op.drop_index('ix_inmates_nib_number', 'inmates')
    op.drop_index('ix_inmates_booking_number', 'inmates')

    # Drop table
    op.drop_table('inmates')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS security_level_enum")
    op.execute("DROP TYPE IF EXISTS inmate_status_enum")
    op.execute("DROP TYPE IF EXISTS gender_enum")
