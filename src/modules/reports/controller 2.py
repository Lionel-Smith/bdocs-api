"""
Reports Controller - REST API endpoints for report management and generation.

Provides endpoints for:
- Report definitions (list, get by code)
- Report generation (sync and queued)
- Report executions (history, status, download)
- Quick reports (real-time summaries without file generation)

Endpoints:
- GET /api/v1/reports/definitions
- GET /api/v1/reports/definitions/{code}
- POST /api/v1/reports/generate/{code}
- POST /api/v1/reports/queue/{code}
- GET /api/v1/reports/executions
- GET /api/v1/reports/executions/{id}
- GET /api/v1/reports/executions/{id}/download
- GET /api/v1/reports/quick/population
- GET /api/v1/reports/quick/incidents
- GET /api/v1/reports/quick/programmes
"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pathlib import Path

from quart import Blueprint, request, jsonify, send_file
from quart_schema import validate_request

from src.database.async_db import get_async_session
from src.modules.reports.service import ReportService, ReportGenerationError
from src.modules.reports.dtos import GenerateReportRequest
from src.common.enums import ReportCategory, ReportStatus, OutputFormat

# Blueprint for auto-discovery
reports_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')
blueprint = reports_bp  # Alias for auto-discovery


# =============================================================================
# Report Definitions Endpoints
# =============================================================================

@reports_bp.route('/definitions', methods=['GET'])
async def get_report_definitions():
    """
    Get all available report definitions.

    GET /api/v1/reports/definitions?category=POPULATION&is_scheduled=true

    Query params:
        category: Filter by ReportCategory
        is_scheduled: Filter scheduled reports only
        skip: Pagination offset
        limit: Page size (max 100)
    """
    category_str = request.args.get('category')
    is_scheduled_str = request.args.get('is_scheduled')
    skip = int(request.args.get('skip', 0))
    limit = min(int(request.args.get('limit', 100)), 100)

    category = ReportCategory(category_str) if category_str else None
    is_scheduled = None
    if is_scheduled_str:
        is_scheduled = is_scheduled_str.lower() == 'true'

    async with get_async_session() as session:
        service = ReportService(session)

        definitions = await service.get_all_definitions(
            category=category,
            is_scheduled=is_scheduled,
            skip=skip,
            limit=limit
        )

        total = await service.count_definitions(category)

        return jsonify({
            'items': [{
                'id': str(d.id),
                'code': d.code,
                'name': d.name,
                'category': d.category.value,
                'output_format': d.output_format.value,
                'is_scheduled': d.is_scheduled,
                'last_generated': d.last_generated.isoformat() if d.last_generated else None
            } for d in definitions],
            'total': total,
            'skip': skip,
            'limit': limit
        })


@reports_bp.route('/definitions/<code>', methods=['GET'])
async def get_report_definition(code: str):
    """
    Get detailed report definition by code.

    GET /api/v1/reports/definitions/RPT-POP-001
    """
    async with get_async_session() as session:
        service = ReportService(session)
        definition = await service.get_definition_by_code(code)

        if not definition:
            return jsonify({'error': 'Report definition not found'}), 404

        return jsonify({
            'id': str(definition.id),
            'code': definition.code,
            'name': definition.name,
            'description': definition.description,
            'category': definition.category.value,
            'parameters_schema': definition.parameters_schema,
            'output_format': definition.output_format.value,
            'is_scheduled': definition.is_scheduled,
            'schedule_cron': definition.schedule_cron,
            'last_generated': definition.last_generated.isoformat() if definition.last_generated else None,
            'created_by': str(definition.created_by),
            'creator_name': definition.creator_name
        })


# =============================================================================
# Report Generation Endpoints
# =============================================================================

@reports_bp.route('/generate/<code>', methods=['POST'])
async def generate_report(code: str):
    """
    Generate a report synchronously.

    POST /api/v1/reports/generate/RPT-POP-001

    Body (optional):
        output_format: Override default format (PDF, EXCEL, CSV, JSON)
        parameters: Report-specific parameters

    Returns:
        Generated file path and execution details

    Note: This endpoint blocks until generation completes.
    For long-running reports, use /queue/{code} instead.
    """
    data = await request.get_json() or {}

    output_format_str = data.get('output_format')
    output_format = OutputFormat(output_format_str) if output_format_str else None
    parameters = data.get('parameters', {})

    # TODO: Get requested_by from authenticated user
    requested_by = UUID('00000000-0000-0000-0000-000000000000')

    async with get_async_session() as session:
        service = ReportService(session)

        try:
            result = await service.generate_report(
                code=code,
                parameters=parameters,
                output_format=output_format,
                requested_by=requested_by
            )
            await session.commit()

            return jsonify({
                'execution_id': str(result.execution_id),
                'status': result.status.value,
                'file_path': result.file_path,
                'file_size_bytes': result.file_size_bytes,
                'duration_seconds': result.duration_seconds,
                'error_message': result.error_message
            }), 201 if result.status == ReportStatus.COMPLETED else 500

        except ReportGenerationError as e:
            return jsonify({
                'error': 'Report generation failed',
                'message': str(e)
            }), 400


@reports_bp.route('/queue/<code>', methods=['POST'])
async def queue_report(code: str):
    """
    Queue a report for asynchronous generation.

    POST /api/v1/reports/queue/RPT-POP-001

    Body (optional):
        output_format: Override default format
        parameters: Report-specific parameters

    Returns:
        Execution ID to check status later

    Note: This returns immediately. Use /executions/{id} to check status.
    """
    data = await request.get_json() or {}

    output_format_str = data.get('output_format')
    output_format = OutputFormat(output_format_str) if output_format_str else None
    parameters = data.get('parameters', {})

    # TODO: Get requested_by from authenticated user
    requested_by = UUID('00000000-0000-0000-0000-000000000000')

    async with get_async_session() as session:
        service = ReportService(session)

        try:
            result = await service.queue_report(
                code=code,
                parameters=parameters,
                output_format=output_format,
                requested_by=requested_by
            )
            await session.commit()

            return jsonify({
                'execution_id': str(result.execution_id),
                'report_code': result.report_code,
                'status': result.status.value,
                'message': result.message,
                'estimated_completion': result.estimated_completion.isoformat() if result.estimated_completion else None,
                '_stub': True,
                '_message': 'STUB: Background processing not implemented'
            }), 202

        except ReportGenerationError as e:
            return jsonify({
                'error': 'Failed to queue report',
                'message': str(e)
            }), 400


# =============================================================================
# Report Executions Endpoints
# =============================================================================

@reports_bp.route('/executions', methods=['GET'])
async def get_report_executions():
    """
    Get report execution history.

    GET /api/v1/reports/executions?status=COMPLETED&limit=20

    Query params:
        report_code: Filter by report code
        status: Filter by status (QUEUED, GENERATING, COMPLETED, FAILED)
        requested_by: Filter by user ID
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        skip: Pagination offset
        limit: Page size (max 100)
    """
    report_code = request.args.get('report_code')
    status_str = request.args.get('status')
    requested_by_str = request.args.get('requested_by')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    skip = int(request.args.get('skip', 0))
    limit = min(int(request.args.get('limit', 100)), 100)

    status = ReportStatus(status_str) if status_str else None
    requested_by = UUID(requested_by_str) if requested_by_str else None

    start_date = None
    end_date = None
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str)
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str)

    async with get_async_session() as session:
        service = ReportService(session)

        # If report_code provided, look up definition ID
        report_definition_id = None
        if report_code:
            definition = await service.get_definition_by_code(report_code)
            if definition:
                report_definition_id = definition.id

        executions = await service.get_report_history(
            report_definition_id=report_definition_id,
            status=status,
            requested_by=requested_by,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

        total = await service.count_executions(
            report_definition_id=report_definition_id,
            status=status,
            requested_by=requested_by
        )

        return jsonify({
            'items': [{
                'id': str(e.id),
                'report_code': e.report_code,
                'report_name': e.report_name,
                'status': e.status.value,
                'started_at': e.started_at.isoformat(),
                'completed_at': e.completed_at.isoformat() if e.completed_at else None,
                'duration_seconds': e.duration_seconds,
                'requested_by': str(e.requested_by),
                'requester_name': e.requester_name
            } for e in executions],
            'total': total,
            'skip': skip,
            'limit': limit
        })


@reports_bp.route('/executions/<uuid:execution_id>', methods=['GET'])
async def get_report_execution(execution_id: UUID):
    """
    Get detailed report execution by ID.

    GET /api/v1/reports/executions/{id}
    """
    async with get_async_session() as session:
        service = ReportService(session)
        execution = await service.get_execution(execution_id)

        if not execution:
            return jsonify({'error': 'Execution not found'}), 404

        return jsonify({
            'id': str(execution.id),
            'report_definition_id': str(execution.report_definition_id),
            'report_code': execution.report_code,
            'report_name': execution.report_name,
            'parameters': execution.parameters,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'file_path': execution.file_path,
            'file_size_bytes': execution.file_size_bytes,
            'error_message': execution.error_message,
            'requested_by': str(execution.requested_by),
            'requester_name': execution.requester_name,
            'duration_seconds': execution.duration_seconds
        })


@reports_bp.route('/executions/<uuid:execution_id>/download', methods=['GET'])
async def download_report(execution_id: UUID):
    """
    Download a generated report file.

    GET /api/v1/reports/executions/{id}/download

    Returns the report file if generation completed successfully.
    """
    async with get_async_session() as session:
        service = ReportService(session)
        execution = await service.get_execution(execution_id)

        if not execution:
            return jsonify({'error': 'Execution not found'}), 404

        if execution.status != ReportStatus.COMPLETED:
            return jsonify({
                'error': 'Report not ready',
                'status': execution.status.value,
                'message': 'Report must be COMPLETED to download'
            }), 400

        if not execution.file_path:
            return jsonify({'error': 'No file available'}), 404

        file_path = Path(execution.file_path)
        if not file_path.exists():
            return jsonify({
                'error': 'File not found',
                'message': 'Generated file may have been cleaned up'
            }), 404

        # Determine content type from file extension
        content_types = {
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.json': 'application/json'
        }
        content_type = content_types.get(file_path.suffix.lower(), 'application/octet-stream')

        return await send_file(
            str(file_path),
            mimetype=content_type,
            as_attachment=True,
            attachment_filename=file_path.name
        )


# =============================================================================
# Quick Report Endpoints
# =============================================================================

@reports_bp.route('/quick/population', methods=['GET'])
async def get_quick_population():
    """
    Get quick population summary.

    GET /api/v1/reports/quick/population?as_of_date=2026-01-05

    Query params:
        as_of_date: Date for snapshot (defaults to today)

    Returns real-time population data without file generation.
    """
    as_of_date_str = request.args.get('as_of_date')
    as_of_date = date.fromisoformat(as_of_date_str) if as_of_date_str else None

    async with get_async_session() as session:
        service = ReportService(session)
        result = await service.get_quick_population(as_of_date)

        return jsonify({
            'as_of_date': result.as_of_date.isoformat(),
            'total_population': result.total_population,
            'by_status': result.by_status,
            'by_security_level': result.by_security_level,
            'by_housing_unit': result.by_housing_unit,
            'by_gender': result.by_gender,
            'average_age': result.average_age,
            'average_sentence_months': result.average_sentence_months,
            'generated_at': result.generated_at.isoformat(),
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        })


@reports_bp.route('/quick/incidents', methods=['GET'])
async def get_quick_incidents():
    """
    Get quick incident summary.

    GET /api/v1/reports/quick/incidents?start_date=2025-12-01&end_date=2026-01-05

    Query params:
        start_date: Period start (defaults to 30 days ago)
        end_date: Period end (defaults to today)

    Returns real-time incident data without file generation.
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = date.fromisoformat(start_date_str) if start_date_str else None
    end_date = date.fromisoformat(end_date_str) if end_date_str else None

    async with get_async_session() as session:
        service = ReportService(session)
        result = await service.get_quick_incidents(start_date, end_date)

        return jsonify({
            'start_date': result.start_date.isoformat(),
            'end_date': result.end_date.isoformat(),
            'total_incidents': result.total_incidents,
            'by_type': result.by_type,
            'by_severity': result.by_severity,
            'by_status': result.by_status,
            'daily_average': result.daily_average,
            'most_common_type': result.most_common_type,
            'highest_severity_count': result.highest_severity_count,
            'generated_at': result.generated_at.isoformat(),
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        })


