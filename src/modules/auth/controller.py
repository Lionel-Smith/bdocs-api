"""
Authentication Controller - API routes for auth operations.

Endpoints:
- POST /api/v1/auth/login - Authenticate user
- POST /api/v1/auth/logout - Invalidate session
- POST /api/v1/auth/refresh - Refresh access token
- GET /api/v1/auth/me - Get current user
- POST /api/v1/auth/change-password - Change password
"""
from functools import wraps
from quart import Blueprint, request, jsonify, g

from src.database.async_db import get_async_session
from src.modules.auth.service import AuthService
from src.modules.auth.dtos import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    AuthTokens,
    RefreshRequest,
    TokenResponse,
    PasswordChangeRequest,
)


from src.common.enums import UserRole

# Create blueprint - auto-discovered by app factory
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
blueprint = auth_bp  # Alias for auto-discovery


# Role-based permissions mapping (matches frontend RBAC)
# Backend roles: ADMIN, SUPERVISOR, OFFICER, INTAKE, PROGRAMMES, MEDICAL, RECORDS, READONLY
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        'inmates:read', 'inmates:write', 'inmates:delete',
        'housing:read', 'housing:write', 'housing:transfer',
        'court:read', 'court:write', 'court:transport',
        'medical:read', 'medical:write', 'medical:prescribe',
        'staff:read', 'staff:write', 'staff:schedule',
        'programmes:read', 'programmes:write', 'programmes:enroll',
        'incidents:read', 'incidents:write', 'incidents:review',
        'reports:read', 'reports:generate', 'reports:export',
        'clemency:read', 'clemency:write', 'clemency:recommend',
        'visitors:read', 'visitors:write', 'visitors:approve',
        'settings:read', 'settings:manage',
    ],
    UserRole.SUPERVISOR: [
        'inmates:read', 'inmates:write',
        'housing:read', 'housing:write', 'housing:transfer',
        'court:read', 'court:write',
        'staff:read', 'staff:schedule',
        'programmes:read', 'programmes:write',
        'incidents:read', 'incidents:write', 'incidents:review',
        'reports:read', 'reports:generate',
        'visitors:read', 'visitors:write', 'visitors:approve',
    ],
    UserRole.OFFICER: [
        'inmates:read',
        'housing:read',
        'court:read',
        'incidents:read', 'incidents:write',
        'visitors:read',
    ],
    UserRole.INTAKE: [
        'inmates:read', 'inmates:write',
        'housing:read',
        'court:read',
    ],
    UserRole.PROGRAMMES: [
        'inmates:read',
        'programmes:read', 'programmes:write', 'programmes:enroll',
        'reports:read',
    ],
    UserRole.MEDICAL: [
        'inmates:read',
        'medical:read', 'medical:write', 'medical:prescribe',
        'reports:read',
    ],
    UserRole.RECORDS: [
        'inmates:read', 'inmates:write',
        'court:read', 'court:write',
        'reports:read', 'reports:generate',
    ],
    UserRole.READONLY: [
        'inmates:read',
        'housing:read',
        'court:read',
        'reports:read',
    ],
}


def _get_permissions_for_role(role: UserRole) -> list[str]:
    """Get list of permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def token_required(f):
    """Decorator to require valid access token."""
    @wraps(f)
    async def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(' ')[1]

        async with get_async_session() as session:
            service = AuthService(session)
            payload = service.verify_access_token(token)

            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            user = await service.get_user_by_id(payload['sub'])
            if not user:
                return jsonify({"error": "User not found"}), 401

            if not user.is_active:
                return jsonify({"error": "Account deactivated"}), 401

            g.current_user = user
            g.token_payload = payload

        return await f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['POST'])
async def login():
    """
    Authenticate user with email and password.

    Request body:
        - email: User's email address
        - password: User's password

    Returns:
        - access_token: JWT access token
        - refresh_token: JWT refresh token
        - token_type: "Bearer"
        - expires_in: Token lifetime in seconds
        - user: User information
    """
    try:
        data = await request.get_json()
        credentials = LoginRequest.model_validate(data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    async with get_async_session() as session:
        service = AuthService(session)
        user, error = await service.authenticate(credentials.email, credentials.password)

        if error:
            return jsonify({"error": error}), 401

        access_token, refresh_token, expires_in = service.generate_tokens(user)

        # Build response matching frontend LoginResponse interface
        tokens = AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )

        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            permissions=_get_permissions_for_role(user.role),
            badge_number=user.badge_number,
            department=user.assigned_unit,  # Map assigned_unit to department
            last_login=user.last_login
        )

        response = LoginResponse(
            user=user_response,
            tokens=tokens
        )

        return jsonify(response.model_dump(mode='json', by_alias=True)), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
async def logout():
    """
    Logout current user.

    In a stateless JWT system, logout is handled client-side by
    discarding the token. This endpoint exists for API completeness
    and could be extended for token blacklisting.
    """
    # In a more complete implementation, we would blacklist the token
    # For now, just return success
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/refresh', methods=['POST'])
async def refresh_token():
    """
    Refresh access token using refresh token.

    Request body:
        - refresh_token: Valid refresh token

    Returns:
        - access_token: New JWT access token
        - refresh_token: New JWT refresh token
        - token_type: "Bearer"
        - expires_in: Token lifetime in seconds
    """
    try:
        data = await request.get_json()
        refresh_request = RefreshRequest.model_validate(data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    async with get_async_session() as session:
        service = AuthService(session)
        payload = service.verify_refresh_token(refresh_request.refresh_token)

        if not payload:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        user = await service.get_user_by_id(payload['sub'])
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401

        access_token, new_refresh_token, expires_in = service.generate_tokens(user)

        response = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in
        )

        return jsonify(response.model_dump(mode='json', by_alias=True)), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
async def get_current_user():
    """
    Get current authenticated user's information.

    Returns:
        User information including role, position, etc.
    """
    user = g.current_user

    response = UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        permissions=_get_permissions_for_role(user.role),
        badge_number=user.badge_number,
        department=user.assigned_unit,
        last_login=user.last_login
    )

    return jsonify(response.model_dump(mode='json', by_alias=True)), 200


@auth_bp.route('/change-password', methods=['POST'])
@token_required
async def change_password():
    """
    Change current user's password.

    Request body:
        - current_password: Current password
        - new_password: New password (min 12 chars)

    Returns:
        Success message
    """
    try:
        data = await request.get_json()
        password_request = PasswordChangeRequest.model_validate(data)
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    async with get_async_session() as session:
        service = AuthService(session)
        user = await service.get_user_by_id(str(g.current_user.id))

        success, error = await service.change_password(
            user,
            password_request.current_password,
            password_request.new_password
        )

        if not success:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Password changed successfully"}), 200
