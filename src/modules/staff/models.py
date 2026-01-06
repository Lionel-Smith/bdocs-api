"""
Staff Management Models - Personnel tracking for BDOCS.

This module handles correctional staff records, shift scheduling,
and training/certification management.

Three core entities:
- Staff: Personnel records linked to auth users
- StaffShift: Duty schedule and post assignments
- StaffTraining: Certifications and training records
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Date, Time, DateTime, Integer, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import (
    StaffRank, Department, StaffStatus,
    ShiftType, ShiftStatus, TrainingType
)


class Staff(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Staff record for BDOCS personnel.

    Links to auth users table for authentication.
    Employee number format: EMP-NNNNN (5-digit sequence).

    Each staff member belongs to one department and holds
    a rank within the organizational hierarchy.
    """
    __tablename__ = 'staff'

    # Link to auth users (one-to-one)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        unique=True,
        nullable=False,
        comment="Link to auth users table"
    )

    # Employee identification
    employee_number: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Format: EMP-NNNNN"
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Position
    rank: Mapped[StaffRank] = mapped_column(
        ENUM(StaffRank, name='staff_rank_enum', create_type=False),
        nullable=False,
        default=StaffRank.OFFICER
    )

    department: Mapped[Department] = mapped_column(
        ENUM(Department, name='department_enum', create_type=False),
        nullable=False,
        default=Department.SECURITY
    )

    # Employment
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[StaffStatus] = mapped_column(
        ENUM(StaffStatus, name='staff_status_enum', create_type=False),
        nullable=False,
        default=StaffStatus.ACTIVE
    )

    # Contact - Bahamas phone format
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Format: (242) XXX-XXXX"
    )

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )

    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Format: (242) XXX-XXXX"
    )

    # Certifications stored as JSONB array
    certifications: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {type, date, expiry, number}"
    )

    # Active flag for quick filtering
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Quick check for active staff"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_staff_name', 'last_name', 'first_name'),
        Index('ix_staff_rank', 'rank'),
        Index('ix_staff_department', 'department'),
        Index('ix_staff_status', 'status'),
        Index('ix_staff_active', 'is_active'),
    )

    @property
    def full_name(self) -> str:
        """Return full name in 'Last, First' format."""
        return f"{self.last_name}, {self.first_name}"

    @property
    def years_of_service(self) -> int:
        """Calculate years of service from hire date."""
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )

    # Relationships
    user = relationship(
        'User',
        foreign_keys=[user_id],
        lazy='selectin'
    )

    shifts = relationship(
        'StaffShift',
        back_populates='staff',
        lazy='selectin',
        cascade='all, delete-orphan',
        foreign_keys='StaffShift.staff_id'
    )

    training_records = relationship(
        'StaffTraining',
        back_populates='staff',
        lazy='selectin',
        cascade='all, delete-orphan'
    )

    # Shifts created by this staff member
    created_shifts = relationship(
        'StaffShift',
        foreign_keys='StaffShift.created_by',
        lazy='selectin'
    )

    def __repr__(self) -> str:
        return f"<Staff {self.employee_number}: {self.full_name} ({self.rank.value})>"


class StaffShift(AsyncBase, UUIDMixin, AuditMixin):
    """
    Staff shift schedule and post assignments.

    Tracks duty schedules with optional housing unit assignments
    for post coverage planning.
    """
    __tablename__ = 'staff_shifts'

    # Staff assignment
    staff_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('staff.id', ondelete='CASCADE'),
        nullable=False
    )

    # Shift date and type
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)

    shift_type: Mapped[ShiftType] = mapped_column(
        ENUM(ShiftType, name='shift_type_enum', create_type=False),
        nullable=False
    )

    # Shift times
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Post assignment (optional)
    housing_unit_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('housing_units.id', ondelete='SET NULL'),
        nullable=True,
        comment="Assigned housing unit/post"
    )

    # Status
    status: Mapped[ShiftStatus] = mapped_column(
        ENUM(ShiftStatus, name='shift_status_enum', create_type=False),
        nullable=False,
        default=ShiftStatus.SCHEDULED
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Shift notes, swap reasons, etc."
    )

    # Created by (supervisor who created the schedule)
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('staff.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_staff_shifts_staff', 'staff_id'),
        Index('ix_staff_shifts_date', 'shift_date'),
        Index('ix_staff_shifts_type', 'shift_type'),
        Index('ix_staff_shifts_status', 'status'),
        Index('ix_staff_shifts_housing', 'housing_unit_id'),
        # Composite index for schedule queries
        Index('ix_staff_shifts_schedule', 'shift_date', 'shift_type', 'status'),
    )

    # Relationships
    staff = relationship(
        'Staff',
        back_populates='shifts',
        foreign_keys=[staff_id],
        lazy='selectin'
    )

    creator = relationship(
        'Staff',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    housing_unit = relationship(
        'HousingUnit',
        lazy='selectin'
    )

    def __repr__(self) -> str:
        return f"<StaffShift {self.staff_id} {self.shift_date} {self.shift_type.value}>"


class StaffTraining(AsyncBase, UUIDMixin, AuditMixin):
    """
    Staff training and certification records.

    Tracks completion of required training with expiry dates
    for certifications that require periodic renewal.
    """
    __tablename__ = 'staff_training'

    # Staff reference
    staff_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('staff.id', ondelete='CASCADE'),
        nullable=False
    )

    # Training type
    training_type: Mapped[TrainingType] = mapped_column(
        ENUM(TrainingType, name='training_type_enum', create_type=False),
        nullable=False
    )

    # Dates
    training_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date training was completed"
    )

    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expiration date for certification (null if no expiry)"
    )

    # Duration
    hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Training hours completed"
    )

    # Instructor
    instructor: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Name of instructor/trainer"
    )

    # Certification
    certification_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Certificate or credential number"
    )

    # Current status
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the current valid certification"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_staff_training_staff', 'staff_id'),
        Index('ix_staff_training_type', 'training_type'),
        Index('ix_staff_training_expiry', 'expiry_date'),
        Index('ix_staff_training_current', 'is_current'),
        # Partial index for expiring certifications
        Index(
            'ix_staff_training_expiring',
            'expiry_date', 'is_current',
            postgresql_where='is_current = true AND expiry_date IS NOT NULL'
        ),
    )

    # Relationships
    staff = relationship(
        'Staff',
        back_populates='training_records',
        lazy='selectin'
    )

    @property
    def is_expired(self) -> bool:
        """Check if certification has expired."""
        if self.expiry_date is None:
            return False
        return date.today() > self.expiry_date

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Days until expiry (negative if expired)."""
        if self.expiry_date is None:
            return None
        return (self.expiry_date - date.today()).days

    def __repr__(self) -> str:
        return f"<StaffTraining {self.staff_id} {self.training_type.value} {self.training_date}>"
