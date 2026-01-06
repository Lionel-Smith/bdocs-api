"""
Authentication DTOs - Request/Response schemas for auth endpoints.

Uses camelCase aliases for frontend compatibility while maintaining
Python snake_case internally.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.common.enums import UserRole


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase serialization."""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthTokens(CamelModel):
    """Token pair response."""
    access_token: str
    refresh_token: str
    expires_in: int  # seconds


class UserResponse(CamelModel):
    """User information response - matches frontend User interface."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    permissions: List[str] = []  # Frontend expects permissions array
    badge_number: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
    )


class LoginResponse(CamelModel):
    """Successful login response - matches frontend LoginResponse interface."""
    user: UserResponse
    tokens: AuthTokens


class RefreshRequest(CamelModel):
    """Token refresh request."""
    refresh_token: str


class TokenResponse(CamelModel):
    """Token refresh response."""
    access_token: str
    refresh_token: str
    expires_in: int


class PasswordChangeRequest(CamelModel):
    """Password change request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12)


class PasswordResetRequest(BaseModel):
    """Password reset request (forgot password)."""
    email: EmailStr


class PasswordResetConfirm(CamelModel):
    """Password reset confirmation with token."""
    token: str
    new_password: str = Field(..., min_length=12)
