"""
Inmate Controller - API endpoints for inmate management.

Blueprint: /api/v1/inmates
"""
from uuid import UUID

from quart import Blueprint, request, jsonify
from pydantic import ValidationError

from src.database.async_db import get_async_session
from src.common.enums import InmateStatus, SecurityLevel
from src.modules.inmate.service import InmateService, InmateNotFoundError
from src.modules.inmate.dtos import (
    InmateCreate,
    InmateUpdate,
    InmateResponse,
    InmateSearchParams,
)

# Create blueprint - auto-discovered by app factory
blueprint = Blueprint('inmates', __name__, url_prefix='/api/v1/inmates')


def error_response(message: str, status_code: int = 400, details: dict = None):
    """Standard error response format."""
    response = {"error": message, "status_code": status_code}
    if details:
        response["details"] = details
    return jsonify(response), status_code


def success_response(data: dict, status_code: int = 200):
    """Standard success response format."""
    return jsonify(data), status_code


@blueprint.route('', methods=['POST'])
async def create_inmate():
    """
    Create a new inmate during intake/booking.

    POST /api/v1/inmates

    Request Body: InmateCreate DTO
    Response: InmateResponse with auto-generated booking_number
    """
    try:
        data = await request.get_json()
        inmate_data = InmateCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = InmateService(session)
        # TODO: Get current user from auth context
        inmate = await service.create_inmate(inmate_data, created_by="system")
        await session.commit()

        response = InmateResponse.model_validate(inmate)
        return success_response(response.model_dump(mode='json'), 201)


@blueprint.route('', methods=['GET'])
async def list_inmates():
    """
    List inmates with pagination and optional filters.

    GET /api/v1/inmates?page=1&page_size=20&status=REMAND&security_level=MAXIMUM

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by InmateStatus
    - security_level: Filter by SecurityLevel
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)  # Cap at 100

    status_str = request.args.get('status')
    security_str = request.args.get('security_level')

    status = InmateStatus(status_str) if status_str else None
    security_level = SecurityLevel(security_str) if security_str else None

    async with get_async_session() as session:
        service = InmateService(session)
        result = await service.list_inmates(
            status=status,
            security_level=security_level,
            page=page,
            page_size=page_size
        )
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/<uuid:inmate_id>', methods=['GET'])
async def get_inmate(inmate_id: UUID):
    """
    Get inmate by UUID.

    GET /api/v1/inmates/{id}
    """
    async with get_async_session() as session:
        service = InmateService(session)
        try:
            inmate = await service.get_inmate_by_id(inmate_id)
            response = InmateResponse.model_validate(inmate)
            return success_response(response.model_dump(mode='json'))
        except InmateNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/booking/<booking_number>', methods=['GET'])
async def get_inmate_by_booking(booking_number: str):
    """
    Get inmate by booking number.

    GET /api/v1/inmates/booking/{booking_number}
    Example: GET /api/v1/inmates/booking/BDOCS-2026-00001
    """
    async with get_async_session() as session:
        service = InmateService(session)
        try:
            inmate = await service.get_inmate_by_booking_number(booking_number)
            response = InmateResponse.model_validate(inmate)
            return success_response(response.model_dump(mode='json'))
        except InmateNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/<uuid:inmate_id>', methods=['PUT'])
async def update_inmate(inmate_id: UUID):
    """
    Update inmate information.

    PUT /api/v1/inmates/{id}

    Request Body: InmateUpdate DTO (partial update)
    """
    try:
        data = await request.get_json()
        update_data = InmateUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = InmateService(session)
        try:
            # TODO: Get current user from auth context
            inmate = await service.update_inmate(
                inmate_id,
                update_data,
                updated_by="system"
            )
            await session.commit()

            response = InmateResponse.model_validate(inmate)
            return success_response(response.model_dump(mode='json'))
        except InmateNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/search', methods=['GET'])
async def search_inmates():
    """
    Search inmates by name or booking number.

    GET /api/v1/inmates/search?query=Smith&page=1&page_size=20

    Query Parameters:
    - query: Search term (min 2 characters)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    """
    query = request.args.get('query', '')
    if len(query) < 2:
        return error_response("Search query must be at least 2 characters", 400)

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)

    async with get_async_session() as session:
        service = InmateService(session)
        result = await service.search_inmates(query, page, page_size)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/active', methods=['GET'])
async def get_active_inmates():
    """
    Get inmates currently in custody (REMAND or SENTENCED status).

    GET /api/v1/inmates/active?page=1&page_size=20
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)

    async with get_async_session() as session:
        service = InmateService(session)
        result = await service.get_active_inmates(page, page_size)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/stats', methods=['GET'])
async def get_population_stats():
    """
    Get population statistics.

    GET /api/v1/inmates/stats

    Returns count of remand vs sentenced inmates.
    """
    async with get_async_session() as session:
        service = InmateService(session)
        stats = await service.get_population_stats()
        return success_response(stats)


@blueprint.route('/<uuid:inmate_id>', methods=['DELETE'])
async def delete_inmate(inmate_id: UUID):
    """
    Soft delete an inmate record.

    DELETE /api/v1/inmates/{id}

    Note: Records are soft-deleted (is_deleted=True) for data retention.
    """
    async with get_async_session() as session:
        service = InmateService(session)
        try:
            # TODO: Get current user from auth context
            await service.soft_delete_inmate(inmate_id, deleted_by="system")
            await session.commit()
            return success_response({"message": "Inmate record deleted"})
        except InmateNotFoundError as e:
            return error_response(str(e), 404)
