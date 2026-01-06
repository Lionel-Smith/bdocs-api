"""
Housing Controller - API endpoints for housing and classification.

Endpoints:
- GET/POST /api/v1/housing/units - List/create housing units
- GET /api/v1/housing/units/{code} - Get unit by code
- GET /api/v1/housing/units/{code}/inmates - Get inmates in unit
- GET /api/v1/housing/units/overcrowded - Get overcrowded units report
- POST /api/v1/inmates/{id}/classification - Create classification
- GET /api/v1/inmates/{id}/classification - Get current classification
- POST /api/v1/housing/assignments - Create housing assignment
- GET /api/v1/inmates/{id}/housing - Get inmate housing summary
- PUT /api/v1/housing/assignments/{id}/end - End assignment
"""
from uuid import UUID

from quart import Blueprint, request, jsonify
from pydantic import ValidationError

from src.database.async_db import get_async_session
from src.modules.housing.service import (
    HousingService,
    HousingUnitNotFoundError,
    AssignmentNotFoundError,
    InvalidAssignmentError,
)
from src.modules.housing.dtos import (
    HousingUnitCreate,
    HousingUnitUpdate,
    ClassificationCreate,
    HousingAssignmentCreate,
    HousingAssignmentEnd,
)


blueprint = Blueprint('housing', __name__, url_prefix='/api/v1')


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
# Housing Unit Endpoints
# ============================================================================

@blueprint.route('/housing/units', methods=['GET'])
async def list_housing_units():
    """
    List all housing units.

    GET /api/v1/housing/units?include_inactive=false
    """
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    async with get_async_session() as session:
        service = HousingService(session)
        units = await service.get_all_units(include_inactive)
        return success_response({
            "items": [u.model_dump(mode='json') for u in units],
            "total": len(units)
        })


@blueprint.route('/housing/units', methods=['POST'])
async def create_housing_unit():
    """
    Create a new housing unit.

    POST /api/v1/housing/units
    """
    try:
        data = await request.get_json()
        unit_data = HousingUnitCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = HousingService(session)
        unit = await service.create_unit(unit_data, created_by="system")
        await session.commit()
        return success_response(unit.model_dump(mode='json'), 201)


@blueprint.route('/housing/units/overcrowded', methods=['GET'])
async def get_overcrowded_units():
    """
    Get report of overcrowded housing units.

    GET /api/v1/housing/units/overcrowded
    """
    async with get_async_session() as session:
        service = HousingService(session)
        report = await service.get_overcrowded_units()
        return success_response(report.model_dump(mode='json'))


@blueprint.route('/housing/units/<code>', methods=['GET'])
async def get_housing_unit(code: str):
    """
    Get housing unit by code.

    GET /api/v1/housing/units/{code}
    """
    async with get_async_session() as session:
        service = HousingService(session)
        try:
            unit = await service.get_unit_by_code(code)
            return success_response(unit.model_dump(mode='json'))
        except HousingUnitNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/housing/units/<code>/inmates', methods=['GET'])
async def get_unit_inmates(code: str):
    """
    Get all inmates currently assigned to a housing unit.

    GET /api/v1/housing/units/{code}/inmates
    """
    async with get_async_session() as session:
        service = HousingService(session)
        try:
            inmates = await service.get_inmates_in_unit(code)
            return success_response({
                "housing_unit_code": code.upper(),
                "items": [i.model_dump(mode='json') for i in inmates],
                "total": len(inmates)
            })
        except HousingUnitNotFoundError as e:
            return error_response(str(e), 404)


# ============================================================================
# Classification Endpoints
# ============================================================================

@blueprint.route('/inmates/<uuid:inmate_id>/classification', methods=['POST'])
async def create_classification(inmate_id: UUID):
    """
    Create a new security classification for an inmate.

    POST /api/v1/inmates/{id}/classification

    Request body:
    {
        "scores": {
            "charge_severity": 1-5,
            "prior_record": 1-5,
            "institutional_behavior": 1-5,
            "escape_risk": 1-5,
            "violence_risk": 1-5
        },
        "review_date": "YYYY-MM-DD" (optional),
        "notes": "string" (optional)
    }

    Security level is auto-calculated:
    - >= 20: MAXIMUM
    - >= 12: MEDIUM
    - < 12: MINIMUM
    """
    try:
        data = await request.get_json()
        data['inmate_id'] = str(inmate_id)
        classification_data = ClassificationCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = HousingService(session)
        # TODO: Get classified_by from auth context
        classification = await service.create_classification(classification_data)
        await session.commit()
        return success_response(classification.model_dump(mode='json'), 201)


@blueprint.route('/inmates/<uuid:inmate_id>/classification', methods=['GET'])
async def get_classification(inmate_id: UUID):
    """
    Get current classification for an inmate.

    GET /api/v1/inmates/{id}/classification?history=false
    """
    include_history = request.args.get('history', 'false').lower() == 'true'

    async with get_async_session() as session:
        service = HousingService(session)

        if include_history:
            history = await service.get_classification_history(inmate_id)
            return success_response({
                "items": [c.model_dump(mode='json') for c in history],
                "total": len(history)
            })
        else:
            classification = await service.get_inmate_classification(inmate_id)
            if not classification:
                return error_response("No classification found for this inmate", 404)
            return success_response(classification.model_dump(mode='json'))


# ============================================================================
# Housing Assignment Endpoints
# ============================================================================

@blueprint.route('/housing/assignments', methods=['POST'])
async def create_assignment():
    """
    Create a new housing assignment.

    POST /api/v1/housing/assignments

    Request body:
    {
        "inmate_id": "uuid",
        "housing_unit_id": "uuid",
        "cell_number": "string" (optional),
        "bed_number": "string" (optional),
        "reason": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        assignment_data = HousingAssignmentCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = HousingService(session)
        try:
            # TODO: Get assigned_by from auth context
            assignment = await service.create_assignment(assignment_data)
            await session.commit()
            return success_response(assignment.model_dump(mode='json'), 201)
        except HousingUnitNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidAssignmentError as e:
            return error_response(str(e), 400)


@blueprint.route('/inmates/<uuid:inmate_id>/housing', methods=['GET'])
async def get_inmate_housing(inmate_id: UUID):
    """
    Get complete housing summary for an inmate.

    GET /api/v1/inmates/{id}/housing

    Returns current assignment, current classification, and histories.
    """
    async with get_async_session() as session:
        service = HousingService(session)
        summary = await service.get_inmate_housing(inmate_id)
        return success_response(summary.model_dump(mode='json'))


@blueprint.route('/housing/assignments/<uuid:assignment_id>/end', methods=['PUT'])
async def end_assignment(assignment_id: UUID):
    """
    End a housing assignment.

    PUT /api/v1/housing/assignments/{id}/end

    Request body:
    {
        "reason": "string" (optional)
    }
    """
    try:
        data = await request.get_json() or {}
        end_data = HousingAssignmentEnd(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = HousingService(session)
        try:
            assignment = await service.end_assignment(assignment_id, end_data)
            await session.commit()
            return success_response(assignment.model_dump(mode='json'))
        except AssignmentNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidAssignmentError as e:
            return error_response(str(e), 400)
