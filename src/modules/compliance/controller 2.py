"""
Compliance Controller - REST API endpoints for ACA compliance management.

Provides endpoints for ACA standards, audits, findings, compliance reports,
and corrective action tracking.

Endpoints:
- GET /api/v1/compliance/standards - List all ACA standards
- GET /api/v1/compliance/standards/{id} - Get standard details
- GET /api/v1/compliance/audits - List audits
- POST /api/v1/compliance/audits - Create new audit
- GET /api/v1/compliance/audits/{id} - Get audit with findings
- PUT /api/v1/compliance/audits/{id} - Update audit
- PUT /api/v1/compliance/audits/{id}/status - Update audit status
- POST /api/v1/compliance/audits/{id}/start - Start scheduled audit
- POST /api/v1/compliance/audits/{id}/findings - Add findings to audit
- GET /api/v1/compliance/findings/{id} - Get finding details
- PUT /api/v1/compliance/findings/{id} - Update finding
- POST /api/v1/compliance/findings/{id}/complete - Complete corrective action
- GET /api/v1/compliance/corrective-actions/overdue - List overdue actions
- GET /api/v1/compliance/corrective-actions/open - List open actions
- GET /api/v1/compliance/report - Generate compliance report
- GET /api/v1/compliance/dashboard - Compliance dashboard
"""
from datetime import date
from typing import Optional, List
from uuid import UUID

from quart import Blueprint, request, jsonify
from quart_schema import validate_request

from src.database.async_db import get_async_session
from src.modules.compliance.service import ComplianceService
from src.modules.compliance.dtos import (
    AuditCreateDTO, AuditUpdateDTO, AuditStatusUpdateDTO,
    FindingCreateDTO, FindingUpdateDTO, FindingCompleteDTO
)
from src.common.enums import ACACategory, AuditType, AuditStatus, ComplianceStatus

# Blueprint for auto-discovery
compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/v1/compliance')
blueprint = compliance_bp  # Alias for auto-discovery


# =============================================================================
# ACA Standards Endpoints (Read-Only)
# =============================================================================

@compliance_bp.route('/standards', methods=['GET'])
async def get_all_standards():
    """
    Get all ACA standards with optional filters.

    GET /api/v1/compliance/standards?category=SAFETY&is_mandatory=true

    Query params:
        category: Filter by ACA category
        is_mandatory: Filter by mandatory flag
        skip: Pagination offset
        limit: Page size (max 100)
    """
    category_str = request.args.get('category')
    is_mandatory_str = request.args.get('is_mandatory')
    skip = int(request.args.get('skip', 0))
    limit = min(int(request.args.get('limit', 100)), 100)

    category = ACACategory(category_str) if category_str else None
    is_mandatory = is_mandatory_str.lower() == 'true' if is_mandatory_str else None

    async with get_async_session() as session:
        service = ComplianceService(session)
        standards = await service.get_all_standards(
            category=category,
            is_mandatory=is_mandatory,
            skip=skip,
            limit=limit
        )

        total = await service.count_standards(category, is_mandatory)

        return jsonify({
            'items': [{
                'id': str(s.id),
                'standard_number': s.standard_number,
                'category': s.category.value,
                'title': s.title,
                'is_mandatory': s.is_mandatory
            } for s in standards],
            'total': total,
            'skip': skip,
            'limit': limit
        })


@compliance_bp.route('/standards/<uuid:standard_id>', methods=['GET'])
async def get_standard(standard_id: UUID):
    """
    Get ACA standard details by ID.

    GET /api/v1/compliance/standards/{id}
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        standard = await service.get_standard(standard_id)

        if not standard:
            return jsonify({'error': 'Standard not found'}), 404

        return jsonify({
            'id': str(standard.id),
            'standard_number': standard.standard_number,
            'category': standard.category.value,
            'title': standard.title,
            'description': standard.description,
            'is_mandatory': standard.is_mandatory,
            'evidence_required': standard.evidence_required,
            'inserted_date': standard.inserted_date.isoformat() if standard.inserted_date else None,
            'updated_date': standard.updated_date.isoformat() if standard.updated_date else None
        })


@compliance_bp.route('/standards/by-number/<string:standard_number>', methods=['GET'])
async def get_standard_by_number(standard_number: str):
    """
    Get ACA standard by standard number (e.g., '4-4001').

    GET /api/v1/compliance/standards/by-number/4-4001
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        standard = await service.get_standard_by_number(standard_number)

        if not standard:
            return jsonify({'error': 'Standard not found'}), 404

        return jsonify({
            'id': str(standard.id),
            'standard_number': standard.standard_number,
            'category': standard.category.value,
            'title': standard.title,
            'description': standard.description,
            'is_mandatory': standard.is_mandatory,
            'evidence_required': standard.evidence_required
        })


