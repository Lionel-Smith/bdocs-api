"""
Movement Controller - API endpoints for movement tracking.

Endpoints:
1. POST /api/v1/movements - Create movement
2. GET /api/v1/movements - List movements (with filters)
3. GET /api/v1/movements/{id} - Get single movement
4. PUT /api/v1/movements/{id} - Update movement details
5. PUT /api/v1/movements/{id}/status - Update status (workflow)
6. DELETE /api/v1/movements/{id} - Delete movement
7. GET /api/v1/movements/in-progress - Get in-progress movements
8. GET /api/v1/inmates/{inmate_id}/movements - Get inmate movements
9. GET /api/v1/movements/daily/{date} - Get daily summary
"""
from datetime import datetime, date
from uuid import UUID

from quart import Blueprint, request, jsonify
from pydantic import ValidationError

from src.database.async_db import get_async_session
from src.common.enums import MovementType, MovementStatus
from src.modules.movement.service import (
    MovementService,
    MovementNotFoundError,
    InvalidStatusTransitionError,
    InmateAlreadyMovingError,
)
from src.modules.movement.dtos import (
    MovementCreate,
    MovementUpdate,
    MovementStatusUpdate,
    MovementFilter,
)


blueprint = Blueprint('movement', __name__, url_prefix='/api/v1')


def error_response(message: str, status_code: int = 400, details: dict = None):
    """Standard error response format."""
    response = {"error": message, "status_code": status_code}
    if details:
        response["details"] = details
    return jsonify(response), status_code


def success_response(data: dict, status_code: int = 200):
    """Standard success response format."""
    return jsonify(data), status_code


# ============================================================================
# Movement CRUD Endpoints
# ============================================================================

@blueprint.route('/movements', methods=['POST'])
async def create_movement():
    """
    Create a new movement.

    POST /api/v1/movements

    Request body:
    {
        "inmate_id": "uuid",
        "movement_type": "COURT_TRANSPORT|MEDICAL_TRANSPORT|...",
        "from_location": "string",
        "to_location": "string",
        "scheduled_time": "ISO datetime",
        "escort_officer_id": "uuid" (optional),
        "vehicle_id": "string" (optional),
        "court_appearance_id": "uuid" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        movement_data = MovementCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = MovementService(session)
        try:
            # TODO: Get created_by from auth context
            movement = await service.create_movement(movement_data)
            await session.commit()
            return success_response(movement.model_dump(mode='json'), 201)
        except InmateAlreadyMovingError as e:
            return error_response(str(e), 409)


@blueprint.route('/movements', methods=['GET'])
async def list_movements():
    """
    List movements with optional filters.

    GET /api/v1/movements?inmate_id=&type=&status=&from_date=&to_date=
    """
    # Parse query parameters
    filters = MovementFilter(
        inmate_id=request.args.get('inmate_id'),
        movement_type=MovementType(request.args.get('type')) if request.args.get('type') else None,
        status=MovementStatus(request.args.get('status')) if request.args.get('status') else None,
        from_date=datetime.fromisoformat(request.args.get('from_date')) if request.args.get('from_date') else None,
        to_date=datetime.fromisoformat(request.args.get('to_date')) if request.args.get('to_date') else None,
        escort_officer_id=request.args.get('escort_officer_id'),
    )

    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = MovementService(session)
        result = await service.search_movements(filters, skip, limit)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/movements/in-progress', methods=['GET'])
async def get_in_progress_movements():
    """
    Get all movements currently in progress.

    GET /api/v1/movements/in-progress
    """
    async with get_async_session() as session:
        service = MovementService(session)
        result = await service.get_in_progress_movements()
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/movements/daily/<target_date>', methods=['GET'])
async def get_daily_summary(target_date: str):
    """
    Get daily movement summary.

    GET /api/v1/movements/daily/{YYYY-MM-DD}
    """
    try:
        parsed_date = date.fromisoformat(target_date)
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", 400)

    async with get_async_session() as session:
        service = MovementService(session)
        result = await service.get_daily_movement_summary(parsed_date)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/movements/<uuid:movement_id>', methods=['GET'])
async def get_movement(movement_id: UUID):
    """
    Get a single movement by ID.

    GET /api/v1/movements/{id}
    """
    async with get_async_session() as session:
        service = MovementService(session)
        try:
            movement = await service.get_movement(movement_id)
            return success_response(movement.model_dump(mode='json'))
        except MovementNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/movements/<uuid:movement_id>', methods=['PUT'])
async def update_movement(movement_id: UUID):
    """
    Update movement details (not status).

    PUT /api/v1/movements/{id}

    Request body:
    {
        "scheduled_time": "ISO datetime" (optional),
        "escort_officer_id": "uuid" (optional),
        "vehicle_id": "string" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        update_data = MovementUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = MovementService(session)
        try:
            # TODO: Get updated_by from auth context
            movement = await service.update_movement(movement_id, update_data)
            await session.commit()
            return success_response(movement.model_dump(mode='json'))
        except MovementNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidStatusTransitionError as e:
            return error_response(str(e), 400)


@blueprint.route('/movements/<uuid:movement_id>/status', methods=['PUT'])
async def update_movement_status(movement_id: UUID):
    """
    Update movement status (workflow transition).

    PUT /api/v1/movements/{id}/status

    Request body:
    {
        "status": "IN_PROGRESS|COMPLETED|CANCELLED",
        "departure_time": "ISO datetime" (optional, for IN_PROGRESS),
        "arrival_time": "ISO datetime" (optional, for COMPLETED),
        "notes": "string" (optional)
    }

    Valid transitions:
    - SCHEDULED → IN_PROGRESS, CANCELLED
    - IN_PROGRESS → COMPLETED
    """
    try:
        data = await request.get_json()
        status_data = MovementStatusUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = MovementService(session)
        try:
            # TODO: Get updated_by from auth context
            movement = await service.update_status(movement_id, status_data)
            await session.commit()
            return success_response(movement.model_dump(mode='json'))
        except MovementNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidStatusTransitionError as e:
            return error_response(str(e), 400)


@blueprint.route('/movements/<uuid:movement_id>', methods=['DELETE'])
async def delete_movement(movement_id: UUID):
    """
    Soft delete a movement.

    DELETE /api/v1/movements/{id}

    Only SCHEDULED or CANCELLED movements can be deleted.
    """
    async with get_async_session() as session:
        service = MovementService(session)
        try:
            # TODO: Get deleted_by from auth context
            await service.delete_movement(movement_id)
            await session.commit()
            return success_response({"message": "Movement deleted successfully"})
        except MovementNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidStatusTransitionError as e:
            return error_response(str(e), 400)


# ============================================================================
# Inmate Movement Endpoints
# ============================================================================

@blueprint.route('/inmates/<uuid:inmate_id>/movements', methods=['GET'])
async def get_inmate_movements(inmate_id: UUID):
    """
    Get all movements for an inmate.

    GET /api/v1/inmates/{inmate_id}/movements
    """
    async with get_async_session() as session:
        service = MovementService(session)
        result = await service.get_movements_by_inmate(inmate_id)
        return success_response({
            "inmate_id": str(inmate_id),
            **result.model_dump(mode='json')
        })


@blueprint.route('/inmates/<uuid:inmate_id>/movements/summary', methods=['GET'])
async def get_inmate_movement_summary(inmate_id: UUID):
    """
    Get movement summary for an inmate.

    GET /api/v1/inmates/{inmate_id}/movements/summary
    """
    async with get_async_session() as session:
        service = MovementService(session)
        result = await service.get_inmate_movement_summary(inmate_id)
        return success_response(result.model_dump(mode='json'))
