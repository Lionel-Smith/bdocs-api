"""
Programme Controller - API endpoints for rehabilitation programmes.

Endpoints:
- POST   /api/v1/programmes                         Create programme
- GET    /api/v1/programmes                         List programmes (with filters)
- GET    /api/v1/programmes/statistics              Get statistics
- GET    /api/v1/programmes/{id}                    Get programme by ID
- PUT    /api/v1/programmes/{id}                    Update programme
- DELETE /api/v1/programmes/{id}                    Delete programme
- GET    /api/v1/programmes/{id}/sessions           List programme sessions
- POST   /api/v1/programmes/{id}/sessions           Create session
- PUT    /api/v1/programmes/sessions/{id}           Update session
- POST   /api/v1/programmes/sessions/{id}/attendance Record attendance
- GET    /api/v1/programmes/{id}/enrollments        List programme enrollments
- POST   /api/v1/programmes/{id}/enroll             Enroll inmate
- PUT    /api/v1/programmes/enrollments/{id}        Update enrollment
- PUT    /api/v1/programmes/enrollments/{id}/status Update enrollment status
- GET    /api/v1/inmates/{id}/programmes            Inmate programme summary
"""
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import ProgrammeCategory, SessionStatus, EnrollmentStatus
from src.modules.programme.service import ProgrammeService
from src.modules.programme.dtos import (
    ProgrammeCreate,
    ProgrammeUpdate,
    ProgrammeResponse,
    ProgrammeListResponse,
    ProgrammeSessionCreate,
    ProgrammeSessionUpdate,
    ProgrammeSessionResponse,
    ProgrammeSessionListResponse,
    ProgrammeEnrollmentCreate,
    ProgrammeEnrollmentUpdate,
    ProgrammeEnrollmentStatusUpdate,
    ProgrammeEnrollmentResponse,
    ProgrammeEnrollmentListResponse,
)