@compliance_bp.route('/standards/categories/<string:category>', methods=['GET'])
async def get_standards_by_category(category: str):
    """
    Get all standards in a specific ACA category.

    GET /api/v1/compliance/standards/categories/SAFETY
    """
    try:
        aca_category = ACACategory(category)
    except ValueError:
        return jsonify({'error': f'Invalid category: {category}'}), 400

    async with get_async_session() as session:
        service = ComplianceService(session)
        standards = await service.get_standards_by_category(aca_category)

        return jsonify({
            'category': category,
            'count': len(standards),
            'items': [{
                'id': str(s.id),
                'standard_number': s.standard_number,
                'title': s.title,
                'is_mandatory': s.is_mandatory
            } for s in standards]
        })


# =============================================================================
# Compliance Audit Endpoints
# =============================================================================

@compliance_bp.route('/audits', methods=['GET'])
async def get_all_audits():
    """
    Get all compliance audits with optional filters.

    GET /api/v1/compliance/audits?audit_type=OFFICIAL&status=COMPLETED&year=2026

    Query params:
        audit_type: Filter by audit type
        status: Filter by status
        year: Filter by year
        skip: Pagination offset
        limit: Page size (max 100)
    """
    audit_type_str = request.args.get('audit_type')
    status_str = request.args.get('status')
    year_str = request.args.get('year')
    skip = int(request.args.get('skip', 0))
    limit = min(int(request.args.get('limit', 100)), 100)

    audit_type = AuditType(audit_type_str) if audit_type_str else None
    status = AuditStatus(status_str) if status_str else None
    year = int(year_str) if year_str else None

    async with get_async_session() as session:
        service = ComplianceService(session)
        audits = await service.get_all_audits(
            audit_type=audit_type,
            status=status,
            year=year,
            skip=skip,
            limit=limit
        )

        return jsonify({
            'items': [{
                'id': str(a.id),
                'audit_date': a.audit_date.isoformat(),
                'auditor_name': a.auditor_name,
                'audit_type': a.audit_type.value,
                'status': a.status.value,
                'overall_score': float(a.overall_score) if a.overall_score else None,
                'corrective_actions_required': a.corrective_actions_required
            } for a in audits],
            'skip': skip,
            'limit': limit
        })


@compliance_bp.route('/audits', methods=['POST'])
@validate_request(AuditCreateDTO)
async def create_audit(data: AuditCreateDTO):
    """
    Create a new compliance audit.

    POST /api/v1/compliance/audits

    Body:
        audit_date: Date of audit
        auditor_name: Name of auditor
        audit_type: Type of audit
        next_audit_date: Optional next audit date
    """
    # TODO: Get created_by from authenticated user
    created_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.create_audit(data, created_by)
        await session.commit()

        return jsonify({
            'id': str(audit.id),
            'audit_date': audit.audit_date.isoformat(),
            'auditor_name': audit.auditor_name,
            'audit_type': audit.audit_type.value,
            'status': audit.status.value,
            'message': 'Compliance audit created'
        }), 201


