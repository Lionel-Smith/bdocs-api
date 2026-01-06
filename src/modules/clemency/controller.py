"""
Clemency Controller - API endpoints for clemency petitions.

Endpoints:
- POST   /api/v1/clemency/petitions              Create petition
- GET    /api/v1/clemency/petitions              List petitions (with filters)
- GET    /api/v1/clemency/petitions/statistics   Get statistics
- GET    /api/v1/clemency/petitions/pending-committee    Committee queue
- GET    /api/v1/clemency/petitions/pending-minister     Minister queue
- GET    /api/v1/clemency/petitions/{id}         Get petition by ID
- PUT    /api/v1/clemency/petitions/{id}         Update petition
- DELETE /api/v1/clemency/petitions/{id}         Delete petition
- PUT    /api/v1/clemency/petitions/{id}/status  Advance status
- GET    /api/v1/clemency/petitions/{id}/history Get status history
- GET    /api/v1/inmates/{inmate_id}/clemency    Inmate clemency summary
"""
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import PetitionStatus, PetitionType
from src.modules.clemency.service import ClemencyService
from src.modules.clemency.dtos import (
    ClemencyPetitionCreate,
    ClemencyPetitionUpdate,
    ClemencyStatusUpdate,
    ClemencyPetitionResponse,
    ClemencyPetitionListResponse,
    ClemencyStatusHistoryResponse,
    ClemencyStatusHistoryListResponse,
)

