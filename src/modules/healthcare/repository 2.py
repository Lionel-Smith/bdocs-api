"""
Healthcare Repository - Data access layer for healthcare management.

HIPAA NOTE: All database operations involve Protected Health Information.
Ensure calling code enforces role-based access control.

Handles database operations for MedicalRecord, MedicalEncounter,
and MedicationAdministration entities.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.healthcare.models import (
    MedicalRecord, MedicalEncounter, MedicationAdministration
)
from src.common.enums import (
    BloodType, EncounterType, ProviderType,
    RouteType, MedAdminStatus
)


class MedicalRecordRepository:
    """Repository for MedicalRecord operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: MedicalRecord) -> MedicalRecord:
        """Create a new medical record."""
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_by_id(self, record_id: UUID) -> Optional[MedicalRecord]:
        """Get medical record by ID."""
        result = await self.session.execute(
            select(MedicalRecord)
            .where(MedicalRecord.id == record_id)
            .options(
                selectinload(MedicalRecord.inmate),
                selectinload(MedicalRecord.creator)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_inmate(self, inmate_id: UUID) -> Optional[MedicalRecord]:
        """Get medical record by inmate ID (one-to-one)."""
        result = await self.session.execute(
            select(MedicalRecord)
            .where(MedicalRecord.inmate_id == inmate_id)
            .options(
                selectinload(MedicalRecord.inmate),
                selectinload(MedicalRecord.creator)
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        mental_health_flag: Optional[bool] = None,
        suicide_watch: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicalRecord]:
        """Get all medical records with optional filters."""
        query = select(MedicalRecord)

        if mental_health_flag is not None:
            query = query.where(MedicalRecord.mental_health_flag == mental_health_flag)
        if suicide_watch is not None:
            query = query.where(MedicalRecord.suicide_watch == suicide_watch)

        query = query.options(selectinload(MedicalRecord.inmate))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_suicide_watch_inmates(self) -> List[MedicalRecord]:
        """Get all inmates on suicide watch."""
        result = await self.session.execute(
            select(MedicalRecord)
            .where(MedicalRecord.suicide_watch == True)
            .options(selectinload(MedicalRecord.inmate))
        )
        return list(result.scalars().all())

    async def get_physicals_due(self, within_days: int = 30) -> List[MedicalRecord]:
        """Get records with physicals due within specified days."""
        cutoff = date.today() + timedelta(days=within_days)

        result = await self.session.execute(
            select(MedicalRecord)
            .where(and_(
                MedicalRecord.next_physical_due.isnot(None),
                MedicalRecord.next_physical_due <= cutoff
            ))
            .options(selectinload(MedicalRecord.inmate))
            .order_by(MedicalRecord.next_physical_due)
        )
        return list(result.scalars().all())

    async def update(self, record: MedicalRecord) -> MedicalRecord:
        """Update a medical record."""
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def count(
        self,
        mental_health_flag: Optional[bool] = None,
        suicide_watch: Optional[bool] = None,
        has_allergies: Optional[bool] = None,
        has_chronic_conditions: Optional[bool] = None
    ) -> int:
        """Count medical records with optional filters."""
        query = select(func.count(MedicalRecord.id))

        if mental_health_flag is not None:
            query = query.where(MedicalRecord.mental_health_flag == mental_health_flag)
        if suicide_watch is not None:
            query = query.where(MedicalRecord.suicide_watch == suicide_watch)

        result = await self.session.execute(query)
        return result.scalar() or 0


class MedicalEncounterRepository:
    """Repository for MedicalEncounter operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, encounter: MedicalEncounter) -> MedicalEncounter:
        """Create a new medical encounter."""
        self.session.add(encounter)
        await self.session.flush()
        await self.session.refresh(encounter)
        return encounter

    async def get_by_id(self, encounter_id: UUID) -> Optional[MedicalEncounter]:
        """Get encounter by ID."""
        result = await self.session.execute(
            select(MedicalEncounter)
            .where(MedicalEncounter.id == encounter_id)
            .options(
                selectinload(MedicalEncounter.inmate),
                selectinload(MedicalEncounter.creator)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        encounter_type: Optional[EncounterType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicalEncounter]:
        """Get encounters for an inmate."""
        query = select(MedicalEncounter).where(MedicalEncounter.inmate_id == inmate_id)

        if encounter_type:
            query = query.where(MedicalEncounter.encounter_type == encounter_type)

        query = query.order_by(MedicalEncounter.encounter_date.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        encounter_type: Optional[EncounterType] = None
    ) -> List[MedicalEncounter]:
        """Get encounters within a date range."""
        query = select(MedicalEncounter).where(and_(
            MedicalEncounter.encounter_date >= start_date,
            MedicalEncounter.encounter_date <= end_date
        ))

        if encounter_type:
            query = query.where(MedicalEncounter.encounter_type == encounter_type)

        query = query.options(selectinload(MedicalEncounter.inmate))
        query = query.order_by(MedicalEncounter.encounter_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_follow_ups_due(self, within_days: int = 7) -> List[MedicalEncounter]:
        """Get encounters with follow-ups due within specified days."""
        today = date.today()
        cutoff = today + timedelta(days=within_days)

        result = await self.session.execute(
            select(MedicalEncounter)
            .where(and_(
                MedicalEncounter.follow_up_required == True,
                MedicalEncounter.follow_up_date.isnot(None),
                MedicalEncounter.follow_up_date >= today,
                MedicalEncounter.follow_up_date <= cutoff
            ))
            .options(selectinload(MedicalEncounter.inmate))
            .order_by(MedicalEncounter.follow_up_date)
        )
        return list(result.scalars().all())

    async def get_latest_by_inmate(
        self,
        inmate_id: UUID,
        encounter_type: Optional[EncounterType] = None
    ) -> Optional[MedicalEncounter]:
        """Get most recent encounter for an inmate."""
        query = select(MedicalEncounter).where(MedicalEncounter.inmate_id == inmate_id)

        if encounter_type:
            query = query.where(MedicalEncounter.encounter_type == encounter_type)

        query = query.order_by(MedicalEncounter.encounter_date.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, encounter: MedicalEncounter) -> MedicalEncounter:
        """Update an encounter."""
        await self.session.flush()
        await self.session.refresh(encounter)
        return encounter

    async def count_by_date(
        self,
        encounter_date: date,
        encounter_type: Optional[EncounterType] = None
    ) -> int:
        """Count encounters for a specific date."""
        start = datetime.combine(encounter_date, time.min)
        end = datetime.combine(encounter_date, time.max)

        query = select(func.count(MedicalEncounter.id)).where(and_(
            MedicalEncounter.encounter_date >= start,
            MedicalEncounter.encounter_date <= end
        ))

        if encounter_type:
            query = query.where(MedicalEncounter.encounter_type == encounter_type)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_external_referrals(self, encounter_date: date) -> int:
        """Count external referrals for a date."""
        start = datetime.combine(encounter_date, time.min)
        end = datetime.combine(encounter_date, time.max)

        result = await self.session.execute(
            select(func.count(MedicalEncounter.id))
            .where(and_(
                MedicalEncounter.encounter_date >= start,
                MedicalEncounter.encounter_date <= end,
                MedicalEncounter.referred_external == True
            ))
        )
        return result.scalar() or 0


class MedicationAdministrationRepository:
    """Repository for MedicationAdministration operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, med_admin: MedicationAdministration) -> MedicationAdministration:
        """Create a new medication administration record."""
        self.session.add(med_admin)
        await self.session.flush()
        await self.session.refresh(med_admin)
        return med_admin

    async def get_by_id(self, admin_id: UUID) -> Optional[MedicationAdministration]:
        """Get medication administration by ID."""
        result = await self.session.execute(
            select(MedicationAdministration)
            .where(MedicationAdministration.id == admin_id)
            .options(
                selectinload(MedicationAdministration.inmate),
                selectinload(MedicationAdministration.administrator),
                selectinload(MedicationAdministration.refusal_witness)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        status: Optional[MedAdminStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicationAdministration]:
        """Get medication administrations for an inmate."""
        query = select(MedicationAdministration).where(
            MedicationAdministration.inmate_id == inmate_id
        )

        if status:
            query = query.where(MedicationAdministration.status == status)

        query = query.order_by(MedicationAdministration.scheduled_time.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        within_minutes: int = 60
    ) -> List[MedicationAdministration]:
        """Get medications due within specified minutes."""
        now = datetime.utcnow()
        cutoff = now + timedelta(minutes=within_minutes)

        result = await self.session.execute(
            select(MedicationAdministration)
            .where(and_(
                MedicationAdministration.status == MedAdminStatus.SCHEDULED,
                MedicationAdministration.scheduled_time <= cutoff
            ))
            .options(selectinload(MedicationAdministration.inmate))
            .order_by(MedicationAdministration.scheduled_time)
        )
        return list(result.scalars().all())

    async def get_overdue(self) -> List[MedicationAdministration]:
        """Get overdue medications."""
        now = datetime.utcnow()

        result = await self.session.execute(
            select(MedicationAdministration)
            .where(and_(
                MedicationAdministration.status == MedAdminStatus.SCHEDULED,
                MedicationAdministration.scheduled_time < now
            ))
            .options(selectinload(MedicationAdministration.inmate))
            .order_by(MedicationAdministration.scheduled_time)
        )
        return list(result.scalars().all())

    async def update(self, med_admin: MedicationAdministration) -> MedicationAdministration:
        """Update a medication administration record."""
        await self.session.flush()
        await self.session.refresh(med_admin)
        return med_admin

    async def count_by_status(self, admin_date: date) -> dict:
        """Get medication counts by status for a date."""
        start = datetime.combine(admin_date, time.min)
        end = datetime.combine(admin_date, time.max)

        result = await self.session.execute(
            select(MedicationAdministration.status, func.count(MedicationAdministration.id))
            .where(and_(
                MedicationAdministration.scheduled_time >= start,
                MedicationAdministration.scheduled_time <= end
            ))
            .group_by(MedicationAdministration.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def count_scheduled_today(self, today: date) -> int:
        """Count medications scheduled for today."""
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        result = await self.session.execute(
            select(func.count(MedicationAdministration.id))
            .where(and_(
                MedicationAdministration.scheduled_time >= start,
                MedicationAdministration.scheduled_time <= end
            ))
        )
        return result.scalar() or 0