@compliance_bp.route('/audits/<uuid:audit_id>', methods=['GET'])
async def get_audit(audit_id: UUID):
    """
    Get audit details with findings.

    GET /api/v1/compliance/audits/{id}
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.get_audit(audit_id)

        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        findings = await service.get_audit_findings(audit_id)

        # Calculate finding counts
        compliant_count = sum(1 for f in findings if f.compliance_status == ComplianceStatus.COMPLIANT)
        non_compliant_count = sum(1 for f in findings if f.compliance_status == ComplianceStatus.NON_COMPLIANT)
        partial_count = sum(1 for f in findings if f.compliance_status == ComplianceStatus.PARTIAL)

        return jsonify({
            'id': str(audit.id),
            'audit_date': audit.audit_date.isoformat(),
            'auditor_name': audit.auditor_name,
            'audit_type': audit.audit_type.value,
            'status': audit.status.value,
            'overall_score': float(audit.overall_score) if audit.overall_score else None,
            'findings_summary': audit.findings_summary,
            'corrective_actions_required': audit.corrective_actions_required,
            'next_audit_date': audit.next_audit_date.isoformat() if audit.next_audit_date else None,
            'created_by': str(audit.created_by),
            'creator_name': audit.creator.full_name if audit.creator else None,
            'total_findings': len(findings),
            'compliant_count': compliant_count,
            'non_compliant_count': non_compliant_count,
            'partial_count': partial_count,
            'findings': [{
                'id': str(f.id),
                'standard_number': f.standard.standard_number if f.standard else None,
                'standard_title': f.standard.title if f.standard else None,
                'compliance_status': f.compliance_status.value,
                'corrective_action': f.corrective_action,
                'corrective_action_due': f.corrective_action_due.isoformat() if f.corrective_action_due else None,
                'is_overdue': f.is_overdue
            } for f in findings],
            'inserted_date': audit.inserted_date.isoformat() if audit.inserted_date else None,
            'updated_date': audit.updated_date.isoformat() if audit.updated_date else None
        })


@compliance_bp.route('/audits/<uuid:audit_id>', methods=['PUT'])
@validate_request(AuditUpdateDTO)
async def update_audit(audit_id: UUID, data: AuditUpdateDTO):
    """
    Update audit details.

    PUT /api/v1/compliance/audits/{id}

    Body:
        auditor_name: Optional new auditor name
        findings_summary: Optional summary
        next_audit_date: Optional next audit date
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.update_audit(audit_id, data)

        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(audit.id),
            'message': 'Audit updated successfully'
        })


@compliance_bp.route('/audits/<uuid:audit_id>/status', methods=['PUT'])
@validate_request(AuditStatusUpdateDTO)
async def update_audit_status(audit_id: UUID, data: AuditStatusUpdateDTO):
    """
    Update audit status.

    When completing an audit, overall score is calculated automatically.

    PUT /api/v1/compliance/audits/{id}/status

    Body:
        status: New status
        findings_summary: Optional summary
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.update_audit_status(audit_id, data)

        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(audit.id),
            'status': audit.status.value,
            'overall_score': float(audit.overall_score) if audit.overall_score else None,
            'message': f'Audit status updated to {audit.status.value}'
        })


@compliance_bp.route('/audits/<uuid:audit_id>/start', methods=['POST'])
async def start_audit(audit_id: UUID):
    """
    Start a scheduled audit (change status to IN_PROGRESS).

    POST /api/v1/compliance/audits/{id}/start
    """
    async with get_async_session() as session:
        service = ComplianceService(session)

        try:
            audit = await service.start_audit(audit_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(audit.id),
            'status': audit.status.value,
            'message': 'Audit started'
        })


@compliance_bp.route('/audits/latest', methods=['GET'])
async def get_latest_audit():
    """
    Get the most recent audit.

    GET /api/v1/compliance/audits/latest?audit_type=OFFICIAL

    Query params:
        audit_type: Optional filter by type
    """
    audit_type_str = request.args.get('audit_type')
    audit_type = AuditType(audit_type_str) if audit_type_str else None

    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.get_latest_audit(audit_type)

        if not audit:
            return jsonify({'error': 'No audits found'}), 404

        return jsonify({
            'id': str(audit.id),
            'audit_date': audit.audit_date.isoformat(),
            'auditor_name': audit.auditor_name,
            'audit_type': audit.audit_type.value,
            'status': audit.status.value,
            'overall_score': float(audit.overall_score) if audit.overall_score else None
        })


@compliance_bp.route('/audits/next-scheduled', methods=['GET'])
async def get_next_scheduled_audit():
    """
    Get the next scheduled audit.

    GET /api/v1/compliance/audits/next-scheduled
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        audit = await service.get_next_scheduled_audit()

        if not audit:
            return jsonify({'error': 'No scheduled audits found'}), 404

        days_until = (audit.audit_date - date.today()).days

        return jsonify({
            'id': str(audit.id),
            'audit_date': audit.audit_date.isoformat(),
            'auditor_name': audit.auditor_name,
            'audit_type': audit.audit_type.value,
            'days_until': days_until
        })


