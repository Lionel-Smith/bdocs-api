"""
Visitation Controller - REST API endpoints for visitation management.

Provides endpoints for visitor registration, visit scheduling, and check-in/out.
All endpoints require authentication.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify
from quart_schema import validate_request

from src.database.async_db import get_async_session
from src.modules.visitation.service import VisitationService
from src.modules.visitation.dtos import (
    VisitorCreateDTO, VisitorUpdateDTO, VisitorApprovalDTO, VisitorDenialDTO,
    VisitScheduleCreateDTO, VisitScheduleUpdateDTO, VisitCancelDTO,
    CheckInDTO, CheckOutDTO
)
from src.common.enums import CheckStatus, VisitStatus, VisitType

# Blueprint for auto-discovery
visitation_bp = Blueprint('visitation', __name__, url_prefix='/api/v1/visitation')
blueprint = visitation_bp  # Alias for auto-discovery


# =============================================================================
# Visitor Endpoints
# =============================================================================

@visitation_bp.route('/visitors', methods=['POST'])
@validate_request(VisitorCreateDTO)
async def register_visitor(data: VisitorCreateDTO):
    """
    Register a new visitor for an inmate.

    POST /api/v1/visitation/visitors
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        visitor = await service.register_visitor(data)
        await session.commit()

        return jsonify({
            'id': str(visitor.id),
            'full_name': visitor.full_name,
            'inmate_id': str(visitor.inmate_id),
            'background_check_status': visitor.background_check_status.value,
            'message': 'Visitor registered successfully. Pending background check.'
        }), 201


@visitation_bp.route('/visitors', methods=['GET'])
async def get_all_visitors():
    """
    Get all visitors with optional filters.

    GET /api/v1/visitation/visitors?check_status=PENDING&is_approved=true&is_active=true
    """
    check_status_str = request.args.get('check_status')
    is_approved = request.args.get('is_approved')
    is_active = request.args.get('is_active')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = VisitationService(session)
        visitors = await service.get_all_visitors(
            check_status=CheckStatus(check_status_str) if check_status_str else None,
            is_approved=is_approved.lower() == 'true' if is_approved else None,
            is_active=is_active.lower() == 'true' if is_active else None,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(v.id),
            'inmate_id': str(v.inmate_id),
            'full_name': v.full_name,
            'relationship': v.relationship.value,
            'background_check_status': v.background_check_status.value,
            'is_approved': v.is_approved,
            'is_active': v.is_active
        } for v in visitors])


@visitation_bp.route('/visitors/<uuid:visitor_id>', methods=['GET'])
async def get_visitor(visitor_id: UUID):
    """
    Get visitor by ID.

    GET /api/v1/visitation/visitors/{id}
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        visitor = await service.get_visitor(visitor_id)

        if not visitor:
            return jsonify({'error': 'Visitor not found'}), 404

        return jsonify({
            'id': str(visitor.id),
            'inmate_id': str(visitor.inmate_id),
            'inmate_name': visitor.inmate.full_name if visitor.inmate else None,
            'first_name': visitor.first_name,
            'last_name': visitor.last_name,
            'full_name': visitor.full_name,
            'relationship': visitor.relationship.value,
            'phone': visitor.phone,
            'email': visitor.email,
            'id_type': visitor.id_type.value,
            'id_number': visitor.id_number,
            'date_of_birth': visitor.date_of_birth.isoformat(),
            'age': visitor.age,
            'photo_url': visitor.photo_url,
            'background_check_date': visitor.background_check_date.isoformat() if visitor.background_check_date else None,
            'background_check_status': visitor.background_check_status.value,
            'is_approved': visitor.is_approved,
            'approval_date': visitor.approval_date.isoformat() if visitor.approval_date else None,
            'approved_by': str(visitor.approved_by) if visitor.approved_by else None,
            'denied_reason': visitor.denied_reason,
            'is_active': visitor.is_active,
            'inserted_date': visitor.inserted_date.isoformat() if visitor.inserted_date else None
        })


@visitation_bp.route('/visitors/<uuid:visitor_id>', methods=['PUT'])
@validate_request(VisitorUpdateDTO)
async def update_visitor(visitor_id: UUID, data: VisitorUpdateDTO):
    """
    Update visitor information.

    PUT /api/v1/visitation/visitors/{id}
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        visitor = await service.update_visitor(visitor_id, data)

        if not visitor:
            return jsonify({'error': 'Visitor not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(visitor.id),
            'full_name': visitor.full_name,
            'message': 'Visitor updated successfully'
        })


