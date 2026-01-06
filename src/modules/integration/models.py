"""
External Integration Models - Logging and tracking for external system integrations.

This module handles integration with external systems, primarily the
Royal Bahamas Police Force (RBPF) for criminal justice data sharing.

Core entity:
- ExternalSystemLog: Audit trail of all external API requests and responses

NOTE: This is a STUB implementation. TODO comments mark where real
RBPF integration would connect when the API becomes available.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, AuditMixin
from src.common.enums import RequestType, IntegrationStatus


class ExternalSystemLog(AsyncBase, UUIDMixin, AuditMixin):
    """
    Log of all external system integration requests.

    Maintains complete audit trail of all API interactions with
    external systems (RBPF, courts, etc.) for debugging, compliance,
    and security purposes.

    Every integration request is logged before execution and updated
    with the response or error upon completion.
    """
    __tablename__ = 'external_system_logs'

    # System identification
    system_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Name of external system (e.g., 'RBPF', 'COURTS')"
    )

    # Request type
    request_type: Mapped[RequestType] = mapped_column(
        ENUM(RequestType, name='request_type_enum', create_type=False),
        nullable=False,
        comment="Type of integration request"
    )

    # Request/Response payloads (JSONB for flexible structure)
    request_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Request data sent to external system (sanitized of sensitive data)"
    )

    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Response data received from external system"
    )

    # Status tracking
    status: Mapped[IntegrationStatus] = mapped_column(
        ENUM(IntegrationStatus, name='integration_status_enum', create_type=False),
        nullable=False,
        default=IntegrationStatus.PENDING,
        comment="Current status of the request"
    )

    # Timing
    request_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the request was initiated"
    )

    response_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the response was received"
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if request failed"
    )

    # Correlation for tracking related requests
    correlation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="UUID for tracking related requests across systems"
    )

    # Who initiated the request
    initiated_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="Staff member who initiated the request"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_ext_sys_logs_system', 'system_name'),
        Index('ix_ext_sys_logs_request_type', 'request_type'),
        Index('ix_ext_sys_logs_status', 'status'),
        Index('ix_ext_sys_logs_request_time', 'request_time'),
        Index('ix_ext_sys_logs_correlation', 'correlation_id'),
        Index('ix_ext_sys_logs_initiated_by', 'initiated_by'),
    )

    # Relationships
    initiator = relationship(
        'User',
        foreign_keys=[initiated_by],
        lazy='selectin'
    )

    @property
    def response_time_ms(self) -> Optional[int]:
        """Calculate response time in milliseconds."""
        if self.response_time and self.request_time:
            delta = self.response_time - self.request_time
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_successful(self) -> bool:
        """Check if request completed successfully."""
        return self.status == IntegrationStatus.SUCCESS

    def __repr__(self) -> str:
        return f"<ExternalSystemLog {self.system_name}:{self.request_type.value} [{self.status.value}]>"