# =============================================================================
# Audit Findings Endpoints
# =============================================================================

@compliance_bp.route('/audits/<uuid:audit_id>/findings', methods=['POST'])
@validate_request(FindingCreateDTO)
async def add_finding(audit_id: UUID, data: FindingCreateDTO):
    """
    Add a finding to an audit.

    POST /api/v1/compliance/audits/{id}/findings

    Body:
        standard_id: ID of standard being evaluated
        compliance_status: Status (COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE)
        evidence_provided: Optional evidence description
        finding_notes: Optional notes
        corrective_action: Optional corrective action
        corrective_action_due: Optional due date
    """
    async with get_async_session() as session:
        service = ComplianceService(session)

        # Verify audit exists
        audit = await service.get_audit(audit_id)
        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        finding = await service.create_finding(audit_id, data)
        await session.commit()

        return jsonify({
            'id': str(finding.id),
            'audit_id': str(finding.audit_id),
            'standard_id': str(finding.standard_id),
            'compliance_status': finding.compliance_status.value,
            'message': 'Finding added to audit'
        }), 201


@compliance_bp.route('/audits/<uuid:audit_id>/findings/bulk', methods=['POST'])
async def add_findings_bulk(audit_id: UUID):
    """
    Add multiple findings to an audit at once.

    POST /api/v1/compliance/audits/{id}/findings/bulk

    Body: Array of FindingCreateDTO objects
    """
    async with get_async_session() as session:
        service = ComplianceService(session)

        # Verify audit exists
        audit = await service.get_audit(audit_id)
        if not audit:
            return jsonify({'error': 'Audit not found'}), 404

        data = await request.get_json()

        if not isinstance(data, list):
            return jsonify({'error': 'Body must be an array of findings'}), 400

        findings_data = [FindingCreateDTO(**item) for item in data]
        findings = await service.create_findings_bulk(audit_id, findings_data)
        await session.commit()

        return jsonify({
            'count': len(findings),
            'findings': [{
                'id': str(f.id),
                'standard_id': str(f.standard_id),
                'compliance_status': f.compliance_status.value
            } for f in findings],
            'message': f'{len(findings)} findings added to audit'
        }), 201


@compliance_bp.route('/audits/<uuid:audit_id>/findings', methods=['GET'])
async def get_audit_findings(audit_id: UUID):
    """
    Get all findings for an audit.

    GET /api/v1/compliance/audits/{id}/findings?compliance_status=NON_COMPLIANT

    Query params:
        compliance_status: Filter by status
    """
    status_str = request.args.get('compliance_status')
    status = ComplianceStatus(status_str) if status_str else None

    async with get_async_session() as session:
        service = ComplianceService(session)
        findings = await service.get_audit_findings(audit_id, status)

        return jsonify({
            'audit_id': str(audit_id),
            'count': len(findings),
            'items': [{
                'id': str(f.id),
                'standard_id': str(f.standard_id),
                'standard_number': f.standard.standard_number if f.standard else None,
                'standard_title': f.standard.title if f.standard else None,
                'standard_category': f.standard.category.value if f.standard else None,
                'is_mandatory': f.standard.is_mandatory if f.standard else None,
                'compliance_status': f.compliance_status.value,
                'evidence_provided': f.evidence_provided,
                'finding_notes': f.finding_notes,
                'corrective_action': f.corrective_action,
                'corrective_action_due': f.corrective_action_due.isoformat() if f.corrective_action_due else None,
                'corrective_action_completed': f.corrective_action_completed.isoformat() if f.corrective_action_completed else None,
                'is_overdue': f.is_overdue
            } for f in findings]
        })


