"""
BDOCS Incident Management Module - Security incident tracking and investigation.

This module handles all security incidents within correctional facilities:
- Assaults (inmate-on-inmate, inmate-on-staff)
- Contraband discoveries
- Escape attempts
- Medical emergencies
- Deaths in custody
- And other security events

Three core entities:
- Incident: Main incident record with auto-generated number (INC-YYYY-NNNNN)
- IncidentInvolvement: Links incidents to inmates/staff with roles
- IncidentAttachment: Evidence and documentation files

Key features:
- Auto-generated incident numbers
- Severity escalation with notification triggers
- Status workflow enforcement (REPORTED → INVESTIGATION → RESOLVED → CLOSED)
- External notification tracking for critical incidents
- Involvement tracking for multiple parties

CRITICAL: Death and escape incidents automatically require external notification.
"""
from src.modules.incident.models import Incident, IncidentInvolvement, IncidentAttachment
from src.modules.incident.controller import incident_bp, blueprint

__all__ = [
    'Incident',
    'IncidentInvolvement',
    'IncidentAttachment',
    'incident_bp',
    'blueprint'
]
