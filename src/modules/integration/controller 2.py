"""
Integration Controller - REST API endpoints for external system integrations.

Provides endpoints for RBPF integration and integration logging/health.

Endpoints:
- POST /api/v1/integration/rbpf/lookup - Look up person by NIB
- POST /api/v1/integration/rbpf/warrants - Check for active warrants
- POST /api/v1/integration/rbpf/notify-booking - Notify RBPF of booking
- POST /api/v1/integration/rbpf/notify-release - Notify RBPF of release
- GET /api/v1/integration/logs - List integration logs
- GET /api/v1/integration/logs/{correlation_id} - Get logs by correlation ID
- GET /api/v1/integration/health - Check integration health

NOTE: This is a STUB implementation using mock RBPF client.
TODO comments mark where real integration would connect.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify
from quart_schema import validate_request

from src.database.async_db import get_async_session
from src.modules.integration.service import IntegrationService
from src.modules.integration.rbpf_client import RBPFClientError
from src.modules.integration.dtos import (
    PersonLookupRequest, WarrantCheckRequest,
    BookingNotificationRequest, ReleaseNotificationRequest
)
from src.common.enums import RequestType, IntegrationStatus

# Blueprint for auto-discovery
integration_bp = Blueprint('integration', __name__, url_prefix='/api/v1/integration')
blueprint = integration_bp  # Alias for auto-discovery


# =============================================================================
# RBPF Integration Endpoints
# =============================================================================

@integration_bp.route('/rbpf/lookup', methods=['POST'])
@validate_request(PersonLookupRequest)
async def rbpf_lookup_person(data: PersonLookupRequest):
    """
    Look up a person by NIB number in RBPF system.

    POST /api/v1/integration/rbpf/lookup

    Body:
        nib_number: National Insurance Board number

    Returns:
        Person details and criminal history if found

    NOTE: STUB - Returns mock data for development/testing.
    TODO: Connect to real RBPF API when available.
    """
    # TODO: Get initiated_by from authenticated user
    initiated_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = IntegrationService(session)

        try:
            result = await service.lookup_person(data, initiated_by)
            await session.commit()

            return jsonify({
                'found': result.found,
                'nib_number': result.nib_number,
                'first_name': result.first_name,
                'last_name': result.last_name,
                'date_of_birth': result.date_of_birth.isoformat() if result.date_of_birth else None,
                'aliases': result.aliases,
                'criminal_history': [
                    {
                        'offense': r.offense,
                        'offense_date': r.offense_date.isoformat(),
                        'court': r.court,
                        'case_number': r.case_number,
                        'disposition': r.disposition,
                        'sentence': r.sentence
                    }
                    for r in result.criminal_history
                ] if result.criminal_history else None,
                'last_known_address': result.last_known_address,
                'rbpf_id': result.rbpf_id,
                '_stub': True,
                '_message': 'STUB: This is mock data for development'
            })

        except RBPFClientError as e:
            return jsonify({
                'error': 'RBPF lookup failed',
                'message': str(e),
                '_stub': True
            }), 503


@integration_bp.route('/rbpf/warrants', methods=['POST'])
@validate_request(WarrantCheckRequest)
async def rbpf_check_warrants(data: WarrantCheckRequest):
    """
    Check for active warrants in RBPF system.

    POST /api/v1/integration/rbpf/warrants

    Body:
        first_name: Person's first name
        last_name: Person's last name
        date_of_birth: Date of birth (YYYY-MM-DD)
        nib_number: Optional NIB for exact match

    Returns:
        List of active warrants if any

    NOTE: STUB - Returns mock data for development/testing.
    TODO: Connect to real RBPF API when available.
    """
    # TODO: Get initiated_by from authenticated user
    initiated_by = UUID('00000000-0000-0000-0000-000000000000')

    async with get_async_session() as session:
        service = IntegrationService(session)

        try:
            result = await service.check_warrants(data, initiated_by)
            await session.commit()

            return jsonify({
                'has_warrants': result.has_warrants,
                'warrant_count': result.warrant_count,
                'warrants': [
                    {
                        'warrant_number': w.warrant_number,
                        'warrant_type': w.warrant_type,
                        'issue_date': w.issue_date.isoformat(),
                        'issuing_court': w.issuing_court,
                        'offense': w.offense,
                        'status': w.status
                    }
                    for w in result.warrants
                ] if result.warrants else None,
                'last_checked': result.last_checked.isoformat(),
                '_stub': True,
                '_message': 'STUB: This is mock data for development'
            })

        except RBPFClientError as e:
            return jsonify({
                'error': 'RBPF warrant check failed',
                'message': str(e),
                '_stub': True
            }), 503


@integration_bp.route('/rbpf/notify-booking', methods=['POST'])
@validate_request(BookingNotificationRequest)
async def rbpf_notify_booking(data: BookingNotificationRequest):
    """
    Notify RBPF of a new inmate booking.

    POST /api/v1/integration/rbpf/notify-booking

    Body:
        inmate_id: BDOCS inmate UUID
        booking_number: BDOCS booking number
        first_name: Inmate first name
        last_name: Inmate last name
        date_of_birth: Date of birth
        nib_number: Optional NIB
        booking_date: Date/time of booking
        offense: Primary offense
        court_case_number: Optional court case number
        arresting_agency: Optional arresting agency

    Returns:
        Acknowledgment from RBPF

    NOTE: STUB - Simulates notification for development/testing.
    TODO: Connect to real RBPF API when available.
    """
    # TODO: Get initiated_by from authenticated user
    initiated_by = UUID('00000000-0000-0000-0000-000000000000')

    async with get_async_session() as session:
        service = IntegrationService(session)

        try:
            result = await service.notify_booking(data, initiated_by)
            await session.commit()

            return jsonify({
                'acknowledged': result.acknowledged,
                'reference_number': result.reference_number,
                'timestamp': result.timestamp.isoformat(),
                'message': result.message,
                '_stub': True,
                '_message': 'STUB: Notification simulated for development'
            }), 201

        except RBPFClientError as e:
            return jsonify({
                'error': 'RBPF booking notification failed',
                'message': str(e),
                '_stub': True
            }), 503


@integration_bp.route('/rbpf/notify-release', methods=['POST'])
@validate_request(ReleaseNotificationRequest)
async def rbpf_notify_release(data: ReleaseNotificationRequest):
    """
    Notify RBPF of an inmate release.

    POST /api/v1/integration/rbpf/notify-release

    Body:
        inmate_id: BDOCS inmate UUID
        booking_number: BDOCS booking number
        first_name: Inmate first name
        last_name: Inmate last name
        nib_number: Optional NIB
        release_date: Date/time of release
        release_type: Type of release (SERVED, BAIL, CLEMENCY, etc.)
        conditions: Optional release conditions

    Returns:
        Acknowledgment from RBPF

    NOTE: STUB - Simulates notification for development/testing.
    TODO: Connect to real RBPF API when available.
    """
    # TODO: Get initiated_by from authenticated user
    initiated_by = UUID('00000000-0000-0000-0000-000000000000')

    async with get_async_session() as session:
        service = IntegrationService(session)

        try:
            result = await service.notify_release(data, initiated_by)
            await session.commit()

            return jsonify({
                'acknowledged': result.acknowledged,
                'reference_number': result.reference_number,
                'timestamp': result.timestamp.isoformat(),
                'message': result.message,
                '_stub': True,
                '_message': 'STUB: Notification simulated for development'
            }), 201

        except RBPFClientError as e:
            return jsonify({
                'error': 'RBPF release notification failed',
                'message': str(e),
                '_stub': True
            }), 503


# =============================================================================
# Integration Logs Endpoints
# =============================================================================

@integration_bp.route('/logs', methods=['GET'])
async def get_integration_logs():
    """
    Get integration logs with optional filters.

    GET /api/v1/integration/logs?system_name=RBPF&status=SUCCESS

    Query params:
        system_name: Filter by system name (e.g., RBPF)
        request_type: Filter by request type
        status: Filter by status
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        skip: Pagination offset
        limit: Page size (max 100)
    """
    system_name = request.args.get('system_name')
    request_type_str = request.args.get('request_type')
    status_str = request.args.get('status')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    skip = int(request.args.get('skip', 0))
    limit = min(int(request.args.get('limit', 100)), 100)

    request_type = RequestType(request_type_str) if request_type_str else None
    status = IntegrationStatus(status_str) if status_str else None

    start_date = None
    end_date = None
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str)
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str)

    async with get_async_session() as session:
        service = IntegrationService(session)
        logs = await service.get_all_logs(
            system_name=system_name,
            request_type=request_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

        total = await service.count_logs(system_name, request_type, status)

        return jsonify({
            'items': [{
                'id': str(log.id),
                'system_name': log.system_name,
                'request_type': log.request_type.value,
                'status': log.status.value,
                'request_time': log.request_time.isoformat(),
                'response_time_ms': log.response_time_ms,
                'correlation_id': str(log.correlation_id),
                'error_message': log.error_message
            } for log in logs],
            'total': total,
            'skip': skip,
            'limit': limit
        })


@integration_bp.route('/logs/<uuid:log_id>', methods=['GET'])
async def get_integration_log(log_id: UUID):
    """
    Get detailed integration log by ID.

    GET /api/v1/integration/logs/{id}
    """
    async with get_async_session() as session:
        service = IntegrationService(session)
        log = await service.get_log(log_id)

        if not log:
            return jsonify({'error': 'Log not found'}), 404

        return jsonify({
            'id': str(log.id),
            'system_name': log.system_name,
            'request_type': log.request_type.value,
            'request_payload': log.request_payload,
            'response_payload': log.response_payload,
            'status': log.status.value,
            'request_time': log.request_time.isoformat(),
            'response_time': log.response_time.isoformat() if log.response_time else None,
            'response_time_ms': log.response_time_ms,
            'error_message': log.error_message,
            'correlation_id': str(log.correlation_id),
            'initiated_by': str(log.initiated_by),
            'initiator_name': log.initiator.full_name if log.initiator else None,
            'inserted_date': log.inserted_date.isoformat() if log.inserted_date else None
        })


@integration_bp.route('/logs/correlation/<uuid:correlation_id>', methods=['GET'])
async def get_logs_by_correlation(correlation_id: UUID):
    """
    Get all logs for a correlation ID.

    GET /api/v1/integration/logs/correlation/{correlation_id}

    Useful for tracking related requests across systems.
    """
    async with get_async_session() as session:
        service = IntegrationService(session)
        logs = await service.get_logs_by_correlation(correlation_id)

        return jsonify({
            'correlation_id': str(correlation_id),
            'count': len(logs),
            'items': [{
                'id': str(log.id),
                'system_name': log.system_name,
                'request_type': log.request_type.value,
                'status': log.status.value,
                'request_time': log.request_time.isoformat(),
                'response_time_ms': log.response_time_ms,
                'error_message': log.error_message
            } for log in logs]
        })


# =============================================================================
# Health Check Endpoint
# =============================================================================

@integration_bp.route('/health', methods=['GET'])
async def get_integration_health():
    """
    Check health status of all integrated systems.

    GET /api/v1/integration/health

    Returns:
        Status of each integrated system and overall health

    NOTE: STUB - Health check uses mock RBPF client.
    TODO: Connect to real system health endpoints when available.
    """
    async with get_async_session() as session:
        service = IntegrationService(session)
        health = await service.get_health()

        return jsonify({
            'overall_status': health.overall_status,
            'systems': [{
                'system_name': s.system_name,
                'status': s.status,
                'last_successful_request': s.last_successful_request.isoformat() if s.last_successful_request else None,
                'last_failed_request': s.last_failed_request.isoformat() if s.last_failed_request else None,
                'success_rate_24h': s.success_rate_24h,
                'average_response_time_ms': s.average_response_time_ms
            } for s in health.systems],
            'checked_at': health.checked_at.isoformat(),
            '_stub': True,
            '_message': 'STUB: Health check uses mock client'
        })
