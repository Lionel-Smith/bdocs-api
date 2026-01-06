"""
Incident Management Repository - Data access for incident operations.

Three repository classes:
- IncidentRepository: Main incident CRUD and queries
- IncidentInvolvementRepository: Person involvement records
- IncidentAttachmentRepository: File attachment management

Key queries:
- get_open_incidents(): All non-closed incidents
- get_critical_incidents(): CRITICAL severity incidents
- get_by_type(): Filter by incident type
- get_by_inmate(): All incidents involving an inmate
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.incident.models import (
    Incident,
    IncidentInvolvement,
    IncidentAttachment
)
from src.common.enums import IncidentType, IncidentSeverity, IncidentStatus, InvolvementType


class IncidentRepository:
    """Repository for incident operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        """Create a new incident."""
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def get_by_id(
        self,
        incident_id: UUID,
        include_involvements: bool = True,
        include_attachments: bool = False
    ) -> Optional[Incident]:
        """Get incident by ID with optional related data."""
        query = select(Incident).where(
            Incident.id == incident_id,
            Incident.is_deleted == False
        )

        if include_involvements:
            query = query.options(selectinload(Incident.involvements))

        if include_attachments:
            query = query.options(selectinload(Incident.attachments))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, incident_number: str) -> Optional[Incident]:
        """Get incident by incident number."""
        query = select(Incident).where(
            Incident.incident_number == incident_number,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements),
            selectinload(Incident.attachments)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Incident]:
        """Get all incidents with pagination."""
        query = select(Incident).where(
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(
            Incident.occurred_at.desc()
        ).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        incident_type: str,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents by type."""
        query = select(Incident).where(
            Incident.incident_type == incident_type,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(
            Incident.occurred_at.desc()
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_severity(
        self,
        severity: str,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents by severity."""
        query = select(Incident).where(
            Incident.severity == severity,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(
            Incident.occurred_at.desc()
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents by status."""
        query = select(Incident).where(
            Incident.status == status,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(
            Incident.occurred_at.desc()
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_incidents(self) -> List[Incident]:
        """Get all open (non-closed) incidents."""
        query = select(Incident).where(
            Incident.status.in_([
                IncidentStatus.REPORTED.value,
                IncidentStatus.UNDER_INVESTIGATION.value
            ]),
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(
            Incident.severity.desc(),
            Incident.occurred_at.desc()
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_critical_incidents(
        self,
        open_only: bool = True
    ) -> List[Incident]:
        """Get critical severity incidents."""
        query = select(Incident).where(
            Incident.severity == IncidentSeverity.CRITICAL.value,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        )

        if open_only:
            query = query.where(
                Incident.status.in_([
                    IncidentStatus.REPORTED.value,
                    IncidentStatus.UNDER_INVESTIGATION.value
                ])
            )

        query = query.order_by(Incident.occurred_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        incident_type: Optional[str] = None
    ) -> List[Incident]:
        """Get incidents within a date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        query = select(Incident).where(
            Incident.occurred_at >= start_datetime,
            Incident.occurred_at <= end_datetime,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        )

        if incident_type:
            query = query.where(Incident.incident_type == incident_type)

        query = query.order_by(Incident.occurred_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_requiring_notification(self) -> List[Incident]:
        """Get incidents requiring external notification that haven't been notified."""
        query = select(Incident).where(
            Incident.external_notification_required == True,
            Incident.external_notified == False,
            Incident.is_deleted == False
        ).options(
            selectinload(Incident.involvements)
        ).order_by(Incident.occurred_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, incident: Incident) -> Incident:
        """Update an incident."""
        await self.session.flush()
        return incident

    async def soft_delete(self, incident: Incident) -> bool:
        """Soft delete an incident."""
        incident.is_deleted = True
        incident.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def get_next_incident_number(self, year: int) -> str:
        """Generate the next incident number for a given year."""
        # Find the highest incident number for this year
        pattern = f"INC-{year}-%"
        query = select(func.max(Incident.incident_number)).where(
            Incident.incident_number.like(pattern)
        )

        result = await self.session.execute(query)
        max_number = result.scalar()

        if max_number:
            # Extract the sequence number and increment
            current_seq = int(max_number.split('-')[2])
            next_seq = current_seq + 1
        else:
            next_seq = 1

        return f"INC-{year}-{next_seq:05d}"

    async def count_total(self) -> int:
        """Count total incidents."""
        query = select(func.count(Incident.id)).where(
            Incident.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_by_status(self) -> dict:
        """Count incidents by status."""
        query = select(
            Incident.status,
            func.count(Incident.id)
        ).where(
            Incident.is_deleted == False
        ).group_by(Incident.status)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_type(self) -> dict:
        """Count incidents by type."""
        query = select(
            Incident.incident_type,
            func.count(Incident.id)
        ).where(
            Incident.is_deleted == False
        ).group_by(Incident.incident_type)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_severity(self) -> dict:
        """Count incidents by severity."""
        query = select(
            Incident.severity,
            func.count(Incident.id)
        ).where(
            Incident.is_deleted == False
        ).group_by(Incident.severity)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_for_month(self, year: int, month: int) -> int:
        """Count incidents for a specific month."""
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        query = select(func.count(Incident.id)).where(
            Incident.occurred_at >= start_datetime,
            Incident.occurred_at <= end_datetime,
            Incident.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_with_injuries(self) -> int:
        """Count incidents with injuries reported."""
        query = select(func.count(Incident.id)).where(
            Incident.injuries_reported == True,
            Incident.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def average_resolution_days(self) -> Optional[float]:
        """Calculate average days to resolve incidents."""
        query = select(
            func.avg(
                func.extract('epoch', Incident.resolved_at - Incident.occurred_at) / 86400
            )
        ).where(
            Incident.resolved_at != None,
            Incident.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar()


class IncidentInvolvementRepository:
    """Repository for incident involvement operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, involvement: IncidentInvolvement) -> IncidentInvolvement:
        """Create an involvement record."""
        self.session.add(involvement)
        await self.session.flush()
        return involvement

    async def get_by_id(self, involvement_id: UUID) -> Optional[IncidentInvolvement]:
        """Get involvement by ID."""
        query = select(IncidentInvolvement).where(
            IncidentInvolvement.id == involvement_id
        ).options(selectinload(IncidentInvolvement.inmate))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_incident(self, incident_id: UUID) -> List[IncidentInvolvement]:
        """Get all involvements for an incident."""
        query = select(IncidentInvolvement).where(
            IncidentInvolvement.incident_id == incident_id
        ).options(
            selectinload(IncidentInvolvement.inmate)
        ).order_by(IncidentInvolvement.involvement_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        involvement_type: Optional[str] = None
    ) -> List[IncidentInvolvement]:
        """Get all involvements for an inmate."""
        query = select(IncidentInvolvement).where(
            IncidentInvolvement.inmate_id == inmate_id
        ).options(
            selectinload(IncidentInvolvement.incident)
        )

        if involvement_type:
            query = query.where(IncidentInvolvement.involvement_type == involvement_type)

        query = query.order_by(IncidentInvolvement.inserted_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_staff(
        self,
        staff_id: UUID,
        involvement_type: Optional[str] = None
    ) -> List[IncidentInvolvement]:
        """Get all involvements for a staff member."""
        query = select(IncidentInvolvement).where(
            IncidentInvolvement.staff_id == staff_id
        ).options(
            selectinload(IncidentInvolvement.incident)
        )

        if involvement_type:
            query = query.where(IncidentInvolvement.involvement_type == involvement_type)

        query = query.order_by(IncidentInvolvement.inserted_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, involvement: IncidentInvolvement) -> IncidentInvolvement:
        """Update an involvement record."""
        await self.session.flush()
        return involvement

    async def delete(self, involvement: IncidentInvolvement) -> bool:
        """Delete an involvement record (hard delete)."""
        await self.session.delete(involvement)
        await self.session.flush()
        return True

    async def count_by_inmate_and_type(self, inmate_id: UUID) -> dict:
        """Count involvements by type for an inmate."""
        query = select(
            IncidentInvolvement.involvement_type,
            func.count(IncidentInvolvement.id)
        ).where(
            IncidentInvolvement.inmate_id == inmate_id
        ).group_by(IncidentInvolvement.involvement_type)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}


class IncidentAttachmentRepository:
    """Repository for incident attachment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attachment: IncidentAttachment) -> IncidentAttachment:
        """Create an attachment record."""
        self.session.add(attachment)
        await self.session.flush()
        return attachment

    async def get_by_id(self, attachment_id: UUID) -> Optional[IncidentAttachment]:
        """Get attachment by ID."""
        query = select(IncidentAttachment).where(
            IncidentAttachment.id == attachment_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_incident(self, incident_id: UUID) -> List[IncidentAttachment]:
        """Get all attachments for an incident."""
        query = select(IncidentAttachment).where(
            IncidentAttachment.incident_id == incident_id
        ).order_by(IncidentAttachment.uploaded_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, attachment: IncidentAttachment) -> bool:
        """Delete an attachment record (hard delete)."""
        await self.session.delete(attachment)
        await self.session.flush()
        return True

    async def count_by_incident(self, incident_id: UUID) -> int:
        """Count attachments for an incident."""
        query = select(func.count(IncidentAttachment.id)).where(
            IncidentAttachment.incident_id == incident_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