@compliance_bp.route('/findings/<uuid:finding_id>', methods=['GET'])
async def get_finding(finding_id: UUID):
    """
    Get finding details.

    GET /api/v1/compliance/findings/{id}
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        finding = await service.get_finding(finding_id)

        if not finding:
            return jsonify({'error': 'Finding not found'}), 404

        return jsonify({
            'id': str(finding.id),
            'audit_id': str(finding.audit_id),
            'standard_id': str(finding.standard_id),
            'standard_number': finding.standard.standard_number if finding.standard else None,
            'standard_title': finding.standard.title if finding.standard else None,
            'standard_category': finding.standard.category.value if finding.standard else None,
            'is_mandatory': finding.standard.is_mandatory if finding.standard else None,
            'compliance_status': finding.compliance_status.value,
            'evidence_provided': finding.evidence_provided,
            'finding_notes': finding.finding_notes,
            'corrective_action': finding.corrective_action,
            'corrective_action_due': finding.corrective_action_due.isoformat() if finding.corrective_action_due else None,
            'corrective_action_completed': finding.corrective_action_completed.isoformat() if finding.corrective_action_completed else None,
            'is_overdue': finding.is_overdue,
            'verified_by': str(finding.verified_by) if finding.verified_by else None,
            'verifier_name': finding.verifier.full_name if finding.verifier else None,
            'inserted_date': finding.inserted_date.isoformat() if finding.inserted_date else None,
            'updated_date': finding.updated_date.isoformat() if finding.updated_date else None
        })


@compliance_bp.route('/findings/<uuid:finding_id>', methods=['PUT'])
@validate_request(FindingUpdateDTO)
async def update_finding(finding_id: UUID, data: FindingUpdateDTO):
    """
    Update a finding.

    PUT /api/v1/compliance/findings/{id}

    Body:
        compliance_status: Optional new status
        evidence_provided: Optional evidence
        finding_notes: Optional notes
        corrective_action: Optional corrective action
        corrective_action_due: Optional due date
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        finding = await service.update_finding(finding_id, data)

        if not finding:
            return jsonify({'error': 'Finding not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(finding.id),
            'compliance_status': finding.compliance_status.value,
            'message': 'Finding updated successfully'
        })


