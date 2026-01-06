"""
Work Release Controller - API endpoints for work release operations.

Endpoints organized by entity:

EMPLOYERS:
- POST   /api/v1/work-release/employers                    Create employer
- GET    /api/v1/work-release/employers                    List employers
- GET    /api/v1/work-release/employers/available          List available employers
- GET    /api/v1/work-release/employers/{id}               Get employer
- PUT    /api/v1/work-release/employers/{id}               Update employer
- PUT    /api/v1/work-release/employers/{id}/approve       Approve employer
- DELETE /api/v1/work-release/employers/{id}               Delete employer

ASSIGNMENTS:
- POST   /api/v1/work-release/assignments                  Create assignment
- GET    /api/v1/work-release/assignments                  List assignments
- GET    /api/v1/work-release/assignments/pending          List pending approvals
- GET    /api/v1/work-release/assignments/active           List active
- GET    /api/v1/work-release/assignments/{id}             Get assignment
- PUT    /api/v1/work-release/assignments/{id}             Update assignment
- PUT    /api/v1/work-release/assignments/{id}/approve     Approve assignment
- PUT    /api/v1/work-release/assignments/{id}/activate    Activate assignment
- PUT    /api/v1/work-release/assignments/{id}/suspend     Suspend assignment
- PUT    /api/v1/work-release/assignments/{id}/reinstate   Reinstate assignment
- PUT    /api/v1/work-release/assignments/{id}/complete    Complete assignment
- PUT    /api/v1/work-release/assignments/{id}/terminate   Terminate assignment
- GET    /api/v1/inmates/{id}/work-release                 Get inmate summary

LOGS:
- POST   /api/v1/work-release/logs/departure               Log departure
- PUT    /api/v1/work-release/logs/{id}/return             Log return
- PUT    /api/v1/work-release/logs/{id}/no-return          Mark no return
- GET    /api/v1/work-release/logs/daily                   Get daily logs
- GET    /api/v1/work-release/logs/unresolved              Get unresolved logs
- GET    /api/v1/work-release/assignments/{id}/logs        Get assignment logs

REPORTS:
- GET    /api/v1/work-release/statistics                   Get statistics
- GET    /api/v1/work-release/daily-report                 Get daily report
"""
from datetime import date
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import WorkReleaseStatus, LogStatus
from src.modules.work_release.service import WorkReleaseService
from src.modules.work_release.dtos import (
    WorkReleaseEmployerCreate,
    WorkReleaseEmployerUpdate,
    WorkReleaseEmployerApprove,
    WorkReleaseEmployerResponse,
    WorkReleaseEmployerListResponse,
    WorkReleaseAssignmentCreate,
    WorkReleaseAssignmentUpdate,
    WorkReleaseAssignmentResponse,
    WorkReleaseAssignmentListResponse,
    WorkReleaseLogDeparture,
    WorkReleaseLogReturn,
    WorkReleaseLogResponse,
    WorkReleaseLogListResponse,
)

