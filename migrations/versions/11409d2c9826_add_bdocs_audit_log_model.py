"""add_bdocs_audit_log_model

Revision ID: 11409d2c9826
Revises:
Create Date: 2026-01-05 03:25:40.549888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '11409d2c9826'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# PostgreSQL trigger function for audit logging
AUDIT_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_cols JSONB;
    record_pk TEXT;
    current_user_id TEXT;
BEGIN
    -- Get current user from session variable (set by application)
    current_user_id := current_setting('bdocs.current_user_id', true);

    IF TG_OP = 'INSERT' THEN
        new_data := to_jsonb(NEW);
        -- Remove auto-timestamp fields from audit
        new_data := new_data - 'inserted_date' - 'updated_date';
        record_pk := COALESCE(NEW.id::TEXT, 'unknown');

        INSERT INTO audit_logs (id, table_name, record_id, action, new_values, user_id, timestamp)
        VALUES (gen_random_uuid(), TG_TABLE_NAME, record_pk, 'INSERT', new_data, current_user_id, NOW());
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);

        -- Find changed columns (excluding timestamp fields)
        SELECT jsonb_agg(key) INTO changed_cols
        FROM (
            SELECT key
            FROM jsonb_each(new_data)
            WHERE new_data -> key IS DISTINCT FROM old_data -> key
              AND key NOT IN ('updated_at', 'updated_by', 'updated_date')
        ) changes;

        -- Only log if there are actual changes
        IF changed_cols IS NOT NULL AND jsonb_array_length(changed_cols) > 0 THEN
            record_pk := COALESCE(NEW.id::TEXT, 'unknown');

            INSERT INTO audit_logs (
                id, table_name, record_id, action,
                old_values, new_values, changed_fields,
                user_id, timestamp
            )
            VALUES (
                gen_random_uuid(), TG_TABLE_NAME, record_pk, 'UPDATE',
                old_data, new_data, changed_cols,
                current_user_id, NOW()
            );
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        record_pk := COALESCE(OLD.id::TEXT, 'unknown');

        INSERT INTO audit_logs (id, table_name, record_id, action, old_values, user_id, timestamp)
        VALUES (gen_random_uuid(), TG_TABLE_NAME, record_pk, 'DELETE', old_data, current_user_id, NOW());
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    # Create enum type for audit actions
    audit_action_enum = postgresql.ENUM('INSERT', 'UPDATE', 'DELETE', name='audit_action_enum', create_type=False)
    audit_action_enum.create(op.get_bind(), checkfirst=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(100), nullable=False),
        sa.Column('action', audit_action_enum, nullable=False),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('changed_fields', postgresql.JSONB, nullable=True),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )

    # Create indexes
    op.create_index('ix_audit_table_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('ix_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_user', 'audit_logs', ['user_id'])

    # Create the audit trigger function
    op.execute(AUDIT_TRIGGER_FUNCTION)


def downgrade() -> None:
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_func() CASCADE")

    # Drop indexes
    op.drop_index('ix_audit_user', 'audit_logs')
    op.drop_index('ix_audit_timestamp', 'audit_logs')
    op.drop_index('ix_audit_table_record', 'audit_logs')

    # Drop table
    op.drop_table('audit_logs')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS audit_action_enum")