# Create blueprint
programme_bp = Blueprint('programme', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = programme_bp


# ============================================================================
# Programme CRUD Endpoints
# ============================================================================

@programme_bp.route('/programmes', methods=['POST'])
async def create_programme():
    """
    Create a new rehabilitation programme.

    Request body: ProgrammeCreate
    Returns: ProgrammeResponse
    """
    try:
        data = await request.get_json()
        programme_data = ProgrammeCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ProgrammeService(session)
            programme = await service.create_programme(programme_data, created_by)
            await session.commit()

            response = ProgrammeResponse.model_validate(programme)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create programme: {str(e)}"}), 500


@programme_bp.route('/programmes', methods=['GET'])
async def list_programmes():
    """
    List programmes with optional filters.

    Query params:
    - category: Filter by ProgrammeCategory
    - active: Filter active only (true/false)

    Returns: ProgrammeListResponse
    """
    try:
        category_filter = request.args.get('category')
        active_filter = request.args.get('active', '').lower() == 'true'

        category = ProgrammeCategory(category_filter) if category_filter else None

        async with get_async_session() as session:
            service = ProgrammeService(session)
            programmes = await service.get_all_programmes(
                active_only=active_filter,
                category=category
            )

            response = ProgrammeListResponse(
                items=[ProgrammeResponse.model_validate(p) for p in programmes],
                total=len(programmes)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to list programmes: {str(e)}"}), 500


@programme_bp.route('/programmes/<uuid:programme_id>', methods=['GET'])
async def get_programme(programme_id: UUID):
    """
    Get a programme by ID.

    Returns: ProgrammeResponse
    """
    try:
        async with get_async_session() as session:
            service = ProgrammeService(session)
            programme = await service.get_programme(programme_id)

            if not programme:
                return jsonify({"error": "Programme not found"}), 404

            response = ProgrammeResponse.model_validate(programme)
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get programme: {str(e)}"}), 500


@programme_bp.route('/programmes/<uuid:programme_id>', methods=['PUT'])
async def update_programme(programme_id: UUID):
    """
    Update a programme.

    Request body: ProgrammeUpdate
    Returns: ProgrammeResponse
    """
    try:
        data = await request.get_json()
        update_data = ProgrammeUpdate(**data)

        async with get_async_session() as session:
            service = ProgrammeService(session)
            programme = await service.update_programme(programme_id, update_data)
            await session.commit()

            if not programme:
                return jsonify({"error": "Programme not found"}), 404

            response = ProgrammeResponse.model_validate(programme)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update programme: {str(e)}"}), 500


@programme_bp.route('/programmes/<uuid:programme_id>', methods=['DELETE'])
async def delete_programme(programme_id: UUID):
    """
    Soft delete a programme.

    Cannot delete programmes with active enrollments.
    """
    try:
        async with get_async_session() as session:
            service = ProgrammeService(session)
            success = await service.delete_programme(programme_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Programme not found"}), 404

            return jsonify({"message": "Programme deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete programme: {str(e)}"}), 500


# ============================================================================
# Session Endpoints
# ============================================================================

@programme_bp.route('/programmes/<uuid:programme_id>/sessions', methods=['GET'])
async def list_programme_sessions(programme_id: UUID):
    """
    List sessions for a programme.

    Query params:
    - status: Filter by SessionStatus

    Returns: ProgrammeSessionListResponse
    """
    try:
        status_filter = request.args.get('status')
        status = SessionStatus(status_filter) if status_filter else None

        async with get_async_session() as session:
            service = ProgrammeService(session)
            sessions = await service.get_programme_sessions(programme_id, status)

            response = ProgrammeSessionListResponse(
                items=[ProgrammeSessionResponse.model_validate(s) for s in sessions],
                total=len(sessions)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to list sessions: {str(e)}"}), 500


@programme_bp.route('/programmes/<uuid:programme_id>/sessions', methods=['POST'])
async def create_session(programme_id: UUID):
    """
    Create a new session for a programme.

    Request body: ProgrammeSessionCreate
    Returns: ProgrammeSessionResponse
    """
    try:
        data = await request.get_json()
        session_data = ProgrammeSessionCreate(**data)

        async with get_async_session() as session:
            service = ProgrammeService(session)
            prog_session = await service.create_session(programme_id, session_data)
            await session.commit()

            response = ProgrammeSessionResponse.model_validate(prog_session)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create session: {str(e)}"}), 500


@programme_bp.route('/programmes/sessions/<uuid:session_id>', methods=['PUT'])
async def update_session(session_id: UUID):
    """
    Update a programme session.

    Request body: ProgrammeSessionUpdate
    Returns: ProgrammeSessionResponse
    """
    try:
        data = await request.get_json()
        update_data = ProgrammeSessionUpdate(**data)

        async with get_async_session() as session:
            service = ProgrammeService(session)
            prog_session = await service.update_session(session_id, update_data)
            await session.commit()

            if not prog_session:
                return jsonify({"error": "Session not found"}), 404

            response = ProgrammeSessionResponse.model_validate(prog_session)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update session: {str(e)}"}), 500


@programme_bp.route('/programmes/sessions/<uuid:session_id>/attendance', methods=['POST'])
async def record_session_attendance(session_id: UUID):
    """
    Record attendance for a session.

    Request body:
    - attendance_count: Number of attendees
    - notes: Optional notes

    Returns: ProgrammeSessionResponse
    """
    try:
        data = await request.get_json()
        attendance_count = data.get('attendance_count')
        notes = data.get('notes')

        if attendance_count is None:
            return jsonify({"error": "attendance_count is required"}), 400

        async with get_async_session() as session:
            service = ProgrammeService(session)
            prog_session = await service.record_attendance(
                session_id, attendance_count, notes
            )
            await session.commit()

            response = ProgrammeSessionResponse.model_validate(prog_session)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to record attendance: {str(e)}"}), 500


# ============================================================================
# Enrollment Endpoints
# ============================================================================

@programme_bp.route('/programmes/<uuid:programme_id>/enrollments', methods=['GET'])
async def list_programme_enrollments(programme_id: UUID):
    """
    List enrollments for a programme.

    Query params:
    - status: Filter by EnrollmentStatus

    Returns: ProgrammeEnrollmentListResponse
    """
    try:
        status_filter = request.args.get('status')
        status = EnrollmentStatus(status_filter) if status_filter else None

        async with get_async_session() as session:
            service = ProgrammeService(session)
            enrollments = await service.get_programme_enrollments(programme_id, status)

            response = ProgrammeEnrollmentListResponse(
                items=[ProgrammeEnrollmentResponse.model_validate(e) for e in enrollments],
                total=len(enrollments)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to list enrollments: {str(e)}"}), 500


@programme_bp.route('/programmes/<uuid:programme_id>/enroll', methods=['POST'])
async def enroll_inmate(programme_id: UUID):
    """
    Enroll an inmate in a programme.

    Validates eligibility and capacity before enrollment.

    Request body: ProgrammeEnrollmentCreate
    Returns: ProgrammeEnrollmentResponse
    """
    try:
        data = await request.get_json()
        enrollment_data = ProgrammeEnrollmentCreate(**data)

        # Get user ID from auth context (placeholder)
        enrolled_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ProgrammeService(session)
            enrollment = await service.enroll_inmate(
                programme_id, enrollment_data, enrolled_by
            )
            await session.commit()

            response = ProgrammeEnrollmentResponse.model_validate(enrollment)
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to enroll inmate: {str(e)}"}), 500


@programme_bp.route('/programmes/enrollments/<uuid:enrollment_id>', methods=['PUT'])
async def update_enrollment(enrollment_id: UUID):
    """
    Update an enrollment (non-status fields).

    Use PUT /enrollments/{id}/status to change status.

    Request body: ProgrammeEnrollmentUpdate
    Returns: ProgrammeEnrollmentResponse
    """
    try:
        data = await request.get_json()
        update_data = ProgrammeEnrollmentUpdate(**data)

        async with get_async_session() as session:
            service = ProgrammeService(session)
            enrollment = await service.update_enrollment(enrollment_id, update_data)
            await session.commit()

            if not enrollment:
                return jsonify({"error": "Enrollment not found"}), 404

            response = ProgrammeEnrollmentResponse.model_validate(enrollment)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update enrollment: {str(e)}"}), 500


@programme_bp.route('/programmes/enrollments/<uuid:enrollment_id>/status', methods=['PUT'])
async def update_enrollment_status(enrollment_id: UUID):
    """
    Update enrollment status with workflow validation.

    Validates that the transition is allowed per enrollment workflow.
    On COMPLETED, sets completion_date and optional grade/certificate.

    Request body: ProgrammeEnrollmentStatusUpdate
    Returns: ProgrammeEnrollmentResponse
    """
    try:
        data = await request.get_json()
        status_update = ProgrammeEnrollmentStatusUpdate(**data)

        async with get_async_session() as session:
            service = ProgrammeService(session)
            enrollment = await service.update_enrollment_status(
                enrollment_id, status_update
            )
            await session.commit()

            response = ProgrammeEnrollmentResponse.model_validate(enrollment)
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500


# ============================================================================
# Inmate Programme Endpoint
# ============================================================================

@programme_bp.route('/inmates/<uuid:inmate_id>/programmes', methods=['GET'])
async def get_inmate_programmes(inmate_id: UUID):
    """
    Get programme summary for an inmate.

    Returns: InmateProgrammeSummary
    """
    try:
        async with get_async_session() as session:
            service = ProgrammeService(session)
            summary = await service.get_inmate_summary(inmate_id)

            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get inmate programmes: {str(e)}"}), 500


# ============================================================================
# Statistics Endpoint
# ============================================================================

@programme_bp.route('/programmes/statistics', methods=['GET'])
async def get_statistics():
    """
    Get programme statistics.

    Returns: ProgrammeStatistics
    """
    try:
        async with get_async_session() as session:
            service = ProgrammeService(session)
            stats = await service.get_statistics()

            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500