# Create blueprint
work_release_bp = Blueprint('work_release', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = work_release_bp


# ============================================================================
# Employer Endpoints
# ============================================================================

@work_release_bp.route('/work-release/employers', methods=['POST'])
async def create_employer():
    """
    Create a new work release employer.

    Request body: WorkReleaseEmployerCreate
    Returns: WorkReleaseEmployerResponse (201)
    """
    try:
        data = await request.get_json()
        employer_data = WorkReleaseEmployerCreate(**data)

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employer = await service.create_employer(employer_data)
            await session.commit()

            response = WorkReleaseEmployerResponse.model_validate(employer)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create employer: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers', methods=['GET'])
async def list_employers():
    """
    List all work release employers.

    Query params:
    - approved: Filter approved only (true/false)
    - active: Filter active only (true/false)

    Returns: WorkReleaseEmployerListResponse
    """
    try:
        approved_only = request.args.get('approved', '').lower() == 'true'
        active_only = request.args.get('active', '').lower() == 'true'

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employers = await service.get_all_employers(approved_only, active_only)

            response = WorkReleaseEmployerListResponse(
                items=[WorkReleaseEmployerResponse.model_validate(e) for e in employers],
                total=len(employers)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list employers: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers/available', methods=['GET'])
async def list_available_employers():
    """
    List employers that can accept new inmates.

    These are approved, active, with valid MOU.

    Returns: WorkReleaseEmployerListResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employers = await service.get_available_employers()

            response = WorkReleaseEmployerListResponse(
                items=[WorkReleaseEmployerResponse.model_validate(e) for e in employers],
                total=len(employers)
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list available employers: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers/<uuid:employer_id>', methods=['GET'])
async def get_employer(employer_id: UUID):
    """
    Get a specific employer.

    Returns: WorkReleaseEmployerResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employer = await service.get_employer(employer_id)

            if not employer:
                return jsonify({"error": "Employer not found"}), 404

            response = WorkReleaseEmployerResponse.model_validate(employer)
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get employer: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers/<uuid:employer_id>', methods=['PUT'])
async def update_employer(employer_id: UUID):
    """
    Update employer details.

    Request body: WorkReleaseEmployerUpdate
    Returns: WorkReleaseEmployerResponse
    """
    try:
        data = await request.get_json()
        update_data = WorkReleaseEmployerUpdate(**data)

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employer = await service.update_employer(employer_id, update_data)
            await session.commit()

            if not employer:
                return jsonify({"error": "Employer not found"}), 404

            response = WorkReleaseEmployerResponse.model_validate(employer)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update employer: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers/<uuid:employer_id>/approve', methods=['PUT'])
async def approve_employer(employer_id: UUID):
    """
    Approve an employer for work release programme.

    Request body: WorkReleaseEmployerApprove
    Returns: WorkReleaseEmployerResponse
    """
    try:
        data = await request.get_json()
        approve_data = WorkReleaseEmployerApprove(**data)

        # Get user ID from auth context (placeholder)
        approved_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            employer = await service.approve_employer(
                employer_id, approve_data, approved_by
            )
            await session.commit()

            if not employer:
                return jsonify({"error": "Employer not found"}), 404

            response = WorkReleaseEmployerResponse.model_validate(employer)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to approve employer: {str(e)}"}), 500


@work_release_bp.route('/work-release/employers/<uuid:employer_id>', methods=['DELETE'])
async def delete_employer(employer_id: UUID):
    """
    Soft delete an employer.

    Cannot delete employers with active assignments.
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            success = await service.delete_employer(employer_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Employer not found"}), 404

            return jsonify({"message": "Employer deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete employer: {str(e)}"}), 500


# ============================================================================
# Assignment Endpoints
# ============================================================================

@work_release_bp.route('/work-release/assignments', methods=['POST'])
async def create_assignment():
    """
    Create a work release assignment.

    Request body: WorkReleaseAssignmentCreate
    Returns: WorkReleaseAssignmentResponse (201)
    """
    try:
        data = await request.get_json()
        assignment_data = WorkReleaseAssignmentCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.create_assignment(assignment_data, created_by)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments', methods=['GET'])
async def list_assignments():
    """
    List all work release assignments.

    Query params:
    - status: Filter by status

    Returns: WorkReleaseAssignmentListResponse
    """
    try:
        status_filter = request.args.get('status')

        async with get_async_session() as session:
            service = WorkReleaseService(session)

            if status_filter:
                assignments = await service.assignment_repo.get_by_status(status_filter.upper())
            else:
                # Get all non-deleted assignments
                assignments = await service.assignment_repo.get_by_status(
                    WorkReleaseStatus.ACTIVE.value
                ) + await service.assignment_repo.get_by_status(
                    WorkReleaseStatus.PENDING_APPROVAL.value
                ) + await service.assignment_repo.get_by_status(
                    WorkReleaseStatus.APPROVED.value
                )

            items = [
                WorkReleaseAssignmentResponse(
                    id=a.id,
                    inmate_id=a.inmate_id,
                    employer_id=a.employer_id,
                    employer_name=a.employer.name if a.employer else None,
                    position_title=a.position_title,
                    start_date=a.start_date,
                    end_date=a.end_date,
                    status=a.status,
                    hourly_rate=a.hourly_rate,
                    work_schedule=a.work_schedule,
                    supervisor_name=a.supervisor_name,
                    supervisor_phone=a.supervisor_phone,
                    approved_by=a.approved_by,
                    approval_date=a.approval_date,
                    termination_reason=a.termination_reason,
                    notes=a.notes,
                    created_by=a.created_by,
                    inserted_date=a.inserted_date,
                    updated_date=a.updated_date
                )
                for a in assignments
            ]

            response = WorkReleaseAssignmentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list assignments: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/pending', methods=['GET'])
async def list_pending_assignments():
    """
    List assignments pending approval.

    Returns: WorkReleaseAssignmentListResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignments = await service.get_pending_approvals()

            items = [
                WorkReleaseAssignmentResponse(
                    id=a.id,
                    inmate_id=a.inmate_id,
                    employer_id=a.employer_id,
                    employer_name=a.employer.name if a.employer else None,
                    position_title=a.position_title,
                    start_date=a.start_date,
                    end_date=a.end_date,
                    status=a.status,
                    hourly_rate=a.hourly_rate,
                    work_schedule=a.work_schedule,
                    supervisor_name=a.supervisor_name,
                    supervisor_phone=a.supervisor_phone,
                    approved_by=a.approved_by,
                    approval_date=a.approval_date,
                    termination_reason=a.termination_reason,
                    notes=a.notes,
                    created_by=a.created_by,
                    inserted_date=a.inserted_date,
                    updated_date=a.updated_date
                )
                for a in assignments
            ]

            response = WorkReleaseAssignmentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list pending assignments: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/active', methods=['GET'])
async def list_active_assignments():
    """
    List all active work release assignments.

    Returns: WorkReleaseAssignmentListResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignments = await service.get_active_work_releases()

            items = [
                WorkReleaseAssignmentResponse(
                    id=a.id,
                    inmate_id=a.inmate_id,
                    employer_id=a.employer_id,
                    employer_name=a.employer.name if a.employer else None,
                    position_title=a.position_title,
                    start_date=a.start_date,
                    end_date=a.end_date,
                    status=a.status,
                    hourly_rate=a.hourly_rate,
                    work_schedule=a.work_schedule,
                    supervisor_name=a.supervisor_name,
                    supervisor_phone=a.supervisor_phone,
                    approved_by=a.approved_by,
                    approval_date=a.approval_date,
                    termination_reason=a.termination_reason,
                    notes=a.notes,
                    created_by=a.created_by,
                    inserted_date=a.inserted_date,
                    updated_date=a.updated_date
                )
                for a in assignments
            ]

            response = WorkReleaseAssignmentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list active assignments: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>', methods=['GET'])
async def get_assignment(assignment_id: UUID):
    """
    Get a specific assignment.

    Returns: WorkReleaseAssignmentResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.get_assignment(assignment_id)

            if not assignment:
                return jsonify({"error": "Assignment not found"}), 404

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>', methods=['PUT'])
async def update_assignment(assignment_id: UUID):
    """
    Update assignment details (non-status fields).

    Request body: WorkReleaseAssignmentUpdate
    Returns: WorkReleaseAssignmentResponse
    """
    try:
        data = await request.get_json()
        update_data = WorkReleaseAssignmentUpdate(**data)

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.update_assignment(assignment_id, update_data)
            await session.commit()

            if not assignment:
                return jsonify({"error": "Assignment not found"}), 404

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/approve', methods=['PUT'])
async def approve_assignment(assignment_id: UUID):
    """
    Approve a work release assignment.

    CRITICAL: Validates employer approval and inmate MINIMUM security level.

    Returns: WorkReleaseAssignmentResponse
    """
    try:
        # Get user ID from auth context (placeholder)
        approved_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.approve_assignment(assignment_id, approved_by)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to approve assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/activate', methods=['PUT'])
async def activate_assignment(assignment_id: UUID):
    """
    Activate an approved assignment.

    Transitions: APPROVED → ACTIVE

    Returns: WorkReleaseAssignmentResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.activate_assignment(assignment_id)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to activate assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/suspend', methods=['PUT'])
async def suspend_assignment(assignment_id: UUID):
    """
    Suspend an active assignment.

    Request body: {"reason": "..."}
    Returns: WorkReleaseAssignmentResponse
    """
    try:
        data = await request.get_json()
        reason = data.get('reason', 'No reason provided')

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.suspend_assignment(assignment_id, reason)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to suspend assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/reinstate', methods=['PUT'])
async def reinstate_assignment(assignment_id: UUID):
    """
    Reinstate a suspended assignment.

    Returns: WorkReleaseAssignmentResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.reinstate_assignment(assignment_id)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to reinstate assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/complete', methods=['PUT'])
async def complete_assignment(assignment_id: UUID):
    """
    Mark assignment as successfully completed.

    Returns: WorkReleaseAssignmentResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.complete_assignment(assignment_id)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to complete assignment: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/terminate', methods=['PUT'])
async def terminate_assignment(assignment_id: UUID):
    """
    Terminate an assignment early.

    Request body: {"reason": "..."}
    Returns: WorkReleaseAssignmentResponse
    """
    try:
        data = await request.get_json()
        reason = data.get('reason')

        if not reason:
            return jsonify({"error": "Termination reason is required"}), 400

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            assignment = await service.terminate_assignment(assignment_id, reason)
            await session.commit()

            response = WorkReleaseAssignmentResponse(
                id=assignment.id,
                inmate_id=assignment.inmate_id,
                employer_id=assignment.employer_id,
                employer_name=assignment.employer.name if assignment.employer else None,
                position_title=assignment.position_title,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                hourly_rate=assignment.hourly_rate,
                work_schedule=assignment.work_schedule,
                supervisor_name=assignment.supervisor_name,
                supervisor_phone=assignment.supervisor_phone,
                approved_by=assignment.approved_by,
                approval_date=assignment.approval_date,
                termination_reason=assignment.termination_reason,
                notes=assignment.notes,
                created_by=assignment.created_by,
                inserted_date=assignment.inserted_date,
                updated_date=assignment.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to terminate assignment: {str(e)}"}), 500


@work_release_bp.route('/inmates/<uuid:inmate_id>/work-release', methods=['GET'])
async def get_inmate_work_release(inmate_id: UUID):
    """
    Get work release summary for an inmate.

    Returns: InmateWorkReleaseSummary
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            summary = await service.get_inmate_work_release_summary(inmate_id)
            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get work release summary: {str(e)}"}), 500


# ============================================================================
# Log Endpoints
# ============================================================================

@work_release_bp.route('/work-release/logs/departure', methods=['POST'])
async def log_departure():
    """
    Log inmate departure for work.

    Request body: WorkReleaseLogDeparture
    Returns: WorkReleaseLogResponse (201)
    """
    try:
        data = await request.get_json()
        departure_data = WorkReleaseLogDeparture(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            log = await service.log_departure(departure_data, created_by)
            await session.commit()

            response = WorkReleaseLogResponse(
                id=log.id,
                assignment_id=log.assignment_id,
                log_date=log.log_date,
                departure_time=log.departure_time,
                expected_return_time=log.expected_return_time,
                actual_return_time=log.actual_return_time,
                status=log.status,
                is_late=log.is_late,
                minutes_late=log.minutes_late,
                verified_by=log.verified_by,
                notes=log.notes,
                inserted_date=log.inserted_date,
                updated_date=log.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to log departure: {str(e)}"}), 500


@work_release_bp.route('/work-release/logs/<uuid:log_id>/return', methods=['PUT'])
async def log_return(log_id: UUID):
    """
    Log inmate return from work.

    Automatically determines if return was late.

    Request body: WorkReleaseLogReturn
    Returns: WorkReleaseLogResponse
    """
    try:
        data = await request.get_json()
        return_data = WorkReleaseLogReturn(**data)

        # Get user ID from auth context (placeholder)
        verified_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            log = await service.log_return(log_id, return_data, verified_by)
            await session.commit()

            response = WorkReleaseLogResponse(
                id=log.id,
                assignment_id=log.assignment_id,
                log_date=log.log_date,
                departure_time=log.departure_time,
                expected_return_time=log.expected_return_time,
                actual_return_time=log.actual_return_time,
                status=log.status,
                is_late=log.is_late,
                minutes_late=log.minutes_late,
                verified_by=log.verified_by,
                notes=log.notes,
                inserted_date=log.inserted_date,
                updated_date=log.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to log return: {str(e)}"}), 500


@work_release_bp.route('/work-release/logs/<uuid:log_id>/no-return', methods=['PUT'])
async def mark_no_return(log_id: UUID):
    """
    Mark an inmate as did not return.

    CRITICAL: This is a serious security incident.
    Auto-suspends the assignment.

    Request body: {"notes": "..."}
    Returns: WorkReleaseLogResponse
    """
    try:
        data = await request.get_json()
        notes = data.get('notes')

        if not notes:
            return jsonify({"error": "Notes are required for no-return incidents"}), 400

        # Get user ID from auth context (placeholder)
        verified_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            log = await service.mark_no_return(log_id, notes, verified_by)
            await session.commit()

            response = WorkReleaseLogResponse(
                id=log.id,
                assignment_id=log.assignment_id,
                log_date=log.log_date,
                departure_time=log.departure_time,
                expected_return_time=log.expected_return_time,
                actual_return_time=log.actual_return_time,
                status=log.status,
                is_late=log.is_late,
                minutes_late=log.minutes_late,
                verified_by=log.verified_by,
                notes=log.notes,
                inserted_date=log.inserted_date,
                updated_date=log.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to mark no-return: {str(e)}"}), 500


@work_release_bp.route('/work-release/logs/daily', methods=['GET'])
async def get_daily_logs():
    """
    Get all logs for a specific date.

    Query params:
    - date: Date in YYYY-MM-DD format (defaults to today)

    Returns: WorkReleaseLogListResponse
    """
    try:
        date_str = request.args.get('date')
        log_date = date.fromisoformat(date_str) if date_str else date.today()

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            logs = await service.get_daily_logs(log_date)

            items = [
                WorkReleaseLogResponse(
                    id=log.id,
                    assignment_id=log.assignment_id,
                    log_date=log.log_date,
                    departure_time=log.departure_time,
                    expected_return_time=log.expected_return_time,
                    actual_return_time=log.actual_return_time,
                    status=log.status,
                    is_late=log.is_late,
                    minutes_late=log.minutes_late,
                    verified_by=log.verified_by,
                    notes=log.notes,
                    inserted_date=log.inserted_date,
                    updated_date=log.updated_date
                )
                for log in logs
            ]

            response = WorkReleaseLogListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get daily logs: {str(e)}"}), 500


@work_release_bp.route('/work-release/logs/unresolved', methods=['GET'])
async def get_unresolved_logs():
    """
    Get logs where inmates departed but haven't returned.

    CRITICAL: Security concern - inmates currently out.

    Returns: WorkReleaseLogListResponse
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            logs = await service.get_unresolved_logs()

            items = [
                WorkReleaseLogResponse(
                    id=log.id,
                    assignment_id=log.assignment_id,
                    log_date=log.log_date,
                    departure_time=log.departure_time,
                    expected_return_time=log.expected_return_time,
                    actual_return_time=log.actual_return_time,
                    status=log.status,
                    is_late=log.is_late,
                    minutes_late=log.minutes_late,
                    verified_by=log.verified_by,
                    notes=log.notes,
                    inserted_date=log.inserted_date,
                    updated_date=log.updated_date
                )
                for log in logs
            ]

            response = WorkReleaseLogListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get unresolved logs: {str(e)}"}), 500


@work_release_bp.route('/work-release/assignments/<uuid:assignment_id>/logs', methods=['GET'])
async def get_assignment_logs(assignment_id: UUID):
    """
    Get logs for a specific assignment.

    Query params:
    - limit: Max number of logs to return

    Returns: WorkReleaseLogListResponse
    """
    try:
        limit = request.args.get('limit', type=int)

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            logs = await service.get_assignment_logs(assignment_id, limit)

            items = [
                WorkReleaseLogResponse(
                    id=log.id,
                    assignment_id=log.assignment_id,
                    log_date=log.log_date,
                    departure_time=log.departure_time,
                    expected_return_time=log.expected_return_time,
                    actual_return_time=log.actual_return_time,
                    status=log.status,
                    is_late=log.is_late,
                    minutes_late=log.minutes_late,
                    verified_by=log.verified_by,
                    notes=log.notes,
                    inserted_date=log.inserted_date,
                    updated_date=log.updated_date
                )
                for log in logs
            ]

            response = WorkReleaseLogListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get assignment logs: {str(e)}"}), 500


# ============================================================================
# Report Endpoints
# ============================================================================

@work_release_bp.route('/work-release/statistics', methods=['GET'])
async def get_statistics():
    """
    Get overall work release statistics.

    Returns: WorkReleaseStatistics
    """
    try:
        async with get_async_session() as session:
            service = WorkReleaseService(session)
            stats = await service.get_statistics()
            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


@work_release_bp.route('/work-release/daily-report', methods=['GET'])
async def get_daily_report():
    """
    Get daily work release activity report.

    Query params:
    - date: Date in YYYY-MM-DD format (defaults to today)

    Returns: DailyWorkReleaseReport
    """
    try:
        date_str = request.args.get('date')
        report_date = date.fromisoformat(date_str) if date_str else None

        async with get_async_session() as session:
            service = WorkReleaseService(session)
            report = await service.get_daily_report(report_date)
            return jsonify(report.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get daily report: {str(e)}"}), 500
