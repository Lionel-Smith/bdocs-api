"""
Authentication Module - User management and access control.

Provides user authentication, authorization, and session management
for the BDOCS Prison Information System.
"""
from src.modules.auth.models import User
from src.modules.auth.controller import auth_bp, blueprint

__all__ = [
    'User',
    'auth_bp',
    'blueprint'
]
