"""
Court Controller - API endpoints for court cases and appearances.

Endpoints:
1. POST /api/v1/court/cases - Create case
2. GET /api/v1/court/cases - List cases
3. GET /api/v1/court/cases/{id} - Get case
4. PUT /api/v1/court/cases/{id} - Update case
5. GET /api/v1/inmates/{id}/cases - Get inmate cases
6. POST /api/v1/court/appearances - Create appearance
7. GET /api/v1/court/appearances - List appearances (date range)
8. GET /api/v1/court/appearances/{id} - Get appearance
9. PUT /api/v1/court/appearances/{id}/outcome - Record outcome
10. GET /api/v1/court/appearances/upcoming - Get upcoming
11. GET /api/v1/inmates/{id}/appearances - Get inmate appearances
"""
from datetime import datetime
from uuid import UUID

from quart import Blueprint, request, jsonify
from pydantic import ValidationError

from src.database.async_db import get_async_session
from src.modules.court.service import (
    CourtService,
    CourtCaseNotFoundError,
    CourtAppearanceNotFoundError,
    DuplicateCaseNumberError,
    InvalidAppearanceError,
)
from src.modules.court.dtos import (
    CourtCaseCreate,
    CourtCaseUpdate,
    CourtAppearanceCreate,
    CourtAppearanceUpdate,
    CourtAppearanceOutcomeUpdate,
)


blueprint = Blueprint('court', __name__, url_prefix='/api/v1')


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
# Court Case Endpoints
# ============================================================================