# Create blueprint
clemency_bp = Blueprint('clemency', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = clemency_bp


# ============================================================================
# Petition CRUD Endpoints
# ============================================================================

@clemency_bp.route('/clemency/petitions', methods=['POST'])
async def create_petition():
    """
    Create a new clemency petition.

    Request body: ClemencyPetitionCreate
    Returns: ClemencyPetitionResponse
    """
    try:
        data = await request.get_json()
        petition_data = ClemencyPetitionCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ClemencyService(session)
            petition = await service.create_petition(petition_data, created_by)
            await session.commit()

            response = ClemencyPetitionResponse.model_validate(petition)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create petition: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions', methods=['GET'])
async def list_petitions():
    """
    List clemency petitions with optional filters.

    Query params:
    - status: Filter by PetitionStatus
    - type: Filter by PetitionType
    - inmate_id: Filter by inmate UUID

    Returns: ClemencyPetitionListResponse
    """
    try:
        status_filter = request.args.get('status')
        type_filter = request.args.get('type')
        inmate_id = request.args.get('inmate_id')

        async with get_async_session() as session:
            service = ClemencyService(session)

            if inmate_id:
                petitions = await service.get_by_inmate(UUID(inmate_id))
            elif status_filter:
                status = PetitionStatus(status_filter)
                petitions = await service.get_by_status(status)
            elif type_filter:
                ptype = PetitionType(type_filter)
                petitions = await service.get_by_type(ptype)
            else:
                # Default: get all non-deleted petitions
                petitions = await service.get_by_status(PetitionStatus.SUBMITTED)
                # Get all statuses
                all_petitions = []
                for status in PetitionStatus:
                    status_petitions = await service.get_by_status(status)
                    all_petitions.extend(status_petitions)
                petitions = all_petitions

            response = ClemencyPetitionListResponse(
                items=[ClemencyPetitionResponse.model_validate(p) for p in petitions],
                total=len(petitions)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to list petitions: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/<uuid:petition_id>', methods=['GET'])
async def get_petition(petition_id: UUID):
    """
    Get a clemency petition by ID.

    Returns: ClemencyPetitionResponse
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            petition = await service.get_petition(petition_id)

            if not petition:
                return jsonify({"error": "Petition not found"}), 404

            response = ClemencyPetitionResponse.model_validate(petition)
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get petition: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/<uuid:petition_id>', methods=['PUT'])
async def update_petition(petition_id: UUID):
    """
    Update a clemency petition (non-status fields).

    Use PUT /petitions/{id}/status to change status.

    Request body: ClemencyPetitionUpdate
    Returns: ClemencyPetitionResponse
    """
    try:
        data = await request.get_json()
        update_data = ClemencyPetitionUpdate(**data)

        async with get_async_session() as session:
            service = ClemencyService(session)
            petition = await service.update_petition(petition_id, update_data)
            await session.commit()

            if not petition:
                return jsonify({"error": "Petition not found"}), 404

            response = ClemencyPetitionResponse.model_validate(petition)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update petition: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/<uuid:petition_id>', methods=['DELETE'])
async def delete_petition(petition_id: UUID):
    """
    Soft delete a clemency petition.

    Cannot delete petitions in terminal states (GRANTED, DENIED).
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            success = await service.delete_petition(petition_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Petition not found"}), 404

            return jsonify({"message": "Petition deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete petition: {str(e)}"}), 500


# ============================================================================
# Status Workflow Endpoints
# ============================================================================

@clemency_bp.route('/clemency/petitions/<uuid:petition_id>/status', methods=['PUT'])
async def advance_petition_status(petition_id: UUID):
    """
    Advance petition status with workflow validation.

    Validates that the transition is allowed per the constitutional workflow.
    On GRANTED, auto-creates a SentenceAdjustment with CLEMENCY_REDUCTION.

    Request body: ClemencyStatusUpdate
    Returns: ClemencyPetitionResponse
    """
    try:
        data = await request.get_json()
        status_update = ClemencyStatusUpdate(**data)

        # Get user ID from auth context (placeholder)
        changed_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ClemencyService(session)
            petition = await service.advance_status(
                petition_id,
                status_update,
                changed_by
            )
            await session.commit()

            response = ClemencyPetitionResponse.model_validate(petition)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/<uuid:petition_id>/history', methods=['GET'])
async def get_petition_history(petition_id: UUID):
    """
    Get status history for a petition.

    Returns: ClemencyStatusHistoryListResponse
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)

            # Verify petition exists
            petition = await service.get_petition(petition_id)
            if not petition:
                return jsonify({"error": "Petition not found"}), 404

            history = await service.get_petition_history(petition_id)

            response = ClemencyStatusHistoryListResponse(
                items=[
                    ClemencyStatusHistoryResponse.model_validate(h)
                    for h in history
                ],
                total=len(history)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500


# ============================================================================
# Queue Endpoints
# ============================================================================

@clemency_bp.route('/clemency/petitions/pending-committee', methods=['GET'])
async def get_pending_committee():
    """
    Get petitions awaiting Advisory Committee review.

    Returns: ClemencyPetitionListResponse
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            petitions = await service.get_pending_committee()

            response = ClemencyPetitionListResponse(
                items=[ClemencyPetitionResponse.model_validate(p) for p in petitions],
                total=len(petitions)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get pending committee: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/pending-minister', methods=['GET'])
async def get_pending_minister():
    """
    Get petitions awaiting Minister review.

    Returns: ClemencyPetitionListResponse
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            petitions = await service.get_pending_minister()

            response = ClemencyPetitionListResponse(
                items=[ClemencyPetitionResponse.model_validate(p) for p in petitions],
                total=len(petitions)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get pending minister: {str(e)}"}), 500


@clemency_bp.route('/clemency/petitions/pending-governor-general', methods=['GET'])
async def get_pending_governor_general():
    """
    Get petitions awaiting Governor-General decision.

    Returns: ClemencyPetitionListResponse
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            petitions = await service.get_pending_governor_general()

            response = ClemencyPetitionListResponse(
                items=[ClemencyPetitionResponse.model_validate(p) for p in petitions],
                total=len(petitions)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get pending GG: {str(e)}"}), 500


# ============================================================================
# Statistics Endpoint
# ============================================================================

@clemency_bp.route('/clemency/petitions/statistics', methods=['GET'])
async def get_statistics():
    """
    Get clemency petition statistics.

    Returns: ClemencyStatistics
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            stats = await service.get_statistics()

            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


# ============================================================================
# Inmate Clemency Endpoint (separate blueprint)
# ============================================================================

@clemency_bp.route('/inmates/<uuid:inmate_id>/clemency', methods=['GET'])
async def get_inmate_clemency(inmate_id: UUID):
    """
    Get clemency summary for an inmate.

    Returns: InmateClemencySummary
    """
    try:
        async with get_async_session() as session:
            service = ClemencyService(session)
            summary = await service.get_inmate_summary(inmate_id)

            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get inmate clemency: {str(e)}"}), 500
