"""
AuditLog for ACA compliance - captures ALL data changes.

This is SEPARATE from the audit fields in mixins:
- AuditMixin fields: Track WHO made changes (inserted_by, updated_by)
- AuditLog table: Track WHAT changed (old values, new values, changed fields)

ACA accreditation requires complete audit trail of all data modifications.
The PostgreSQL trigger function automatically populates this table.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database.async_db import AsyncBase
from src.common.enums import AuditAction


class AuditLog(AsyncBase):
    """
    Complete audit trail for ACA compliance.
    Populated automatically by PostgreSQL trigger.

    DO NOT INSERT MANUALLY - use the trigger function.
    """
    __tablename__ = 'audit_logs'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # What changed
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(
        SAEnum(AuditAction, name='audit_action_enum', create_type=True),
        nullable=False
    )

    # Change details
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    changed_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Who and when
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index('ix_audit_table_record', 'table_name', 'record_id'),
        Index('ix_audit_timestamp', 'timestamp'),
        Index('ix_audit_user', 'user_id'),
    )


# PostgreSQL trigger function - creates comprehensive audit trail
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


def create_audit_trigger_sql(table_name: str) -> str:
    """
    Generate SQL to create audit trigger for a table.

    Usage in migrations:
        from src.models.audit_log_model import create_audit_trigger_sql
        op.execute(create_audit_trigger_sql('inmates'))
    """
    return f"""
    DROP TRIGGER IF EXISTS {table_name}_audit_trigger ON {table_name};
    CREATE TRIGGER {table_name}_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON {table_name}
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
    """


def drop_audit_trigger_sql(table_name: str) -> str:
    """Generate SQL to drop audit trigger (for migration rollback)."""
    return f"DROP TRIGGER IF EXISTS {table_name}_audit_trigger ON {table_name};"
