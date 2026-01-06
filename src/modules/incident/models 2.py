"""
Incident Management Models - Security incident tracking and investigation.

This module handles all security incidents within correctional facilities:
- Assaults (inmate-on-inmate, inmate-on-staff)
- Contraband discoveries
- Escape attempts
- Medical emergencies
- Deaths in custody
- And other security events

Three core entities:
- Incident: Main incident record with auto-generated number
- IncidentInvolvement: Links incidents to inmates/staff with roles
- IncidentAttachment: Evidence and documentation files

CRITICAL: Death and escape incidents require external notification.
"""
from datetime import datetime, date
from typing import Optional, List
import uuid

from sqlalchemy import String, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, SoftDeleteMixin, AuditMixin
from src.common.enums import IncidentType, IncidentSeverity, IncidentStatus, InvolvementType


class Incident(AsyncBase, UUIDMixin, SoftDeleteMixin, AuditMixin):
    """
    Security incident record.

    Incident numbers are auto-generated in format: INC-YYYY-NNNNN
    Example: INC-2026-00042

    Workflow: REPORTED → UNDER_INVESTIGATION → RESOLVED → CLOSED

    CRITICAL incidents (death, escape, serious assault) require
    external notification to police, coroner, or ministry.
    """
    __tablename__ = 'incidents'

    # Auto-generated incident number
    incident_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Format: INC-YYYY-NNNNN"
    )

    # Incident classification
    incident_type: Mapped[str] = mapped_column(
        ENUM(
            'ASSAULT', 'CONTRABAND', 'ESCAPE_ATTEMPT', 'MEDICAL_EMERGENCY',
            'FIRE', 'DISTURBANCE', 'PROPERTY_DAMAGE', 'DEATH',
            'SUICIDE_ATTEMPT', 'DRUG_USE', 'WEAPON', 'OTHER',
            name='incident_type_enum',
            create_type=False
        ),
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        ENUM(
            'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
            name='incident_severity_enum',
            create_type=False
        ),
        nullable=False,
        default=IncidentSeverity.MEDIUM.value
    )

    status: Mapped[str] = mapped_column(
        ENUM(
            'REPORTED', 'UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED',
            name='incident_status_enum',
            create_type=False
        ),
        nullable=False,
        default=IncidentStatus.REPORTED.value
    )

    # When and where
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the incident occurred"
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Location within facility"
    )

    # Reporting
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When incident was reported"
    )

    reported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="Staff member who reported incident"
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed description of incident"
    )

    immediate_actions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Actions taken immediately after incident"
    )

    # Impact assessment
    injuries_reported: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Were any injuries reported?"
    )

    property_damage: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was there property damage?"
    )

    # External notification (critical incidents)
    external_notification_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Does incident require external notification (police, ministry)?"
    )

    external_notified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Have external parties been notified?"
    )

    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="How incident was resolved"
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When incident was resolved"
    )

    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Staff member who resolved incident"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_incidents_number', 'incident_number'),
        Index('ix_incidents_type', 'incident_type'),
        Index('ix_incidents_severity', 'severity'),
        Index('ix_incidents_status', 'status'),
        Index('ix_incidents_occurred', 'occurred_at'),
        Index('ix_incidents_reported_by', 'reported_by'),
        # Partial index for open incidents
        Index(
            'ix_incidents_open',
            'status', 'severity',
            postgresql_where="status IN ('REPORTED', 'UNDER_INVESTIGATION') AND is_deleted = false"
        ),
        # Partial index for critical incidents
        Index(
            'ix_incidents_critical',
            'severity', 'status',
            postgresql_where="severity = 'CRITICAL' AND is_deleted = false"
        ),
    )

    # Relationships
    involvements = relationship(
        'IncidentInvolvement',
        back_populates='incident',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='IncidentInvolvement.involvement_type'
    )
    attachments = relationship(
        'IncidentAttachment',
        back_populates='incident',
        lazy='selectin',
        cascade='all, delete-orphan',
        order_by='IncidentAttachment.uploaded_at.desc()'
    )

    @property
    def is_open(self) -> bool:
        """Check if incident is still open."""
        return self.status in [
            IncidentStatus.REPORTED.value,
            IncidentStatus.UNDER_INVESTIGATION.value
        ]

    @property
    def requires_notification(self) -> bool:
        """Check if external notification is required but not done."""
        return self.external_notification_required and not self.external_notified

    def __repr__(self) -> str:
        return f"<Incident {self.incident_number} ({self.incident_type} - {self.severity})>"


class IncidentInvolvement(AsyncBase, UUIDMixin, AuditMixin):
    """
    Record of person involved in an incident.

    Can link to either an inmate or a staff member (or neither for
    external persons like visitors).

    No soft delete - involvement records are permanent for legal purposes.
    """
    __tablename__ = 'incident_involvements'

    # Foreign key to incident
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('incidents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Person involved (one of these should be set)
    inmate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
        comment="Inmate involved (if applicable)"
    )

    staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
        comment="Staff member involved (if applicable)"
    )

    # Role in incident
    involvement_type: Mapped[str] = mapped_column(
        ENUM(
            'VICTIM', 'PERPETRATOR', 'WITNESS', 'RESPONDER', 'OTHER',
            name='involvement_type_enum',
            create_type=False
        ),
        nullable=False
    )

    # Details
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of involvement"
    )

    injuries: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of any injuries sustained"
    )

    disciplinary_action_taken: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was disciplinary action taken against this person?"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_incident_involvements_incident', 'incident_id'),
        Index('ix_incident_involvements_inmate', 'inmate_id'),
        Index('ix_incident_involvements_staff', 'staff_id'),
        Index('ix_incident_involvements_type', 'involvement_type'),
    )

    # Relationships
    incident = relationship('Incident', back_populates='involvements', lazy='selectin')
    inmate = relationship('Inmate', back_populates='incident_involvements', lazy='selectin')

    def __repr__(self) -> str:
        person = f"Inmate {self.inmate_id}" if self.inmate_id else f"Staff {self.staff_id}"
        return f"<IncidentInvolvement {person} - {self.involvement_type}>"


class IncidentAttachment(AsyncBase, UUIDMixin, AuditMixin):
    """
    File attachment for incident documentation.

    Stores evidence, photos, reports, and other documentation
    related to an incident.

    No soft delete - attachments are permanent for legal purposes.
    """
    __tablename__ = 'incident_attachments'

    # Foreign key to incident
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('incidents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # File information
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original file name"
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="MIME type or file extension"
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path or URL"
    )

    # Upload information
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When file was uploaded"
    )

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="Staff member who uploaded file"
    )

    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of attachment"
    )

    # Table indexes
    __table_args__ = (
        Index('ix_incident_attachments_incident', 'incident_id'),
        Index('ix_incident_attachments_uploaded', 'uploaded_at'),
    )

    # Relationships
    incident = relationship('Incident', back_populates='attachments', lazy='selectin')

    def __repr__(self) -> str:
        return f"<IncidentAttachment {self.file_name}>"
