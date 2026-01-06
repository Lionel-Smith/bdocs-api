"""
Case Management Controller - API endpoints for case management.

Endpoints:
- POST   /api/v1/cases/assignments                  Assign case officer
- GET    /api/v1/cases/assignments                  List assignments
- PUT    /api/v1/cases/assignments/{id}/end         End assignment
- GET    /api/v1/cases/officers/{id}/caseload       Get officer caseload
- GET    /api/v1/inmates/{id}/case                  Get inmate case summary
- POST   /api/v1/cases/notes                        Add case note
- GET    /api/v1/inmates/{id}/case/notes            Get inmate case notes
- POST   /api/v1/inmates/{id}/goals                 Create goal
- GET    /api/v1/inmates/{id}/goals                 Get inmate goals
- PUT    /api/v1/cases/goals/{id}                   Update goal
- PUT    /api/v1/cases/goals/{id}/progress          Update goal progress
- DELETE /api/v1/cases/goals/{id}                   Delete goal
- GET    /api/v1/cases/goals/overdue                Get overdue goals
- GET    /api/v1/cases/statistics                   Get statistics
"""
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import NoteType, GoalType, GoalStatus
from src.modules.case.service import CaseService
from src.modules.case.dtos import (
    CaseAssignmentCreate,
    CaseAssignmentEnd,
    CaseAssignmentResponse,
    CaseAssignmentListResponse,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteListResponse,
    RehabilitationGoalCreate,
    RehabilitationGoalUpdate,
    RehabilitationGoalProgressUpdate,
    RehabilitationGoalResponse,
    RehabilitationGoalListResponse,
)

