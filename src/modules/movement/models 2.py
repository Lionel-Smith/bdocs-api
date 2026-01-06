"""
Movement Model - Inmate movement tracking.

Tracks all inmate movements including court transport, medical transport,
internal transfers, work release, and releases.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import MovementType, MovementStatus


class Movement(UUIDMixin, SoftDeleteMixin, AuditMixin, AsyncBase):
    """
    Inmate movement record.

    Tracks movements with status workflow:
    SCHEDULED → IN_PROGRESS → COMPLETED
                    ↓
               CANCELLED (from SCHEDULED only)
    """
    __tablename__ = 'movements'

    # Foreign Keys
    inmate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Movement type and status
    movement_type: Mapped[str] = mapped_column(
        ENUM(
            'INTERNAL_TRANSFER', 'COURT_TRANSPORT', 'MEDICAL_TRANSPORT',
            'WORK_RELEASE', 'TEMPORARY_RELEASE', 'FURLOUGH',
            'EXTERNAL_APPOINTMENT', 'RELEASE',
            name='movement_type_enum',
            create_type=False
        ),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        ENUM(
            'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED',
            name='movement_status_enum',
            create_type=False
        ),
        nullable=False,
        default=MovementStatus.SCHEDULED.value
    )

    # Locations
    from_location: Mapped[str] = mapped_column(String(200), nullable=False)
    to_location: Mapped[str] = mapped_column(String(200), nullable=False)

    # Timestamps
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    departure_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    arrival_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Optional foreign keys
    escort_officer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True
    )

    vehicle_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Court appearance FK with deferred constraint (for future CourtAppearance table)
    court_appearance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey('court_appearances.id', ondelete='SET NULL', use_alter=True),
        nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Created by (user who scheduled the movement)
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True
    )

    # Relationships
    inmate = relationship('Inmate', back_populates='movements', lazy='selectin')
    court_appearance = relationship(
        'CourtAppearance',
        back_populates='movement',
        lazy='selectin',
        foreign_keys=[court_appearance_id]
    )

    def __repr__(self) -> str:
        return f"<Movement {self.movement_type} {self.status} inmate={self.inmate_id}>"