@visitation_bp.route('/visitors/<uuid:visitor_id>/approve', methods=['PUT'])
@validate_request(VisitorApprovalDTO)
async def approve_visitor(visitor_id: UUID, data: VisitorApprovalDTO):
    """
    Approve a visitor after background check.

    PUT /api/v1/visitation/visitors/{id}/approve
    """
    # TODO: Get approved_by from authenticated user
    approved_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            visitor = await service.approve_visitor(visitor_id, data, approved_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not visitor:
            return jsonify({'error': 'Visitor not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(visitor.id),
            'full_name': visitor.full_name,
            'is_approved': visitor.is_approved,
            'background_check_status': visitor.background_check_status.value,
            'message': 'Visitor approved successfully' if visitor.is_approved else 'Visitor status updated'
        })


@visitation_bp.route('/visitors/<uuid:visitor_id>/deny', methods=['PUT'])
@validate_request(VisitorDenialDTO)
async def deny_visitor(visitor_id: UUID, data: VisitorDenialDTO):
    """
    Deny a visitor.

    PUT /api/v1/visitation/visitors/{id}/deny
    """
    # TODO: Get denied_by from authenticated user
    denied_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = VisitationService(session)
        visitor = await service.deny_visitor(visitor_id, data, denied_by)

        if not visitor:
            return jsonify({'error': 'Visitor not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(visitor.id),
            'full_name': visitor.full_name,
            'is_approved': visitor.is_approved,
            'denied_reason': visitor.denied_reason,
            'message': 'Visitor denied'
        })


# Inmate's visitors endpoint
@visitation_bp.route('/inmates/<uuid:inmate_id>/visitors', methods=['GET'])
async def get_inmate_visitors(inmate_id: UUID):
    """
    Get all visitors registered for an inmate.

    GET /api/v1/visitation/inmates/{id}/visitors?approved_only=true
    """
    approved_only = request.args.get('approved_only', 'false').lower() == 'true'

    async with get_async_session() as session:
        service = VisitationService(session)
        visitors = await service.get_inmate_visitors(inmate_id, approved_only)

        return jsonify([{
            'id': str(v.id),
            'full_name': v.full_name,
            'relationship': v.relationship.value,
            'phone': v.phone,
            'background_check_status': v.background_check_status.value,
            'is_approved': v.is_approved,
            'is_active': v.is_active
        } for v in visitors])


# =============================================================================
# Visit Schedule Endpoints
# =============================================================================

@visitation_bp.route('/schedule', methods=['POST'])
@validate_request(VisitScheduleCreateDTO)
async def schedule_visit(data: VisitScheduleCreateDTO):
    """
    Schedule a new visit.

    POST /api/v1/visitation/schedule
    """
    # TODO: Get created_by from authenticated user
    created_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            schedule = await service.schedule_visit(data, created_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        await session.commit()

        return jsonify({
            'id': str(schedule.id),
            'inmate_id': str(schedule.inmate_id),
            'visitor_id': str(schedule.visitor_id),
            'scheduled_date': schedule.scheduled_date.isoformat(),
            'scheduled_time': schedule.scheduled_time.isoformat(),
            'status': schedule.status.value,
            'message': 'Visit scheduled successfully'
        }), 201


@visitation_bp.route('/schedule', methods=['GET'])
async def get_visit_schedules():
    """
    Get visit schedules with filters.

    GET /api/v1/visitation/schedule?date=2026-01-05&status=SCHEDULED&visit_type=GENERAL
    """
    date_str = request.args.get('date')
    status_str = request.args.get('status')
    visit_type_str = request.args.get('visit_type')

    if not date_str:
        return jsonify({'error': 'date parameter is required'}), 400

    try:
        visit_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    async with get_async_session() as session:
        service = VisitationService(session)
        schedules = await service.get_visits_by_date(
            visit_date=visit_date,
            status=VisitStatus(status_str) if status_str else None,
            visit_type=VisitType(visit_type_str) if visit_type_str else None
        )

        return jsonify([{
            'id': str(s.id),
            'inmate_id': str(s.inmate_id),
            'inmate_name': s.inmate.full_name if s.inmate else None,
            'visitor_id': str(s.visitor_id),
            'visitor_name': s.visitor.full_name if s.visitor else None,
            'scheduled_date': s.scheduled_date.isoformat(),
            'scheduled_time': s.scheduled_time.isoformat(),
            'duration_minutes': s.duration_minutes,
            'visit_type': s.visit_type.value,
            'status': s.status.value,
            'location': s.location
        } for s in schedules])


@visitation_bp.route('/schedule/<uuid:schedule_id>', methods=['GET'])
async def get_visit_schedule(schedule_id: UUID):
    """
    Get visit schedule by ID.

    GET /api/v1/visitation/schedule/{id}
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        schedule = await service.get_visit_schedule(schedule_id)

        if not schedule:
            return jsonify({'error': 'Visit schedule not found'}), 404

        return jsonify({
            'id': str(schedule.id),
            'inmate_id': str(schedule.inmate_id),
            'inmate_name': schedule.inmate.full_name if schedule.inmate else None,
            'inmate_booking_number': schedule.inmate.booking_number if schedule.inmate else None,
            'visitor_id': str(schedule.visitor_id),
            'visitor_name': schedule.visitor.full_name if schedule.visitor else None,
            'visitor_relationship': schedule.visitor.relationship.value if schedule.visitor else None,
            'scheduled_date': schedule.scheduled_date.isoformat(),
            'scheduled_time': schedule.scheduled_time.isoformat(),
            'duration_minutes': schedule.duration_minutes,
            'visit_type': schedule.visit_type.value,
            'status': schedule.status.value,
            'location': schedule.location,
            'actual_start_time': schedule.actual_start_time.isoformat() if schedule.actual_start_time else None,
            'actual_end_time': schedule.actual_end_time.isoformat() if schedule.actual_end_time else None,
            'cancelled_reason': schedule.cancelled_reason,
            'notes': schedule.notes,
            'created_by': str(schedule.created_by),
            'inserted_date': schedule.inserted_date.isoformat() if schedule.inserted_date else None
        })


@visitation_bp.route('/schedule/<uuid:schedule_id>/cancel', methods=['PUT'])
@validate_request(VisitCancelDTO)
async def cancel_visit(schedule_id: UUID, data: VisitCancelDTO):
    """
    Cancel a scheduled visit.

    PUT /api/v1/visitation/schedule/{id}/cancel
    """
    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            schedule = await service.cancel_visit(schedule_id, data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not schedule:
            return jsonify({'error': 'Visit schedule not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(schedule.id),
            'status': schedule.status.value,
            'cancelled_reason': schedule.cancelled_reason,
            'message': 'Visit cancelled'
        })


@visitation_bp.route('/schedule/<uuid:schedule_id>/check-in', methods=['POST'])
@validate_request(CheckInDTO)
async def check_in_visitor(schedule_id: UUID, data: CheckInDTO):
    """
    Check in a visitor for their scheduled visit.

    POST /api/v1/visitation/schedule/{id}/check-in
    """
    # TODO: Get processed_by from authenticated user
    processed_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            log = await service.check_in_visitor(schedule_id, data, processed_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        await session.commit()

        return jsonify({
            'visit_log_id': str(log.id),
            'visit_schedule_id': str(log.visit_schedule_id),
            'checked_in_at': log.checked_in_at.isoformat(),
            'visitor_searched': log.visitor_searched,
            'items_stored': log.items_stored,
            'message': 'Visitor checked in successfully'
        }), 201


@visitation_bp.route('/schedule/<uuid:schedule_id>/check-out', methods=['POST'])
@validate_request(CheckOutDTO)
async def check_out_visitor(schedule_id: UUID, data: CheckOutDTO):
    """
    Check out a visitor after their visit.

    POST /api/v1/visitation/schedule/{id}/check-out
    """
    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            log = await service.check_out_visitor(schedule_id, data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not log:
            return jsonify({'error': 'Visit log not found'}), 404

        await session.commit()

        return jsonify({
            'visit_log_id': str(log.id),
            'checked_out_at': log.checked_out_at.isoformat() if log.checked_out_at else None,
            'visit_duration_minutes': log.visit_duration_minutes,
            'contraband_found': log.contraband_found,
            'incident_id': str(log.incident_id) if log.incident_id else None,
            'message': 'Visitor checked out successfully'
        })


@visitation_bp.route('/schedule/<uuid:schedule_id>/no-show', methods=['POST'])
async def mark_no_show(schedule_id: UUID):
    """
    Mark a visitor as no-show.

    POST /api/v1/visitation/schedule/{id}/no-show
    """
    async with get_async_session() as session:
        service = VisitationService(session)

        try:
            schedule = await service.mark_no_show(schedule_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not schedule:
            return jsonify({'error': 'Visit schedule not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(schedule.id),
            'status': schedule.status.value,
            'message': 'Visitor marked as no-show'
        })


# =============================================================================
# Today's Visits & Statistics
# =============================================================================

@visitation_bp.route('/today', methods=['GET'])
async def get_todays_visits():
    """
    Get all visits scheduled for today.

    GET /api/v1/visitation/today
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        visits = await service.get_todays_visits()

        return jsonify([{
            'visit_id': str(v.visit_id),
            'inmate_id': str(v.inmate_id),
            'inmate_name': v.inmate_name,
            'inmate_booking_number': v.inmate_booking_number,
            'visitor_id': str(v.visitor_id),
            'visitor_name': v.visitor_name,
            'relationship': v.relationship.value if v.relationship else None,
            'scheduled_time': v.scheduled_time.isoformat(),
            'duration_minutes': v.duration_minutes,
            'visit_type': v.visit_type.value,
            'status': v.status.value,
            'location': v.location,
            'is_checked_in': v.is_checked_in,
            'checked_in_at': v.checked_in_at.isoformat() if v.checked_in_at else None
        } for v in visits])


@visitation_bp.route('/statistics', methods=['GET'])
async def get_visitation_statistics():
    """
    Get comprehensive visitation statistics.

    GET /api/v1/visitation/statistics
    """
    async with get_async_session() as session:
        service = VisitationService(session)
        stats = await service.get_statistics()

        return jsonify({
            'total_approved_visitors': stats.total_approved_visitors,
            'pending_approval': stats.pending_approval,
            'active_visitors': stats.active_visitors,
            'visits_scheduled_today': stats.visits_scheduled_today,
            'visits_completed_today': stats.visits_completed_today,
            'visits_in_progress': stats.visits_in_progress,
            'no_shows_today': stats.no_shows_today,
            'cancellations_today': stats.cancellations_today,
            'by_visit_type': stats.by_visit_type,
            'contraband_incidents_week': stats.contraband_incidents_week,
            'total_visitors_searched_today': stats.total_visitors_searched_today,
            'average_visit_duration_minutes': stats.average_visit_duration_minutes
        })
