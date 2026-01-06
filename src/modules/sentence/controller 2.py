"""
Sentence Controller - API endpoints for sentence management.

Endpoints:
1. POST /api/v1/sentences - Create sentence
2. GET /api/v1/sentences - List sentences
3. GET /api/v1/sentences/{id} - Get sentence
4. PUT /api/v1/sentences/{id} - Update sentence
5. GET /api/v1/inmates/{id}/sentences - Get inmate sentences
6. GET /api/v1/inmates/{id}/sentences/current - Get current sentence
7. POST /api/v1/sentences/{id}/adjustments - Create adjustment
8. GET /api/v1/sentences/{id}/adjustments - Get adjustments
9. GET /api/v1/sentences/releasing-soon - Get releasing soon
10. GET /api/v1/sentences/{id}/calculate-release - Calculate release
"""
from uuid import UUID

from quart import Blueprint, request, jsonify
from pydantic import ValidationError

from src.database.async_db import get_async_session
from src.modules.sentence.service import (
    SentenceService,
    SentenceNotFoundError,
    AdjustmentNotFoundError,
    InvalidSentenceError,
)
from src.modules.sentence.dtos import (
    SentenceCreate,
    SentenceUpdate,
    SentenceAdjustmentCreate,
)


blueprint = Blueprint('sentence', __name__, url_prefix='/api/v1')


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
# Sentence Endpoints
# ============================================================================

@blueprint.route('/sentences', methods=['POST'])
async def create_sentence():
    """
    Create a new sentence.

    POST /api/v1/sentences

    Request body:
    {
        "inmate_id": "uuid",
        "court_case_id": "uuid",
        "sentence_date": "YYYY-MM-DD",
        "sentence_type": "IMPRISONMENT|LIFE|DEATH|...",
        "original_term_months": 60 (for fixed terms),
        "life_sentence": false,
        "is_death_sentence": false,
        "minimum_term_months": null (for life sentences),
        "start_date": "YYYY-MM-DD",
        "time_served_days": 0,
        "sentencing_judge": "string" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        sentence_data = SentenceCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            # TODO: Get created_by from auth context
            sentence = await service.create_sentence(sentence_data)
            await session.commit()
            return success_response(sentence.model_dump(mode='json'), 201)
        except InvalidSentenceError as e:
            return error_response(str(e), 400)


@blueprint.route('/sentences', methods=['GET'])
async def list_sentences():
    """
    List all sentences.

    GET /api/v1/sentences?skip=0&limit=100
    """
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = SentenceService(session)
        result = await service.get_all_sentences(skip=skip, limit=limit)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/sentences/releasing-soon', methods=['GET'])
async def get_releasing_soon():
    """
    Get sentences with expected release within specified days.

    GET /api/v1/sentences/releasing-soon?days=30
    """
    days_ahead = int(request.args.get('days', 30))

    async with get_async_session() as session:
        service = SentenceService(session)
        result = await service.get_releasing_soon(days_ahead)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/sentences/<uuid:sentence_id>', methods=['GET'])
async def get_sentence(sentence_id: UUID):
    """
    Get a sentence by ID.

    GET /api/v1/sentences/{id}
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            sentence = await service.get_sentence(sentence_id)
            return success_response(sentence.model_dump(mode='json'))
        except SentenceNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/sentences/<uuid:sentence_id>', methods=['PUT'])