@reports_bp.route('/quick/programmes', methods=['GET'])
async def get_quick_programmes():
    """
    Get quick programme summary.

    GET /api/v1/reports/quick/programmes

    Returns real-time programme data without file generation.
    YTD statistics are calculated automatically.
    """
    async with get_async_session() as session:
        service = ReportService(session)
        result = await service.get_quick_programmes()

        return jsonify({
            'total_programmes': result.total_programmes,
            'total_enrolled': result.total_enrolled,
            'total_completed_ytd': result.total_completed_ytd,
            'completion_rate': result.completion_rate,
            'btvi_certifications_ytd': result.btvi_certifications_ytd,
            'by_programme_type': result.by_programme_type,
            'top_programmes': result.top_programmes,
            'generated_at': result.generated_at.isoformat(),
            '_stub': True,
            '_message': 'STUB: Mock data for development'
        })


# =============================================================================
# Report Statistics Endpoint
# =============================================================================

@reports_bp.route('/definitions/<code>/stats', methods=['GET'])
async def get_report_stats(code: str):
    """
    Get execution statistics for a report definition.

    GET /api/v1/reports/definitions/RPT-POP-001/stats

    Returns total executions, success rate, average duration.
    """
    async with get_async_session() as session:
        service = ReportService(session)

        definition = await service.get_definition_by_code(code)
        if not definition:
            return jsonify({'error': 'Report definition not found'}), 404

        stats = await service.get_execution_stats(definition.id)

        return jsonify({
            'report_code': code,
            'report_name': definition.name,
            **stats
        })
