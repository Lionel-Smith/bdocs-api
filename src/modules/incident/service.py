"""
Incident Management Service - Business logic for incident operations.

Key features:
1. Auto-generated incident numbers (INC-YYYY-NNNNN)
2. Severity escalation with notification triggers
3. Status workflow enforcement
4. Involvement tracking for inmates and staff
5. Attachment management for evidence

CRITICAL: Death and escape incidents automatically require external notification.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.incident.models import (
    Incident,
    IncidentInvolvement,
    IncidentAttachment
)
from src.modules.incident.repository import (
    IncidentRepository,
    IncidentInvolvementRepository,
    IncidentAttachmentRepository
)
from src.modules.incident.dtos import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentResolve,
    IncidentInvolvementCreate,
    IncidentInvolvementResponse,
    IncidentAttachmentCreate,
    IncidentAttachmentResponse,
    IncidentStatistics,
    IncidentTypeCount,
    IncidentSeverityCount,
    InmateIncidentSummary
)
from src.common.enums import (
    IncidentType, IncidentSeverity, IncidentStatus, InvolvementType
)


# Incident types that require external notification
NOTIFICATION_REQUIRED_TYPES = {
    IncidentType.DEATH.value,
    IncidentType.ESCAPE_ATTEMPT.value,
}


class IncidentService:
    """Service for incident management business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)
        self.involvement_repo = IncidentInvolvementRepository(session)
        self.attachment_repo = IncidentAttachmentRepository(session)

    # ========================================================================
    # Incident Operations
    # ========================================================================

    async def create_incident(
        self,
        data: IncidentCreate,
        reported_by: UUID
    ) -> Incident:
        """
        Create a new incident with auto-generated incident number.

        Automatically sets external_notification_required for:
        - DEATH incidents
        - ESCAPE_ATTEMPT incidents
        - CRITICAL severity incidents
        """
        # Generate incident number
        year = datetime.now().year
        incident_number = await self.incident_repo.get_next_incident_number(year)

        # Determine if external notification is required
        notification_required = data.external_notification_required
        if data.incident_type.value in NOTIFICATION_REQUIRED_TYPES:
            notification_required = True
        if data.severity == IncidentSeverity.CRITICAL:
            notification_required = True

        incident = Incident(
            incident_number=incident_number,
            incident_type=data.incident_type.value,
            severity=data.severity.value,
            status=IncidentStatus.REPORTED.value,
            occurred_at=data.occurred_at,
            location=data.location,
            reported_at=datetime.now(),
            reported_by=reported_by,
            description=data.description,
            immediate_actions=data.immediate_actions,
            injuries_reported=data.injuries_reported,
            property_damage=data.property_damage,
            external_notification_required=notification_required,
            external_notified=False
        )

        return await self.incident_repo.create(incident)

    async def get_incident(
        self,
        incident_id: UUID,
        include_attachments: bool = False
    ) -> Optional[Incident]:
        """Get incident by ID."""
        return await self.incident_repo.get_by_id(
            incident_id,
            include_involvements=True,
            include_attachments=include_attachments
        )

    async def get_incident_by_number(self, incident_number: str) -> Optional[Incident]:
        """Get incident by incident number."""
        return await self.incident_repo.get_by_number(incident_number)

    async def get_all_incidents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Incident]:
        """Get all incidents with pagination."""
        return await self.incident_repo.get_all(limit, offset)

    async def get_incidents_by_type(
        self,
        incident_type: IncidentType,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents filtered by type."""
        return await self.incident_repo.get_by_type(incident_type.value, limit)

    async def get_incidents_by_severity(
        self,
        severity: IncidentSeverity,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents filtered by severity."""
        return await self.incident_repo.get_by_severity(severity.value, limit)

    async def get_incidents_by_status(
        self,
        status: IncidentStatus,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents filtered by status."""
        return await self.incident_repo.get_by_status(status.value, limit)

    async def get_open_incidents(self) -> List[Incident]:
        """Get all open (non-closed) incidents."""
        return await self.incident_repo.get_open_incidents()

    async def get_critical_incidents(
        self,
        open_only: bool = True
    ) -> List[Incident]:
        """Get critical severity incidents."""
        return await self.incident_repo.get_critical_incidents(open_only)

    async def get_incidents_by_date_range(
        self,
        start_date: date,
        end_date: date,
        incident_type: Optional[IncidentType] = None
    ) -> List[Incident]:
        """Get incidents within a date range."""
        type_value = incident_type.value if incident_type else None
        return await self.incident_repo.get_by_date_range(
            start_date, end_date, type_value
        )

    async def get_incidents_requiring_notification(self) -> List[Incident]:
        """Get incidents requiring external notification."""
        return await self.incident_repo.get_requiring_notification()

    async def update_incident(
        self,
        incident_id: UUID,
        data: IncidentUpdate
    ) -> Optional[Incident]:
        """Update incident details."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            return None

        if incident.status == IncidentStatus.CLOSED.value:
            raise ValueError("Cannot update closed incidents")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == 'incident_type' and value:
                setattr(incident, field, value.value)
                # Check if type change requires notification
                if value.value in NOTIFICATION_REQUIRED_TYPES:
                    incident.external_notification_required = True
            else:
                setattr(incident, field, value)

        return await self.incident_repo.update(incident)

    async def update_status(
        self,
        incident_id: UUID,
        status: IncidentStatus,
        notes: Optional[str] = None
    ) -> Incident:
        """Update incident status with workflow validation."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        # Validate status transition
        current = IncidentStatus(incident.status)
        valid_transitions = {
            IncidentStatus.REPORTED: [IncidentStatus.UNDER_INVESTIGATION, IncidentStatus.RESOLVED],
            IncidentStatus.UNDER_INVESTIGATION: [IncidentStatus.RESOLVED, IncidentStatus.REPORTED],
            IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.UNDER_INVESTIGATION],
            IncidentStatus.CLOSED: []  # Terminal state
        }

        if status not in valid_transitions.get(current, []):
            raise ValueError(
                f"Invalid status transition: {current.value} → {status.value}"
            )

        # Require resolution for RESOLVED status
        if status == IncidentStatus.RESOLVED and not incident.resolution:
            raise ValueError("Resolution is required before marking as resolved")

        incident.status = status.value

        return await self.incident_repo.update(incident)

    async def escalate_severity(
        self,
        incident_id: UUID,
        new_severity: IncidentSeverity,
        reason: str
    ) -> Incident:
        """Escalate incident severity."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        if incident.status == IncidentStatus.CLOSED.value:
            raise ValueError("Cannot escalate closed incidents")

        current_severity = IncidentSeverity(incident.severity)

        # Record escalation in description
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        escalation_note = f"\n[ESCALATED {timestamp}] {current_severity.value} → {new_severity.value}: {reason}"
        incident.description = f"{incident.description}{escalation_note}"

        incident.severity = new_severity.value

        # CRITICAL severity triggers notification requirement
        if new_severity == IncidentSeverity.CRITICAL:
            incident.external_notification_required = True

        return await self.incident_repo.update(incident)

    async def resolve_incident(
        self,
        incident_id: UUID,
        data: IncidentResolve,
        resolved_by: UUID
    ) -> Incident:
        """Resolve an incident with resolution details."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        if incident.status == IncidentStatus.CLOSED.value:
            raise ValueError("Incident is already closed")

        incident.resolution = data.resolution
        incident.resolved_at = datetime.now()
        incident.resolved_by = resolved_by
        incident.status = IncidentStatus.RESOLVED.value

        if data.notes:
            incident.description = f"{incident.description}\n[RESOLUTION NOTES] {data.notes}"

        return await self.incident_repo.update(incident)

    async def close_incident(
        self,
        incident_id: UUID
    ) -> Incident:
        """
        Close an incident.

        REQUIRES: Incident must be in RESOLVED status with a resolution.
        """
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        if incident.status != IncidentStatus.RESOLVED.value:
            raise ValueError("Can only close RESOLVED incidents")

        if not incident.resolution:
            raise ValueError("Resolution is required before closing")

        # Check notification compliance
        if incident.external_notification_required and not incident.external_notified:
            raise ValueError(
                "External notification is required but not completed. "
                "Mark external_notified as true before closing."
            )

        incident.status = IncidentStatus.CLOSED.value

        return await self.incident_repo.update(incident)

    async def mark_external_notified(
        self,
        incident_id: UUID,
        notes: str
    ) -> Incident:
        """Mark external notification as completed."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        incident.external_notified = True
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        incident.description = f"{incident.description}\n[EXTERNAL NOTIFIED {timestamp}] {notes}"

        return await self.incident_repo.update(incident)

    async def delete_incident(self, incident_id: UUID) -> bool:
        """Soft delete an incident."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            return False

        if incident.status == IncidentStatus.CLOSED.value:
            raise ValueError("Cannot delete closed incidents")

        return await self.incident_repo.soft_delete(incident)

    # ========================================================================
    # Involvement Operations
    # ========================================================================

    async def add_involvement(
        self,
        incident_id: UUID,
        data: IncidentInvolvementCreate
    ) -> IncidentInvolvement:
        """Add a person's involvement to an incident."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        if incident.status == IncidentStatus.CLOSED.value:
            raise ValueError("Cannot add involvement to closed incidents")

        involvement = IncidentInvolvement(
            incident_id=incident_id,
            inmate_id=data.inmate_id,
            staff_id=data.staff_id,
            involvement_type=data.involvement_type.value,
            description=data.description,
            injuries=data.injuries,
            disciplinary_action_taken=data.disciplinary_action_taken
        )

        return await self.involvement_repo.create(involvement)

    async def get_involvement(
        self,
        involvement_id: UUID
    ) -> Optional[IncidentInvolvement]:
        """Get involvement by ID."""
        return await self.involvement_repo.get_by_id(involvement_id)

    async def get_incident_involvements(
        self,
        incident_id: UUID
    ) -> List[IncidentInvolvement]:
        """Get all involvements for an incident."""
        return await self.involvement_repo.get_by_incident(incident_id)

    async def get_inmate_involvements(
        self,
        inmate_id: UUID,
        involvement_type: Optional[InvolvementType] = None
    ) -> List[IncidentInvolvement]:
        """Get all involvements for an inmate."""
        type_value = involvement_type.value if involvement_type else None
        return await self.involvement_repo.get_by_inmate(inmate_id, type_value)

    async def update_involvement(
        self,
        involvement_id: UUID,
        data: dict
    ) -> Optional[IncidentInvolvement]:
        """Update involvement record."""
        involvement = await self.involvement_repo.get_by_id(involvement_id)
        if not involvement:
            return None

        for field, value in data.items():
            if value is not None:
                if field == 'involvement_type':
                    setattr(involvement, field, value.value)
                else:
                    setattr(involvement, field, value)

        return await self.involvement_repo.update(involvement)

    async def delete_involvement(self, involvement_id: UUID) -> bool:
        """Delete an involvement record."""
        involvement = await self.involvement_repo.get_by_id(involvement_id)
        if not involvement:
            return False

        return await self.involvement_repo.delete(involvement)

    # ========================================================================
    # Attachment Operations
    # ========================================================================

    async def add_attachment(
        self,
        incident_id: UUID,
        data: IncidentAttachmentCreate,
        uploaded_by: UUID
    ) -> IncidentAttachment:
        """Add an attachment to an incident."""
        incident = await self.incident_repo.get_by_id(incident_id, include_involvements=False)
        if not incident:
            raise ValueError("Incident not found")

        attachment = IncidentAttachment(
            incident_id=incident_id,
            file_name=data.file_name,
            file_type=data.file_type,
            file_path=data.file_path,
            uploaded_at=datetime.now(),
            uploaded_by=uploaded_by,
            description=data.description
        )

        return await self.attachment_repo.create(attachment)

    async def get_attachment(
        self,
        attachment_id: UUID
    ) -> Optional[IncidentAttachment]:
        """Get attachment by ID."""
        return await self.attachment_repo.get_by_id(attachment_id)

    async def get_incident_attachments(
        self,
        incident_id: UUID
    ) -> List[IncidentAttachment]:
        """Get all attachments for an incident."""
        return await self.attachment_repo.get_by_incident(incident_id)

    async def delete_attachment(self, attachment_id: UUID) -> bool:
        """Delete an attachment record."""
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if not attachment:
            return False

        return await self.attachment_repo.delete(attachment)

    # ========================================================================
    # Statistics and Reports
    # ========================================================================

    async def get_inmate_incident_summary(
        self,
        inmate_id: UUID
    ) -> InmateIncidentSummary:
        """Get incident summary for an inmate."""
        involvements = await self.involvement_repo.get_by_inmate(inmate_id)
        type_counts = await self.involvement_repo.count_by_inmate_and_type(inmate_id)

        # Get recent incidents (last 5)
        recent_involvements = involvements[:5]
        recent_incidents = []

        for inv in recent_involvements:
            if inv.incident:
                incident = inv.incident
                recent_incidents.append(IncidentResponse(
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
                ))

        return InmateIncidentSummary(
            inmate_id=inmate_id,
            total_involvements=len(involvements),
            as_victim=type_counts.get(InvolvementType.VICTIM.value, 0),
            as_perpetrator=type_counts.get(InvolvementType.PERPETRATOR.value, 0),
            as_witness=type_counts.get(InvolvementType.WITNESS.value, 0),
            recent_incidents=recent_incidents
        )

    async def get_statistics(self) -> IncidentStatistics:
        """Get overall incident statistics."""
        total = await self.incident_repo.count_total()
        status_counts = await self.incident_repo.count_by_status()
        type_counts = await self.incident_repo.count_by_type()
        severity_counts = await self.incident_repo.count_by_severity()

        # Calculate open incidents
        open_count = (
            status_counts.get(IncidentStatus.REPORTED.value, 0) +
            status_counts.get(IncidentStatus.UNDER_INVESTIGATION.value, 0)
        )

        # Count this month's incidents
        today = date.today()
        this_month = await self.incident_repo.count_for_month(today.year, today.month)

        # Get incidents requiring notification
        requiring_notification = await self.incident_repo.get_requiring_notification()

        # Get incidents with injuries
        with_injuries = await self.incident_repo.count_with_injuries()

        # Average resolution time
        avg_resolution = await self.incident_repo.average_resolution_days()

        by_type = [
            IncidentTypeCount(incident_type=t, count=c)
            for t, c in type_counts.items()
        ]

        by_severity = [
            IncidentSeverityCount(severity=s, count=c)
            for s, c in severity_counts.items()
        ]

        return IncidentStatistics(
            total_incidents=total,
            open_incidents=open_count,
            critical_incidents=severity_counts.get(IncidentSeverity.CRITICAL.value, 0),
            incidents_this_month=this_month,
            incidents_requiring_notification=len(requiring_notification),
            incidents_with_injuries=with_injuries,
            by_type=by_type,
            by_severity=by_severity,
            average_resolution_days=round(avg_resolution, 1) if avg_resolution else None
        )