async def update_sentence(sentence_id: UUID):
    """
    Update a sentence.

    PUT /api/v1/sentences/{id}

    Request body:
    {
        "original_term_months": 72 (optional),
        "minimum_term_months": 120 (optional),
        "start_date": "YYYY-MM-DD" (optional),
        "time_served_days": 30 (optional),
        "good_time_days": 15 (optional),
        "sentencing_judge": "string" (optional),
        "actual_release_date": "YYYY-MM-DD" (optional),
        "notes": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        update_data = SentenceUpdate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            # TODO: Get updated_by from auth context
            sentence = await service.update_sentence(sentence_id, update_data)
            await session.commit()
            return success_response(sentence.model_dump(mode='json'))
        except SentenceNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/sentences/<uuid:sentence_id>/calculate-release', methods=['GET'])
async def calculate_release(sentence_id: UUID):
    """
    Calculate expected release date for a sentence.

    GET /api/v1/sentences/{id}/calculate-release

    Returns detailed calculation including:
    - Original term
    - Time served credits
    - Good time credits
    - All adjustments
    - Maximum remission (1/3 rule)
    - Expected release date
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            result = await service.calculate_release(sentence_id)
            return success_response(result.model_dump(mode='json'))
        except SentenceNotFoundError as e:
            return error_response(str(e), 404)


# ============================================================================
# Sentence Adjustment Endpoints
# ============================================================================

@blueprint.route('/sentences/<uuid:sentence_id>/adjustments', methods=['POST'])
async def create_adjustment(sentence_id: UUID):
    """
    Create a sentence adjustment.

    POST /api/v1/sentences/{id}/adjustments

    Request body:
    {
        "adjustment_type": "GOOD_TIME|REMISSION|TIME_SERVED_CREDIT|...",
        "days": 30 (positive = reduces sentence),
        "effective_date": "YYYY-MM-DD",
        "reason": "string",
        "document_reference": "string" (optional)
    }
    """
    try:
        data = await request.get_json()
        adjustment_data = SentenceAdjustmentCreate(**data)
    except ValidationError as e:
        return error_response("Validation error", 422, e.errors())
    except Exception as e:
        return error_response(f"Invalid request data: {str(e)}", 400)

    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            # TODO: Get approved_by from auth context
            adjustment = await service.create_adjustment(sentence_id, adjustment_data)
            await session.commit()
            return success_response(adjustment.model_dump(mode='json'), 201)
        except SentenceNotFoundError as e:
            return error_response(str(e), 404)


@blueprint.route('/sentences/<uuid:sentence_id>/adjustments', methods=['GET'])
async def get_adjustments(sentence_id: UUID):
    """
    Get all adjustments for a sentence.

    GET /api/v1/sentences/{id}/adjustments
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        try:
            result = await service.get_adjustments(sentence_id)
            return success_response(result.model_dump(mode='json'))
        except SentenceNotFoundError as e:
            return error_response(str(e), 404)


# ============================================================================
# Inmate Sentence Endpoints
# ============================================================================

@blueprint.route('/inmates/<uuid:inmate_id>/sentences', methods=['GET'])
async def get_inmate_sentences(inmate_id: UUID):
    """
    Get all sentences for an inmate.

    GET /api/v1/inmates/{inmate_id}/sentences
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        result = await service.get_sentences_by_inmate(inmate_id)
        return success_response({
            "inmate_id": str(inmate_id),
            **result.model_dump(mode='json')
        })


@blueprint.route('/inmates/<uuid:inmate_id>/sentences/current', methods=['GET'])
async def get_current_sentence(inmate_id: UUID):
    """
    Get the current active sentence for an inmate.

    GET /api/v1/inmates/{inmate_id}/sentences/current
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        result = await service.get_current_sentence(inmate_id)
        if not result:
            return error_response("No current sentence found for this inmate", 404)
        return success_response(result.model_dump(mode='json'))


@blueprint.route('/inmates/<uuid:inmate_id>/sentences/summary', methods=['GET'])
async def get_inmate_sentence_summary(inmate_id: UUID):
    """
    Get complete sentence summary for an inmate.

    GET /api/v1/inmates/{inmate_id}/sentences/summary

    Returns all sentences with totals and flags for life/death sentences.
    """
    async with get_async_session() as session:
        service = SentenceService(session)
        result = await service.get_inmate_sentence_summary(inmate_id)
        return success_response(result.model_dump(mode='json'))
