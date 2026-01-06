"""
Authentication Models - User entity for BDOCS system access.

The User model handles authentication credentials and role-based
access control. Separate from Staff records (personnel management).

User-Staff Relationship:
- A User can exist without a Staff record (e.g., external auditors)
- A Staff record always links to a User (authentication required)
- This separation allows different lifecycle management
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import UserRole


class User(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    System user for authentication and authorization.

    Username format: lowercase letters, numbers, dots, underscores.
    Email domain: @bdcs.gov.bs for internal users.
    Password: bcrypt hashed, minimum 12 characters.

    Roles determine system access levels via RBAC.
    """
    __tablename__ = 'users'

    # Authentication credentials
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique login username"
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email address for notifications"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hashed password"
    )

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Role-based access control
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name='user_role_enum', create_type=False),
        nullable=False,
        default=UserRole.READONLY,
        comment="System access role"
    )

    # Identification
    badge_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
        comment="BDOCS badge number"
    )

    # Contact - Bahamas phone format (242) XXX-XXXX
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Format: (242) XXX-XXXX"
    )

    # Position/title
    position: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Job title or position"
    )

    # Assigned housing unit (for officers/supervisors)
    assigned_unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Housing unit code assignment"
    )

    # Shift assignment (DAY, EVENING, NIGHT)
    shift: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Shift type assignment"
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether account can authenticate"
    )

    is_system_account: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="System/service account flag"
    )

    is_external: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="External user flag (auditors, etc.)"
    )

    # Session tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Consecutive failed login attempts"
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account lockout expiry (null if not locked)"
    )

    # Password management
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last password change timestamp"
    )

    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Force password change on next login"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_users_role', 'role'),
        Index('ix_users_active', 'is_active'),
        Index('ix_users_name', 'last_name', 'first_name'),
        Index('ix_users_external', 'is_external'),
    )

    @property
    def full_name(self) -> str:
        """Return full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(self.locked_until.tzinfo) < self.locked_until

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
