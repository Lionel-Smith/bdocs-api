"""
BDOCS-specific model mixins.
These EXTEND the existing BaseModel - they do not replace it.

Usage: Combine with AsyncBase for BDOCS entities
    class Inmate(AsyncBase, UUIDMixin, SoftDeleteMixin):
        ...
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, Mapped, mapped_column


class UUIDMixin:
    """
    UUID primary key mixin for RBPF integration compatibility.

    Use this INSTEAD OF integer PKs when:
    - Table needs to integrate with RBPF systems
    - Records may be shared across systems

    NOTE: This OVERRIDES default id field with UUID
    """
    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4
        )


class SoftDeleteMixin:
    """
    Soft delete support for data retention compliance.
    Records are never truly deleted - is_deleted flag is set.

    This is required for ACA compliance - inmates records
    must be retained even after release.
    """
    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def deleted_by(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(100), nullable=True)


class AuditMixin:
    """
    Standard audit fields for tracking record changes.
    Complements the PostgreSQL audit trigger for detailed change tracking.
    """
    @declared_attr
    def inserted_by(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(100), nullable=True)

    @declared_attr
    def inserted_date(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(100), nullable=True)

    @declared_attr
    def updated_date(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            onupdate=datetime.utcnow,
            nullable=True
        )