# Create blueprint
case_bp = Blueprint('case', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = case_bp


# ============================================================================
# Case Assignment Endpoints
# ============================================================================

@case_bp.route('/cases/assignments', methods=['POST'])
async def assign_case_officer():
    """
    Assign a case officer to an inmate.

    Automatically ends any existing active assignment.

    Request body: CaseAssignmentCreate
    Returns: CaseAssignmentResponse
    """
    try:
        data = await request.get_json()
        assignment_data = CaseAssignmentCreate(**data)

        # Get user ID from auth context (placeholder)
        assigned_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = CaseService(session)
            assignment = await service.assign_case_officer(assignment_data, assigned_by)
            await session.commit()

            response = CaseAssignmentResponse.model_validate(assignment)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to assign case officer: {str(e)}"}), 500


@case_bp.route('/cases/assignments', methods=['GET'])
async def list_assignments():
    """
    List case assignments.

    Query params:
    - active: Filter active only (true/false)

    Returns: CaseAssignmentListResponse
    """
    try:
        active_filter = request.args.get('active', '').lower() == 'true'

        async with get_async_session() as session:
            service = CaseService(session)
            assignments = await service.get_all_assignments(active_only=active_filter)

            response = CaseAssignmentListResponse(
                items=[CaseAssignmentResponse.model_validate(a) for a in assignments],
                total=len(assignments)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list assignments: {str(e)}"}), 500


@case_bp.route('/cases/assignments/<uuid:assignment_id>/end', methods=['PUT'])
async def end_assignment(assignment_id: UUID):
    """
    End a case assignment.

    Request body: CaseAssignmentEnd
    Returns: CaseAssignmentResponse
    """
    try:
        data = await request.get_json()
        end_data = CaseAssignmentEnd(**data)

        async with get_async_session() as session:
            service = CaseService(session)
            assignment = await service.end_assignment(assignment_id, end_data)
            await session.commit()

            response = CaseAssignmentResponse.model_validate(assignment)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to end assignment: {str(e)}"}), 500


@case_bp.route('/cases/officers/<uuid:officer_id>/caseload', methods=['GET'])
async def get_officer_caseload(officer_id: UUID):
    """
    Get a case officer's current caseload.

    Returns: CaseOfficerCaseload
    """
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            caseload = await service.get_caseload(officer_id)

            return jsonify(caseload.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get caseload: {str(e)}"}), 500


# ============================================================================
# Inmate Case Summary Endpoint
# ============================================================================

@case_bp.route('/inmates/<uuid:inmate_id>/case', methods=['GET'])
async def get_inmate_case(inmate_id: UUID):
    """
    Get comprehensive case summary for an inmate.

    Returns: InmateCaseSummary
    """
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            summary = await service.get_inmate_case_summary(inmate_id)

            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get case summary: {str(e)}"}), 500


# ============================================================================
# Case Note Endpoints
# ============================================================================

@case_bp.route('/cases/notes', methods=['POST'])
async def add_case_note():
    """
    Add a case note for an inmate.

    Note is linked to the inmate's current active assignment.

    Request body: CaseNoteCreate
    Returns: CaseNoteResponse
    """
    try:
        data = await request.get_json()
        note_data = CaseNoteCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = CaseService(session)
            note = await service.add_case_note(note_data, created_by)
            await session.commit()

            response = CaseNoteResponse.model_validate(note)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to add case note: {str(e)}"}), 500


@case_bp.route('/inmates/<uuid:inmate_id>/case/notes', methods=['GET'])
async def get_inmate_case_notes(inmate_id: UUID):
    """
    Get case notes for an inmate.

    Query params:
    - include_confidential: Include confidential notes (true/false)
    - limit: Max number of notes to return

    Returns: CaseNoteListResponse
    """
    try:
        include_confidential = request.args.get('include_confidential', '').lower() == 'true'
        limit = request.args.get('limit', type=int)

        async with get_async_session() as session:
            service = CaseService(session)
            notes = await service.get_inmate_notes(
                inmate_id, include_confidential, limit
            )

            response = CaseNoteListResponse(
                items=[CaseNoteResponse.model_validate(n) for n in notes],
                total=len(notes)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get case notes: {str(e)}"}), 500


# ============================================================================
# Rehabilitation Goal Endpoints
# ============================================================================

@case_bp.route('/inmates/<uuid:inmate_id>/goals', methods=['POST'])
async def create_goal(inmate_id: UUID):
    """
    Create a rehabilitation goal for an inmate.

    Request body: RehabilitationGoalCreate
    Returns: RehabilitationGoalResponse
    """
    try:
        data = await request.get_json()
        goal_data = RehabilitationGoalCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = CaseService(session)
            goal = await service.create_goal(inmate_id, goal_data, created_by)
            await session.commit()

            response = RehabilitationGoalResponse(
                id=goal.id,
                inmate_id=goal.inmate_id,
                goal_type=GoalType(goal.goal_type),
                title=goal.title,
                description=goal.description,
                target_date=goal.target_date,
                status=GoalStatus(goal.status),
                progress_percentage=goal.progress_percentage,
                completion_date=goal.completion_date,
                is_overdue=goal.is_overdue,
                notes=goal.notes,
                created_by=goal.created_by,
                inserted_date=goal.inserted_date,
                updated_date=goal.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create goal: {str(e)}"}), 500


@case_bp.route('/inmates/<uuid:inmate_id>/goals', methods=['GET'])
async def get_inmate_goals(inmate_id: UUID):
    """
    Get rehabilitation goals for an inmate.

    Returns: RehabilitationGoalListResponse
    """
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            goals = await service.get_inmate_goals(inmate_id)

            items = [
                RehabilitationGoalResponse(
                    id=g.id,
                    inmate_id=g.inmate_id,
                    goal_type=GoalType(g.goal_type),
                    title=g.title,
                    description=g.description,
                    target_date=g.target_date,
                    status=GoalStatus(g.status),
                    progress_percentage=g.progress_percentage,
                    completion_date=g.completion_date,
                    is_overdue=g.is_overdue,
                    notes=g.notes,
                    created_by=g.created_by,
                    inserted_date=g.inserted_date,
                    updated_date=g.updated_date
                )
                for g in goals
            ]

            response = RehabilitationGoalListResponse(
                items=items,
                total=len(items)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get goals: {str(e)}"}), 500


@case_bp.route('/cases/goals/<uuid:goal_id>', methods=['PUT'])
async def update_goal(goal_id: UUID):
    """
    Update a rehabilitation goal.

    Request body: RehabilitationGoalUpdate
    Returns: RehabilitationGoalResponse
    """
    try:
        data = await request.get_json()
        update_data = RehabilitationGoalUpdate(**data)

        async with get_async_session() as session:
            service = CaseService(session)
            goal = await service.update_goal(goal_id, update_data)
            await session.commit()

            if not goal:
                return jsonify({"error": "Goal not found"}), 404

            response = RehabilitationGoalResponse(
                id=goal.id,
                inmate_id=goal.inmate_id,
                goal_type=GoalType(goal.goal_type),
                title=goal.title,
                description=goal.description,
                target_date=goal.target_date,
                status=GoalStatus(goal.status),
                progress_percentage=goal.progress_percentage,
                completion_date=goal.completion_date,
                is_overdue=goal.is_overdue,
                notes=goal.notes,
                created_by=goal.created_by,
                inserted_date=goal.inserted_date,
                updated_date=goal.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update goal: {str(e)}"}), 500


@case_bp.route('/cases/goals/<uuid:goal_id>/progress', methods=['PUT'])
async def update_goal_progress(goal_id: UUID):
    """
    Update goal progress.

    Auto-completes goal if progress reaches 100%.

    Request body: RehabilitationGoalProgressUpdate
    Returns: RehabilitationGoalResponse
    """
    try:
        data = await request.get_json()
        progress_data = RehabilitationGoalProgressUpdate(**data)

        async with get_async_session() as session:
            service = CaseService(session)
            goal = await service.update_goal_progress(goal_id, progress_data)
            await session.commit()

            response = RehabilitationGoalResponse(
                id=goal.id,
                inmate_id=goal.inmate_id,
                goal_type=GoalType(goal.goal_type),
                title=goal.title,
                description=goal.description,
                target_date=goal.target_date,
                status=GoalStatus(goal.status),
                progress_percentage=goal.progress_percentage,
                completion_date=goal.completion_date,
                is_overdue=goal.is_overdue,
                notes=goal.notes,
                created_by=goal.created_by,
                inserted_date=goal.inserted_date,
                updated_date=goal.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update progress: {str(e)}"}), 500


@case_bp.route('/cases/goals/<uuid:goal_id>', methods=['DELETE'])
async def delete_goal(goal_id: UUID):
    """Soft delete a rehabilitation goal."""
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            success = await service.delete_goal(goal_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Goal not found"}), 404

            return jsonify({"message": "Goal deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete goal: {str(e)}"}), 500


@case_bp.route('/cases/goals/overdue', methods=['GET'])
async def get_overdue_goals():
    """
    Get all overdue rehabilitation goals.

    Returns: RehabilitationGoalListResponse
    """
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            goals = await service.get_overdue_goals()

            items = [
                RehabilitationGoalResponse(
                    id=g.id,
                    inmate_id=g.inmate_id,
                    goal_type=GoalType(g.goal_type),
                    title=g.title,
                    description=g.description,
                    target_date=g.target_date,
                    status=GoalStatus(g.status),
                    progress_percentage=g.progress_percentage,
                    completion_date=g.completion_date,
                    is_overdue=g.is_overdue,
                    notes=g.notes,
                    created_by=g.created_by,
                    inserted_date=g.inserted_date,
                    updated_date=g.updated_date
                )
                for g in goals
            ]

            response = RehabilitationGoalListResponse(
                items=items,
                total=len(items)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get overdue goals: {str(e)}"}), 500


# ============================================================================
# Statistics Endpoint
# ============================================================================

@case_bp.route('/cases/statistics', methods=['GET'])
async def get_statistics():
    """
    Get overall case management statistics.

    Returns: CaseStatistics
    """
    try:
        async with get_async_session() as session:
            service = CaseService(session)
            stats = await service.get_statistics()

            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500