@compliance_bp.route('/findings/<uuid:finding_id>/complete', methods=['POST'])
@validate_request(FindingCompleteDTO)
async def complete_corrective_action(finding_id: UUID, data: FindingCompleteDTO):
    """
    Mark a corrective action as completed.

    POST /api/v1/compliance/findings/{id}/complete

    Body:
        completion_notes: Optional notes about completion
    """
    # TODO: Get verified_by from authenticated user
    verified_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = ComplianceService(session)

        try:
            finding = await service.complete_corrective_action(finding_id, data, verified_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not finding:
            return jsonify({'error': 'Finding not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(finding.id),
            'corrective_action_completed': finding.corrective_action_completed.isoformat(),
            'verified_by': str(finding.verified_by),
            'message': 'Corrective action marked as completed'
        })


# =============================================================================
# Corrective Actions Endpoints
# =============================================================================

@compliance_bp.route('/corrective-actions/overdue', methods=['GET'])
async def get_overdue_corrective_actions():
    """
    Get all overdue corrective actions.

    GET /api/v1/compliance/corrective-actions/overdue
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        actions = await service.get_overdue_corrective_actions()

        return jsonify({
            'count': len(actions),
            'items': [{
                'finding_id': str(a.finding_id),
                'audit_id': str(a.audit_id),
                'audit_date': a.audit_date.isoformat(),
                'audit_type': a.audit_type.value,
                'standard_number': a.standard_number,
                'standard_title': a.standard_title,
                'category': a.category.value,
                'is_mandatory': a.is_mandatory,
                'corrective_action': a.corrective_action,
                'corrective_action_due': a.corrective_action_due.isoformat(),
                'days_overdue': a.days_overdue
            } for a in actions]
        })


@compliance_bp.route('/corrective-actions/open', methods=['GET'])
async def get_open_corrective_actions():
    """
    Get all open (incomplete) corrective actions.

    GET /api/v1/compliance/corrective-actions/open
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        findings = await service.get_open_corrective_actions()
        today = date.today()

        return jsonify({
            'count': len(findings),
            'items': [{
                'finding_id': str(f.id),
                'audit_id': str(f.audit_id),
                'standard_number': f.standard.standard_number if f.standard else None,
                'standard_title': f.standard.title if f.standard else None,
                'corrective_action': f.corrective_action,
                'corrective_action_due': f.corrective_action_due.isoformat() if f.corrective_action_due else None,
                'is_overdue': f.is_overdue,
                'days_until_due': (f.corrective_action_due - today).days if f.corrective_action_due else None
            } for f in findings]
        })


# =============================================================================
# Report Endpoints
# =============================================================================

@compliance_bp.route('/report', methods=['GET'])
async def generate_compliance_report():
    """
    Generate comprehensive compliance report.

    Aggregates data from all BDOCS modules for ACA reporting.

    GET /api/v1/compliance/report?facility_name=BDOCS
    """
    facility_name = request.args.get('facility_name', 'Bahamas Department of Correctional Services')

    async with get_async_session() as session:
        service = ComplianceService(session)
        report = await service.generate_compliance_report(facility_name)

        return jsonify({
            'report_date': report.report_date.isoformat(),
            'facility_name': report.facility_name,
            'overall_compliance_score': report.overall_compliance_score,
            'mandatory_standards_met': report.mandatory_standards_met,
            'mandatory_standards_total': report.mandatory_standards_total,
            'non_mandatory_standards_met': report.non_mandatory_standards_met,
            'non_mandatory_standards_total': report.non_mandatory_standards_total,
            'inmate_statistics': {
                'total_inmates': report.inmate_statistics.total_inmates,
                'by_status': report.inmate_statistics.by_status,
                'by_security_level': report.inmate_statistics.by_security_level,
                'average_age': report.inmate_statistics.average_age
            },
            'incident_statistics': {
                'total_incidents_year': report.incident_statistics.total_incidents_year,
                'by_type': report.incident_statistics.by_type,
                'by_severity': report.incident_statistics.by_severity,
                'average_resolution_days': report.incident_statistics.average_resolution_days
            },
            'training_statistics': {
                'total_staff': report.training_statistics.total_staff,
                'training_completion_rate': report.training_statistics.training_completion_rate,
                'certifications_current': report.training_statistics.certifications_current,
                'certifications_expired': report.training_statistics.certifications_expired,
                'certifications_expiring_30_days': report.training_statistics.certifications_expiring_30_days
            },
            'healthcare_statistics': {
                'inmates_with_medical_records': report.healthcare_statistics.inmates_with_medical_records,
                'intake_screenings_completed': report.healthcare_statistics.intake_screenings_completed,
                'mental_health_flagged': report.healthcare_statistics.mental_health_flagged,
                'on_suicide_watch': report.healthcare_statistics.on_suicide_watch,
                'medication_compliance_rate': report.healthcare_statistics.medication_compliance_rate
            },
            'programme_statistics': {
                'total_programmes': report.programme_statistics.total_programmes,
                'active_enrollments': report.programme_statistics.active_enrollments,
                'completion_rate': report.programme_statistics.completion_rate,
                'btvi_certifications_issued': report.programme_statistics.btvi_certifications_issued
            },
            'by_category': report.by_category,
            'open_corrective_actions': report.open_corrective_actions,
            'overdue_corrective_actions': report.overdue_corrective_actions,
            'last_audit_date': report.last_audit_date.isoformat() if report.last_audit_date else None,
            'last_audit_score': report.last_audit_score,
            'next_scheduled_audit': report.next_scheduled_audit.isoformat() if report.next_scheduled_audit else None
        })


@compliance_bp.route('/dashboard', methods=['GET'])
async def get_compliance_dashboard():
    """
    Get compliance dashboard summary.

    GET /api/v1/compliance/dashboard
    """
    async with get_async_session() as session:
        service = ComplianceService(session)
        dashboard = await service.get_dashboard()

        return jsonify({
            'overall_compliance_score': dashboard.overall_compliance_score,
            'mandatory_compliance_rate': dashboard.mandatory_compliance_rate,
            'total_standards': dashboard.total_standards,
            'mandatory_standards': dashboard.mandatory_standards,
            'audits_this_year': dashboard.audits_this_year,
            'last_audit_date': dashboard.last_audit_date.isoformat() if dashboard.last_audit_date else None,
            'last_audit_type': dashboard.last_audit_type.value if dashboard.last_audit_type else None,
            'last_audit_score': dashboard.last_audit_score,
            'next_scheduled_audit': dashboard.next_scheduled_audit.isoformat() if dashboard.next_scheduled_audit else None,
            'open_corrective_actions': dashboard.open_corrective_actions,
            'overdue_corrective_actions': dashboard.overdue_corrective_actions,
            'corrective_actions_completed_month': dashboard.corrective_actions_completed_month,
            'compliance_by_category': dashboard.compliance_by_category,
            'alerts': dashboard.alerts
        })
