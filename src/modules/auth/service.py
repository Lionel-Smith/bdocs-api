"""
Authentication Service - Business logic for user authentication.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID
import bcrypt
import jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import JWTConfig
from src.modules.auth.models import User


# JWT settings
JWT_SECRET = JWTConfig.secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email and password.
        Returns (user, error_message) tuple.
        """
        # Find user by email
        result = await self.session.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None, "Invalid credentials"

        # Check if account is locked
        if user.is_locked:
            return None, f"Account locked. Try again after {user.locked_until}"

        # Check if account is active
        if not user.is_active:
            return None, "Account is deactivated"

        # Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account if too many failures
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

            await self.session.commit()
            return None, "Invalid credentials"

        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        await self.session.commit()

        return user, None

    def generate_tokens(self, user: User) -> Tuple[str, str, int]:
        """
        Generate access and refresh tokens.
        Returns (access_token, refresh_token, expires_in_seconds).
        """
        now = datetime.now(timezone.utc)

        # Access token
        access_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # Refresh token
        refresh_payload = {
            "sub": str(user.id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return access_token, refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify and decode access token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_refresh_token(self, token: str) -> Optional[dict]:
        """Verify and decode refresh token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == UUID(user_id), User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def change_password(self, user: User, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        Returns (success, error_message).
        """
        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"

        # Hash and save new password
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.must_change_password = False
        await self.session.commit()

        return True, None

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
