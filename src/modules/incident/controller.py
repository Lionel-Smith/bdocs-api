"""
Incident Management Controller - API endpoints for incident operations.

INCIDENTS:
- POST   /api/v1/incidents                          Create incident
- GET    /api/v1/incidents                          List incidents (with filters)
- GET    /api/v1/incidents/{id}                     Get incident detail
- PUT    /api/v1/incidents/{id}                     Update incident
- PUT    /api/v1/incidents/{id}/status              Update status
- PUT    /api/v1/incidents/{id}/severity            Escalate severity
- PUT    /api/v1/incidents/{id}/resolve             Resolve incident
- PUT    /api/v1/incidents/{id}/close               Close incident
- PUT    /api/v1/incidents/{id}/notify              Mark external notified
- DELETE /api/v1/incidents/{id}                     Delete incident

INVOLVEMENTS:
- POST   /api/v1/incidents/{id}/involvement         Add involvement
- GET    /api/v1/incidents/{id}/involvements        Get involvements
- PUT    /api/v1/incidents/involvements/{id}        Update involvement
- DELETE /api/v1/incidents/involvements/{id}        Delete involvement

ATTACHMENTS:
- POST   /api/v1/incidents/{id}/attachments         Add attachment
- GET    /api/v1/incidents/{id}/attachments         Get attachments
- DELETE /api/v1/incidents/attachments/{id}         Delete attachment

QUERIES:
- GET    /api/v1/incidents/open                     Open incidents
- GET    /api/v1/incidents/critical                 Critical incidents
- GET    /api/v1/inmates/{id}/incidents             Inmate incidents
- GET    /api/v1/incidents/statistics               Statistics
"""
from datetime import date
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import IncidentType, IncidentSeverity, IncidentStatus, InvolvementType
from src.modules.incident.service import IncidentService
from src.modules.incident.dtos import (
    IncidentCreate,
    IncidentUpdate,
    IncidentStatusUpdate,
    IncidentSeverityUpdate,
    IncidentResolve,
    IncidentResponse,
    IncidentListResponse,
    IncidentInvolvementCreate,
    IncidentInvolvementResponse,
    IncidentInvolvementListResponse,
    IncidentAttachmentCreate,
    IncidentAttachmentResponse,
    IncidentAttachmentListResponse,
)