@blueprint.route('/court/cases', methods=['POST'])
async def create_court_case():
    """
    Create a new court case.

    POST /api/v1/court/cases

    Request body:
    {
        "inmate_id": "uuid",
        "case_number": "MC-2026-00123",
        "court_type": "MAGISTRATES|SUPREME|...",
        "charges": [{"offense": "...", "statute": "...", "count": 1, "plea": null}],
        "filing_date": "YYYY-MM-DD",
        "presiding_judge": "string" (optional),
        "prosecutor": "string" (optional),
        "defense_attorney": "string" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        case_data = CourtCaseCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = CourtService(session)
        try:
            # TODO: Get created_by from auth context
            court_case = await service.create_case(case_data)
            await session.commit()
            return success_response(court_case.model_dump(mode='json'), 201)
        except DuplicateCaseNumberError as e:
            return error_response(str(e), 409)


@blueprint.route('/court/cases', methods=['GET'])
async def list_court_cases():
    """
    List all court cases.

    GET /api/v1/court/cases?skip=0&limit=100
    """
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_all_cases(skip=skip, limit=limit)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/court/cases/<uuid:case_id>', methods=['GET'])
async def get_court_case(case_id: UUID):
    """
    Get a court case by ID.

    GET /api/v1/court/cases/{id}
    """
    async with get_async_session() as session:
        service = CourtService(session)
        try:
            court_case = await service.get_case(case_id)
            return success_response(court_case.model_dump(mode='json'))
        except CourtCaseNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/court/cases/<uuid:case_id>', methods=['PUT'])
async def update_court_case(case_id: UUID):
    """
    Update a court case.

    PUT /api/v1/court/cases/{id}

    Request body:
    {
        "status": "PENDING|ACTIVE|ADJUDICATED|DISMISSED|APPEALED" (optional),
        "presiding_judge": "string" (optional),
        "prosecutor": "string" (optional),
        "defense_attorney": "string" (optional),
        "charges": [...] (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        update_data = CourtCaseUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = CourtService(session)
        try:
            # TODO: Get updated_by from auth context
            court_case = await service.update_case(case_id, update_data)
            await session.commit()
            return success_response(court_case.model_dump(mode='json'))
        except CourtCaseNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/inmates/<uuid:inmate_id>/cases', methods=['GET'])
async def get_inmate_cases(inmate_id: UUID):
    """
    Get all court cases for an inmate.

    GET /api/v1/inmates/{inmate_id}/cases
    """
    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_cases_by_inmate(inmate_id)
        return success_response({
            "inmate_id": str(inmate_id),
            **result.model_dump(mode='json')
        })


# ============================================================================
# Court Appearance Endpoints
# ============================================================================

@blueprint.route('/court/appearances', methods=['POST'])
async def create_court_appearance():
    """
    Create a new court appearance.

    POST /api/v1/court/appearances

    Request body:
    {
        "court_case_id": "uuid",
        "inmate_id": "uuid",
        "appearance_date": "ISO datetime",
        "appearance_type": "ARRAIGNMENT|BAIL_HEARING|...",
        "court_location": "string",
        "notes": "string" (optional),
        "auto_create_movement": true (default, creates COURT_TRANSPORT)
    }
    """
    try:
        data = await request.get_json()
        appearance_data = CourtAppearanceCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = CourtService(session)
        try:
            # TODO: Get created_by from auth context
            appearance = await service.create_appearance(appearance_data)
            await session.commit()
            return success_response(appearance.model_dump(mode='json'), 201)
        except CourtCaseNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/court/appearances', methods=['GET'])
async def list_court_appearances():
    """
    List court appearances with optional date range filter.

    GET /api/v1/court/appearances?from_date=&to_date=
    """
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    # Default to next 30 days if no date range provided
    if from_date_str:
        from_date = datetime.fromisoformat(from_date_str)
    else:
        from_date = datetime.utcnow()

    if to_date_str:
        to_date = datetime.fromisoformat(to_date_str)
    else:
        from datetime import timedelta
        to_date = from_date + timedelta(days=30)

    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_appearances_by_date_range(from_date, to_date)
        return success_response({
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            **result.model_dump(mode='json')
        })


@blueprint.route('/court/appearances/upcoming', methods=['GET'])
async def get_upcoming_appearances():
    """
    Get upcoming court appearances (no outcome yet).

    GET /api/v1/court/appearances/upcoming?days=7
    """
    days_ahead = int(request.args.get('days', 7))

    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_upcoming_appearances(days_ahead)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/court/appearances/<uuid:appearance_id>', methods=['GET'])
async def get_court_appearance(appearance_id: UUID):
    """
    Get a court appearance by ID.

    GET /api/v1/court/appearances/{id}
    """
    async with get_async_session() as session:
        service = CourtService(session)
        try:
            appearance = await service.get_appearance(appearance_id)
            return success_response(appearance.model_dump(mode='json'))
        except CourtAppearanceNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/court/appearances/<uuid:appearance_id>', methods=['PUT'])
async def update_court_appearance(appearance_id: UUID):
    """
    Update a court appearance (before it occurs).

    PUT /api/v1/court/appearances/{id}

    Request body:
    {
        "appearance_date": "ISO datetime" (optional),
        "court_location": "string" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        update_data = CourtAppearanceUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = CourtService(session)
        try:
            # TODO: Get updated_by from auth context
            appearance = await service.update_appearance(appearance_id, update_data)
            await session.commit()
            return success_response(appearance.model_dump(mode='json'))
        except CourtAppearanceNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidAppearanceError as e:
            return error_response(str(e), 400)


@blueprint.route('/court/appearances/<uuid:appearance_id>/outcome', methods=['PUT'])
async def record_appearance_outcome(appearance_id: UUID):
    """
    Record the outcome of a court appearance.

    PUT /api/v1/court/appearances/{id}/outcome

    Request body:
    {
        "outcome": "ADJOURNED|BAIL_GRANTED|BAIL_DENIED|CONVICTED|ACQUITTED|SENTENCED|REMANDED",
        "next_appearance_date": "ISO datetime" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        outcome_data = CourtAppearanceOutcomeUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = CourtService(session)
        try:
            # TODO: Get updated_by from auth context
            appearance = await service.record_outcome(appearance_id, outcome_data)
            await session.commit()
            return success_response(appearance.model_dump(mode='json'))
        except CourtAppearanceNotFoundError as e:
            return error_response(str(e), 404)
        except InvalidAppearanceError as e:
            return error_response(str(e), 400)


@blueprint.route('/inmates/<uuid:inmate_id>/appearances', methods=['GET'])
async def get_inmate_appearances(inmate_id: UUID):
    """
    Get all court appearances for an inmate.

    GET /api/v1/inmates/{inmate_id}/appearances
    """
    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_appearances_by_inmate(inmate_id)
        return success_response({
            "inmate_id": str(inmate_id),
            **result.model_dump(mode='json')
        })


# ============================================================================
# Court Summary Endpoint
# ============================================================================

@blueprint.route('/inmates/<uuid:inmate_id>/court/summary', methods=['GET'])
async def get_inmate_court_summary(inmate_id: UUID):
    """
    Get complete court summary for an inmate.

    GET /api/v1/inmates/{inmate_id}/court/summary

    Returns cases, appearances, and statistics.
    """
    async with get_async_session() as session:
        service = CourtService(session)
        result = await service.get_inmate_court_summary(inmate_id)
        return success_response(result.model_dump(mode='json'))