# Create blueprint
incident_bp = Blueprint('incident', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = incident_bp


# ============================================================================
# Incident Endpoints
# ============================================================================

@incident_bp.route('/incidents', methods=['POST'])
async def create_incident():
    """
    Create a new incident report.

    Auto-generates incident number (INC-YYYY-NNNNN).
    Auto-sets external_notification_required for critical incidents.

    Request body: IncidentCreate
    Returns: IncidentResponse (201)
    """
    try:
        data = await request.get_json()
        incident_data = IncidentCreate(**data)

        # Get user ID from auth context (placeholder)
        reported_by = data.get('reported_by')  # TODO: Get from auth context
        if not reported_by:
            return jsonify({"error": "reported_by is required"}), 400

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.create_incident(incident_data, UUID(reported_by))
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                involvement_count=0,
                attachment_count=0,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create incident: {str(e)}"}), 500


@incident_bp.route('/incidents', methods=['GET'])
async def list_incidents():
    """
    List incidents with optional filters.

    Query params:
    - type: Filter by incident type
    - severity: Filter by severity
    - status: Filter by status
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)
    - limit: Max results (default 100)
    - offset: Offset for pagination

    Returns: IncidentListResponse
    """
    try:
        # Parse filters
        type_filter = request.args.get('type')
        severity_filter = request.args.get('severity')
        status_filter = request.args.get('status')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        async with get_async_session() as session:
            service = IncidentService(session)

            # Apply filters
            if start_date_str and end_date_str:
                start_date = date.fromisoformat(start_date_str)
                end_date = date.fromisoformat(end_date_str)
                incident_type = IncidentType(type_filter) if type_filter else None
                incidents = await service.get_incidents_by_date_range(
                    start_date, end_date, incident_type
                )
            elif type_filter:
                incidents = await service.get_incidents_by_type(
                    IncidentType(type_filter), limit
                )
            elif severity_filter:
                incidents = await service.get_incidents_by_severity(
                    IncidentSeverity(severity_filter), limit
                )
            elif status_filter:
                incidents = await service.get_incidents_by_status(
                    IncidentStatus(status_filter), limit
                )
            else:
                incidents = await service.get_all_incidents(limit, offset)

            items = []
            for incident in incidents:
                items.append(IncidentResponse(
                    id=incident.id,
                    incident_number=incident.incident_number,
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    occurred_at=incident.occurred_at,
                    location=incident.location,
                    reported_at=incident.reported_at,
                    reported_by=incident.reported_by,
                    description=incident.description,
                    immediate_actions=incident.immediate_actions,
                    injuries_reported=incident.injuries_reported,
                    property_damage=incident.property_damage,
                    external_notification_required=incident.external_notification_required,
                    external_notified=incident.external_notified,
                    resolution=incident.resolution,
                    resolved_at=incident.resolved_at,
                    resolved_by=incident.resolved_by,
                    is_open=incident.is_open,
                    requires_notification=incident.requires_notification,
                    involvement_count=len(incident.involvements) if incident.involvements else 0,
                    inserted_date=incident.inserted_date,
                    updated_date=incident.updated_date
                ))

            response = IncidentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list incidents: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>', methods=['GET'])
async def get_incident(incident_id: UUID):
    """
    Get incident details with involvements and attachments.

    Returns: IncidentResponse with involvements and attachments
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.get_incident(incident_id, include_attachments=True)

            if not incident:
                return jsonify({"error": "Incident not found"}), 404

            involvements = [
                IncidentInvolvementResponse(
                    id=inv.id,
                    incident_id=inv.incident_id,
                    inmate_id=inv.inmate_id,
                    staff_id=inv.staff_id,
                    involvement_type=inv.involvement_type,
                    description=inv.description,
                    injuries=inv.injuries,
                    disciplinary_action_taken=inv.disciplinary_action_taken,
                    inmate_name=inv.inmate.full_name if inv.inmate else None,
                    inserted_date=inv.inserted_date,
                    updated_date=inv.updated_date
                )
                for inv in (incident.involvements or [])
            ]

            attachments = [
                IncidentAttachmentResponse(
                    id=att.id,
                    incident_id=att.incident_id,
                    file_name=att.file_name,
                    file_type=att.file_type,
                    file_path=att.file_path,
                    uploaded_at=att.uploaded_at,
                    uploaded_by=att.uploaded_by,
                    description=att.description,
                    inserted_date=att.inserted_date
                )
                for att in (incident.attachments or [])
            ]

            response = {
                "incident": IncidentResponse(
                    id=incident.id,
                    incident_number=incident.incident_number,
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    occurred_at=incident.occurred_at,
                    location=incident.location,
                    reported_at=incident.reported_at,
                    reported_by=incident.reported_by,
                    description=incident.description,
                    immediate_actions=incident.immediate_actions,
                    injuries_reported=incident.injuries_reported,
                    property_damage=incident.property_damage,
                    external_notification_required=incident.external_notification_required,
                    external_notified=incident.external_notified,
                    resolution=incident.resolution,
                    resolved_at=incident.resolved_at,
                    resolved_by=incident.resolved_by,
                    is_open=incident.is_open,
                    requires_notification=incident.requires_notification,
                    involvement_count=len(involvements),
                    attachment_count=len(attachments),
                    inserted_date=incident.inserted_date,
                    updated_date=incident.updated_date
                ).model_dump(mode='json'),
                "involvements": [inv.model_dump(mode='json') for inv in involvements],
                "attachments": [att.model_dump(mode='json') for att in attachments]
            }

            return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Failed to get incident: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>', methods=['PUT'])
async def update_incident(incident_id: UUID):
    """
    Update incident details.

    Request body: IncidentUpdate
    Returns: IncidentResponse
    """
    try:
        data = await request.get_json()
        update_data = IncidentUpdate(**data)

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.update_incident(incident_id, update_data)
            await session.commit()

            if not incident:
                return jsonify({"error": "Incident not found"}), 404

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update incident: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/status', methods=['PUT'])
async def update_incident_status(incident_id: UUID):
    """
    Update incident status.

    Request body: {"status": "UNDER_INVESTIGATION", "notes": "..."}
    Returns: IncidentResponse
    """
    try:
        data = await request.get_json()
        status = IncidentStatus(data.get('status'))
        notes = data.get('notes')

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.update_status(incident_id, status, notes)
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/severity', methods=['PUT'])
async def escalate_severity(incident_id: UUID):
    """
    Escalate incident severity.

    Request body: {"severity": "CRITICAL", "reason": "..."}
    Returns: IncidentResponse
    """
    try:
        data = await request.get_json()
        severity = IncidentSeverity(data.get('severity'))
        reason = data.get('reason')

        if not reason:
            return jsonify({"error": "Reason is required for severity change"}), 400

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.escalate_severity(incident_id, severity, reason)
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to escalate severity: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/resolve', methods=['PUT'])
async def resolve_incident(incident_id: UUID):
    """
    Resolve an incident.

    Request body: IncidentResolve
    Returns: IncidentResponse
    """
    try:
        data = await request.get_json()
        resolve_data = IncidentResolve(**data)

        # Get user ID from auth context (placeholder)
        resolved_by = data.get('resolved_by')  # TODO: Get from auth context
        if not resolved_by:
            return jsonify({"error": "resolved_by is required"}), 400

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.resolve_incident(
                incident_id, resolve_data, UUID(resolved_by)
            )
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to resolve incident: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/close', methods=['PUT'])
async def close_incident(incident_id: UUID):
    """
    Close an incident.

    Requires: RESOLVED status and external notification (if required).

    Returns: IncidentResponse
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.close_incident(incident_id)
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to close incident: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/notify', methods=['PUT'])
async def mark_external_notified(incident_id: UUID):
    """
    Mark external notification as completed.

    Request body: {"notes": "Notified police at..."}
    Returns: IncidentResponse
    """
    try:
        data = await request.get_json()
        notes = data.get('notes')

        if not notes:
            return jsonify({"error": "Notes are required for notification record"}), 400

        async with get_async_session() as session:
            service = IncidentService(session)
            incident = await service.mark_external_notified(incident_id, notes)
            await session.commit()

            response = IncidentResponse(
                id=incident.id,
                incident_number=incident.incident_number,
                incident_type=incident.incident_type,
                severity=incident.severity,
                status=incident.status,
                occurred_at=incident.occurred_at,
                location=incident.location,
                reported_at=incident.reported_at,
                reported_by=incident.reported_by,
                description=incident.description,
                immediate_actions=incident.immediate_actions,
                injuries_reported=incident.injuries_reported,
                property_damage=incident.property_damage,
                external_notification_required=incident.external_notification_required,
                external_notified=incident.external_notified,
                resolution=incident.resolution,
                resolved_at=incident.resolved_at,
                resolved_by=incident.resolved_by,
                is_open=incident.is_open,
                requires_notification=incident.requires_notification,
                inserted_date=incident.inserted_date,
                updated_date=incident.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to mark notification: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>', methods=['DELETE'])
async def delete_incident(incident_id: UUID):
    """Soft delete an incident."""
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            success = await service.delete_incident(incident_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Incident not found"}), 404

            return jsonify({"message": "Incident deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete incident: {str(e)}"}), 500


# ============================================================================
# Involvement Endpoints
# ============================================================================

@incident_bp.route('/incidents/<uuid:incident_id>/involvement', methods=['POST'])
async def add_involvement(incident_id: UUID):
    """
    Add involvement record to an incident.

    Request body: IncidentInvolvementCreate
    Returns: IncidentInvolvementResponse (201)
    """
    try:
        data = await request.get_json()
        involvement_data = IncidentInvolvementCreate(**data)

        async with get_async_session() as session:
            service = IncidentService(session)
            involvement = await service.add_involvement(incident_id, involvement_data)
            await session.commit()

            response = IncidentInvolvementResponse(
                id=involvement.id,
                incident_id=involvement.incident_id,
                inmate_id=involvement.inmate_id,
                staff_id=involvement.staff_id,
                involvement_type=involvement.involvement_type,
                description=involvement.description,
                injuries=involvement.injuries,
                disciplinary_action_taken=involvement.disciplinary_action_taken,
                inserted_date=involvement.inserted_date,
                updated_date=involvement.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to add involvement: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/involvements', methods=['GET'])
async def get_incident_involvements(incident_id: UUID):
    """
    Get all involvements for an incident.

    Returns: IncidentInvolvementListResponse
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            involvements = await service.get_incident_involvements(incident_id)

            items = [
                IncidentInvolvementResponse(
                    id=inv.id,
                    incident_id=inv.incident_id,
                    inmate_id=inv.inmate_id,
                    staff_id=inv.staff_id,
                    involvement_type=inv.involvement_type,
                    description=inv.description,
                    injuries=inv.injuries,
                    disciplinary_action_taken=inv.disciplinary_action_taken,
                    inmate_name=inv.inmate.full_name if inv.inmate else None,
                    inserted_date=inv.inserted_date,
                    updated_date=inv.updated_date
                )
                for inv in involvements
            ]

            response = IncidentInvolvementListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get involvements: {str(e)}"}), 500


@incident_bp.route('/incidents/involvements/<uuid:involvement_id>', methods=['DELETE'])
async def delete_involvement(involvement_id: UUID):
    """Delete an involvement record."""
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            success = await service.delete_involvement(involvement_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Involvement not found"}), 404

            return jsonify({"message": "Involvement deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete involvement: {str(e)}"}), 500


# ============================================================================
# Attachment Endpoints
# ============================================================================

@incident_bp.route('/incidents/<uuid:incident_id>/attachments', methods=['POST'])
async def add_attachment(incident_id: UUID):
    """
    Add an attachment to an incident.

    Request body: IncidentAttachmentCreate
    Returns: IncidentAttachmentResponse (201)
    """
    try:
        data = await request.get_json()
        attachment_data = IncidentAttachmentCreate(**data)

        # Get user ID from auth context (placeholder)
        uploaded_by = data.get('uploaded_by')  # TODO: Get from auth context
        if not uploaded_by:
            return jsonify({"error": "uploaded_by is required"}), 400

        async with get_async_session() as session:
            service = IncidentService(session)
            attachment = await service.add_attachment(
                incident_id, attachment_data, UUID(uploaded_by)
            )
            await session.commit()

            response = IncidentAttachmentResponse(
                id=attachment.id,
                incident_id=attachment.incident_id,
                file_name=attachment.file_name,
                file_type=attachment.file_type,
                file_path=attachment.file_path,
                uploaded_at=attachment.uploaded_at,
                uploaded_by=attachment.uploaded_by,
                description=attachment.description,
                inserted_date=attachment.inserted_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to add attachment: {str(e)}"}), 500


@incident_bp.route('/incidents/<uuid:incident_id>/attachments', methods=['GET'])
async def get_incident_attachments(incident_id: UUID):
    """
    Get all attachments for an incident.

    Returns: IncidentAttachmentListResponse
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            attachments = await service.get_incident_attachments(incident_id)

            items = [
                IncidentAttachmentResponse(
                    id=att.id,
                    incident_id=att.incident_id,
                    file_name=att.file_name,
                    file_type=att.file_type,
                    file_path=att.file_path,
                    uploaded_at=att.uploaded_at,
                    uploaded_by=att.uploaded_by,
                    description=att.description,
                    inserted_date=att.inserted_date
                )
                for att in attachments
            ]

            response = IncidentAttachmentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get attachments: {str(e)}"}), 500


@incident_bp.route('/incidents/attachments/<uuid:attachment_id>', methods=['DELETE'])
async def delete_attachment(attachment_id: UUID):
    """Delete an attachment."""
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            success = await service.delete_attachment(attachment_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Attachment not found"}), 404

            return jsonify({"message": "Attachment deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete attachment: {str(e)}"}), 500


# ============================================================================
# Query Endpoints
# ============================================================================

@incident_bp.route('/incidents/open', methods=['GET'])
async def get_open_incidents():
    """
    Get all open (non-closed) incidents.

    Returns: IncidentListResponse
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            incidents = await service.get_open_incidents()

            items = [
                IncidentResponse(
                    id=incident.id,
                    incident_number=incident.incident_number,
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    occurred_at=incident.occurred_at,
                    location=incident.location,
                    reported_at=incident.reported_at,
                    reported_by=incident.reported_by,
                    description=incident.description,
                    immediate_actions=incident.immediate_actions,
                    injuries_reported=incident.injuries_reported,
                    property_damage=incident.property_damage,
                    external_notification_required=incident.external_notification_required,
                    external_notified=incident.external_notified,
                    resolution=incident.resolution,
                    resolved_at=incident.resolved_at,
                    resolved_by=incident.resolved_by,
                    is_open=incident.is_open,
                    requires_notification=incident.requires_notification,
                    involvement_count=len(incident.involvements) if incident.involvements else 0,
                    inserted_date=incident.inserted_date,
                    updated_date=incident.updated_date
                )
                for incident in incidents
            ]

            response = IncidentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get open incidents: {str(e)}"}), 500


@incident_bp.route('/incidents/critical', methods=['GET'])
async def get_critical_incidents():
    """
    Get critical severity incidents.

    Query params:
    - open_only: Only open incidents (default: true)

    Returns: IncidentListResponse
    """
    try:
        open_only = request.args.get('open_only', 'true').lower() == 'true'

        async with get_async_session() as session:
            service = IncidentService(session)
            incidents = await service.get_critical_incidents(open_only)

            items = [
                IncidentResponse(
                    id=incident.id,
                    incident_number=incident.incident_number,
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    occurred_at=incident.occurred_at,
                    location=incident.location,
                    reported_at=incident.reported_at,
                    reported_by=incident.reported_by,
                    description=incident.description,
                    immediate_actions=incident.immediate_actions,
                    injuries_reported=incident.injuries_reported,
                    property_damage=incident.property_damage,
                    external_notification_required=incident.external_notification_required,
                    external_notified=incident.external_notified,
                    resolution=incident.resolution,
                    resolved_at=incident.resolved_at,
                    resolved_by=incident.resolved_by,
                    is_open=incident.is_open,
                    requires_notification=incident.requires_notification,
                    involvement_count=len(incident.involvements) if incident.involvements else 0,
                    inserted_date=incident.inserted_date,
                    updated_date=incident.updated_date
                )
                for incident in incidents
            ]

            response = IncidentListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get critical incidents: {str(e)}"}), 500


@incident_bp.route('/inmates/<uuid:inmate_id>/incidents', methods=['GET'])
async def get_inmate_incidents(inmate_id: UUID):
    """
    Get incident summary for an inmate.

    Returns: InmateIncidentSummary
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            summary = await service.get_inmate_incident_summary(inmate_id)
            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get inmate incidents: {str(e)}"}), 500


@incident_bp.route('/incidents/statistics', methods=['GET'])
async def get_statistics():
    """
    Get incident statistics.

    Returns: IncidentStatistics
    """
    try:
        async with get_async_session() as session:
            service = IncidentService(session)
            stats = await service.get_statistics()
            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500
