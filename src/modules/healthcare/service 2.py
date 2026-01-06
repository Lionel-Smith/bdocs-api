"""
Healthcare Service - Business logic for healthcare management.

HIPAA NOTE: All operations involve Protected Health Information (PHI).
Ensure role-based access control is enforced before calling these methods.

Handles medical records, encounters, and medication administration.
Key features:
- Intake screening on admission
- Medication scheduling and administration
- Suicide watch monitoring
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.healthcare.models import (
    MedicalRecord, MedicalEncounter, MedicationAdministration
)
from src.modules.healthcare.repository import (
    MedicalRecordRepository, MedicalEncounterRepository,
    MedicationAdministrationRepository
)
from src.modules.healthcare.dtos import (
    MedicalRecordCreateDTO, MedicalRecordUpdateDTO, SuicideWatchUpdateDTO,
    EncounterCreateDTO, MedicationScheduleDTO, MedicationAdministerDTO,
    MedicationRefuseDTO, SuicideWatchInmateDTO, MedicationDueDTO,
    HealthcareStatisticsDTO
)
from src.common.enums import (
    BloodType, EncounterType, ProviderType,
    RouteType, MedAdminStatus
)


class HealthcareService:
    """Service for healthcare management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.record_repo = MedicalRecordRepository(session)
        self.encounter_repo = MedicalEncounterRepository(session)
        self.med_admin_repo = MedicationAdministrationRepository(session)

    # =========================================================================
    # Medical Record Operations
    # =========================================================================

    async def create_intake_screening(
        self,
        data: MedicalRecordCreateDTO,
        created_by: UUID
    ) -> MedicalRecord:
        """
        Create initial medical record during intake screening.

        Called when a new inmate is admitted. This is a mandatory
        process that must occur within 24 hours of admission.

        Args:
            data: Medical record data from intake screening
            created_by: ID of medical staff performing screening

        Returns:
            Created MedicalRecord entity
        """
        # Convert nested DTOs to dicts for JSONB storage
        allergies = [a.model_dump() for a in data.allergies] if data.allergies else []
        chronic_conditions = [c.model_dump() for c in data.chronic_conditions] if data.chronic_conditions else []
        current_medications = [m.model_dump() for m in data.current_medications] if data.current_medications else []
        dietary_restrictions = [d.model_dump() for d in data.dietary_restrictions] if data.dietary_restrictions else []

        record = MedicalRecord(
            id=uuid4(),
            inmate_id=data.inmate_id,
            blood_type=data.blood_type,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            current_medications=current_medications,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            last_physical_date=date.today(),  # Intake screening counts as physical
            next_physical_due=date.today() + timedelta(days=365),  # Annual physical
            mental_health_flag=data.mental_health_flag,
            suicide_watch=data.suicide_watch,
            dietary_restrictions=dietary_restrictions,
            disability_accommodations=data.disability_accommodations,
            created_by=created_by
        )

        return await self.record_repo.create(record)

    async def get_medical_record(self, record_id: UUID) -> Optional[MedicalRecord]:
        """Get medical record by ID."""
        return await self.record_repo.get_by_id(record_id)

    async def get_inmate_medical_record(self, inmate_id: UUID) -> Optional[MedicalRecord]:
        """Get medical record for a specific inmate."""
        return await self.record_repo.get_by_inmate(inmate_id)

    async def get_all_medical_records(
        self,
        mental_health_flag: Optional[bool] = None,
        suicide_watch: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicalRecord]:
        """Get all medical records with optional filters."""
        return await self.record_repo.get_all(
            mental_health_flag=mental_health_flag,
            suicide_watch=suicide_watch,
            skip=skip,
            limit=limit
        )

    async def update_medical_record(
        self,
        inmate_id: UUID,
        data: MedicalRecordUpdateDTO
    ) -> Optional[MedicalRecord]:
        """Update an inmate's medical record."""
        record = await self.record_repo.get_by_inmate(inmate_id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Convert nested DTOs to dicts
        if 'allergies' in update_data and update_data['allergies']:
            update_data['allergies'] = [a.model_dump() if hasattr(a, 'model_dump') else a
                                        for a in update_data['allergies']]
        if 'chronic_conditions' in update_data and update_data['chronic_conditions']:
            update_data['chronic_conditions'] = [c.model_dump() if hasattr(c, 'model_dump') else c
                                                  for c in update_data['chronic_conditions']]
        if 'current_medications' in update_data and update_data['current_medications']:
            update_data['current_medications'] = [m.model_dump() if hasattr(m, 'model_dump') else m
                                                   for m in update_data['current_medications']]
        if 'dietary_restrictions' in update_data and update_data['dietary_restrictions']:
            update_data['dietary_restrictions'] = [d.model_dump() if hasattr(d, 'model_dump') else d
                                                    for d in update_data['dietary_restrictions']]

        for field, value in update_data.items():
            setattr(record, field, value)

        return await self.record_repo.update(record)

    async def update_suicide_watch(
        self,
        inmate_id: UUID,
        data: SuicideWatchUpdateDTO,
        updated_by: UUID
    ) -> Optional[MedicalRecord]:
        """
        Update suicide watch status - CRITICAL operation.

        This is a high-priority flag that affects inmate monitoring.
        Changes should be documented with reason.

        Args:
            inmate_id: Inmate to update
            data: Suicide watch status and reason
            updated_by: Medical staff making the change

        Returns:
            Updated MedicalRecord or None if not found
        """
        record = await self.record_repo.get_by_inmate(inmate_id)
        if not record:
            return None

        record.suicide_watch = data.suicide_watch

        # Log the change reason in a note (would typically create an encounter)
        # This is a critical safety change

        return await self.record_repo.update(record)

    async def get_suicide_watch_inmates(self) -> List[SuicideWatchInmateDTO]:
        """
        Get all inmates currently on suicide watch.

        Critical safety list for monitoring staff.

        Returns:
            List of SuicideWatchInmateDTO with inmate and watch details
        """
        records = await self.record_repo.get_suicide_watch_inmates()

        result = []
        for record in records:
            # Get latest mental health encounter
            latest_encounter = await self.encounter_repo.get_latest_by_inmate(
                record.inmate_id,
                EncounterType.MENTAL_HEALTH
            )

            result.append(SuicideWatchInmateDTO(
                inmate_id=record.inmate_id,
                inmate_name=record.inmate.full_name if record.inmate else "Unknown",
                inmate_booking_number=record.inmate.booking_number if record.inmate else "",
                housing_unit=None,  # Would need housing module integration
                suicide_watch_since=record.updated_date,
                mental_health_flag=record.mental_health_flag,
                last_encounter_date=latest_encounter.encounter_date if latest_encounter else None,
                last_encounter_type=latest_encounter.encounter_type if latest_encounter else None
            ))

        return result

    # =========================================================================
    # Medical Encounter Operations
    # =========================================================================

    async def create_encounter(
        self,
        data: EncounterCreateDTO,
        created_by: UUID
    ) -> MedicalEncounter:
        """
        Create a medical encounter record.

        Args:
            data: Encounter data
            created_by: ID of staff creating record

        Returns:
            Created MedicalEncounter entity
        """
        # Convert vitals DTO to dict
        vitals = data.vitals.model_dump() if data.vitals else None

        # Convert medications to dicts
        medications = [m.model_dump() for m in data.medications_prescribed] if data.medications_prescribed else []

        encounter = MedicalEncounter(
            id=uuid4(),
            inmate_id=data.inmate_id,
            encounter_date=datetime.utcnow(),
            encounter_type=data.encounter_type,
            chief_complaint=data.chief_complaint,
            vitals=vitals,
            diagnosis=data.diagnosis,
            treatment=data.treatment,
            medications_prescribed=medications,
            follow_up_required=data.follow_up_required,
            follow_up_date=data.follow_up_date,
            provider_name=data.provider_name,
            provider_type=data.provider_type,
            location=data.location,
            referred_external=data.referred_external,
            external_facility=data.external_facility,
            notes=data.notes,
            created_by=created_by
        )

        return await self.encounter_repo.create(encounter)

    async def get_encounter(self, encounter_id: UUID) -> Optional[MedicalEncounter]:
        """Get encounter by ID."""
        return await self.encounter_repo.get_by_id(encounter_id)

    async def get_inmate_encounters(
        self,
        inmate_id: UUID,
        encounter_type: Optional[EncounterType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicalEncounter]:
        """Get encounters for an inmate."""
        return await self.encounter_repo.get_by_inmate(
            inmate_id=inmate_id,
            encounter_type=encounter_type,
            skip=skip,
            limit=limit
        )

    async def get_encounters_by_date(
        self,
        encounter_date: date,
        encounter_type: Optional[EncounterType] = None
    ) -> List[MedicalEncounter]:
        """Get all encounters for a specific date."""
        start = datetime.combine(encounter_date, time.min)
        end = datetime.combine(encounter_date, time.max)

        return await self.encounter_repo.get_by_date_range(
            start_date=start,
            end_date=end,
            encounter_type=encounter_type
        )

    # =========================================================================
    # Medication Administration Operations
    # =========================================================================

    async def schedule_medication(
        self,
        data: MedicationScheduleDTO
    ) -> MedicationAdministration:
        """
        Schedule a medication for administration.

        Args:
            data: Medication scheduling data

        Returns:
            Created MedicationAdministration entity
        """
        med_admin = MedicationAdministration(
            id=uuid4(),
            inmate_id=data.inmate_id,
            medication_name=data.medication_name,
            dosage=data.dosage,
            route=data.route,
            scheduled_time=data.scheduled_time,
            status=MedAdminStatus.SCHEDULED,
            notes=data.notes
        )

        return await self.med_admin_repo.create(med_admin)

    async def get_medication_admin(self, admin_id: UUID) -> Optional[MedicationAdministration]:
        """Get medication administration by ID."""
        return await self.med_admin_repo.get_by_id(admin_id)

    async def get_inmate_medications(
        self,
        inmate_id: UUID,
        status: Optional[MedAdminStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicationAdministration]:
        """Get medication administrations for an inmate."""
        return await self.med_admin_repo.get_by_inmate(
            inmate_id=inmate_id,
            status=status,
            skip=skip,
            limit=limit
        )

    async def get_upcoming_medications(
        self,
        within_minutes: int = 60
    ) -> List[MedicationDueDTO]:
        """
        Get medications due within specified minutes.

        Used by medication cart rounds.

        Args:
            within_minutes: Lookahead window (default 60)

        Returns:
            List of MedicationDueDTO sorted by scheduled time
        """
        med_admins = await self.med_admin_repo.get_upcoming(within_minutes)
        now = datetime.utcnow()

        result = []
        for med in med_admins:
            minutes_until = int((med.scheduled_time - now).total_seconds() / 60)

            result.append(MedicationDueDTO(
                id=med.id,
                inmate_id=med.inmate_id,
                inmate_name=med.inmate.full_name if med.inmate else "Unknown",
                inmate_booking_number=med.inmate.booking_number if med.inmate else "",
                medication_name=med.medication_name,
                dosage=med.dosage,
                route=med.route,
                scheduled_time=med.scheduled_time,
                minutes_until_due=minutes_until,
                is_overdue=minutes_until < 0
            ))

        return result

    async def administer_medication(
        self,
        admin_id: UUID,
        data: MedicationAdministerDTO,
        administered_by: UUID
    ) -> Optional[MedicationAdministration]:
        """
        Record medication administration.

        Args:
            admin_id: Medication administration record ID
            data: Administration notes
            administered_by: Staff administering medication

        Returns:
            Updated MedicationAdministration or None if not found
        """
        med_admin = await self.med_admin_repo.get_by_id(admin_id)
        if not med_admin:
            return None

        if med_admin.status != MedAdminStatus.SCHEDULED:
            raise ValueError(f"Cannot administer medication with status {med_admin.status.value}")

        med_admin.status = MedAdminStatus.ADMINISTERED
        med_admin.administered_time = datetime.utcnow()
        med_admin.administered_by = administered_by

        if data.notes:
            existing_notes = med_admin.notes or ""
            med_admin.notes = f"{existing_notes}\nAdministered: {data.notes}".strip()

        return await self.med_admin_repo.update(med_admin)

    async def refuse_medication(
        self,
        admin_id: UUID,
        data: MedicationRefuseDTO,
        recorded_by: UUID
    ) -> Optional[MedicationAdministration]:
        """
        Record medication refusal.

        IMPORTANT: Refusals MUST have a witness for legal protection.

        Args:
            admin_id: Medication administration record ID
            data: Refusal data including witness
            recorded_by: Staff recording refusal

        Returns:
            Updated MedicationAdministration or None if not found
        """
        med_admin = await self.med_admin_repo.get_by_id(admin_id)
        if not med_admin:
            return None

        if med_admin.status != MedAdminStatus.SCHEDULED:
            raise ValueError(f"Cannot refuse medication with status {med_admin.status.value}")

        # Witness is required for refusals
        if not data.refusal_witnessed_by:
            raise ValueError("Refusal must have a witness")

        med_admin.status = MedAdminStatus.REFUSED
        med_admin.administered_time = datetime.utcnow()
        med_admin.administered_by = recorded_by
        med_admin.refusal_witnessed_by = data.refusal_witnessed_by

        if data.notes:
            existing_notes = med_admin.notes or ""
            med_admin.notes = f"{existing_notes}\nRefused: {data.notes}".strip()

        return await self.med_admin_repo.update(med_admin)

    async def mark_medication_missed(
        self,
        admin_id: UUID,
        reason: str
    ) -> Optional[MedicationAdministration]:
        """Mark a medication as missed."""
        med_admin = await self.med_admin_repo.get_by_id(admin_id)
        if not med_admin:
            return None

        med_admin.status = MedAdminStatus.MISSED
        med_admin.administered_time = datetime.utcnow()

        existing_notes = med_admin.notes or ""
        med_admin.notes = f"{existing_notes}\nMissed: {reason}".strip()

        return await self.med_admin_repo.update(med_admin)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_statistics(self) -> HealthcareStatisticsDTO:
        """
        Get comprehensive healthcare statistics.

        Returns:
            HealthcareStatisticsDTO with counts and metrics
        """
        today = date.today()

        # Medical record counts
        total_records = await self.record_repo.count()
        mental_health = await self.record_repo.count(mental_health_flag=True)
        suicide_watch = await self.record_repo.count(suicide_watch=True)

        # We'd need additional queries for allergy/chronic condition counts
        # Simplified for now
        with_allergies = 0
        with_chronic = 0

        # Encounter counts for today
        encounters_today = await self.encounter_repo.count_by_date(today)
        external_referrals = await self.encounter_repo.count_external_referrals(today)

        # Get encounter type breakdown
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        encounters = await self.encounter_repo.get_by_date_range(start, end)
        by_type = {}
        for enc in encounters:
            type_key = enc.encounter_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        # Medication counts
        med_counts = await self.med_admin_repo.count_by_status(today)
        meds_scheduled = await self.med_admin_repo.count_scheduled_today(today)
        meds_administered = med_counts.get(MedAdminStatus.ADMINISTERED.value, 0)
        meds_refused = med_counts.get(MedAdminStatus.REFUSED.value, 0)
        meds_missed = med_counts.get(MedAdminStatus.MISSED.value, 0)

        # Upcoming counts
        follow_ups = await self.encounter_repo.get_follow_ups_due(7)
        physicals = await self.record_repo.get_physicals_due(30)

        return HealthcareStatisticsDTO(
            total_medical_records=total_records,
            inmates_with_allergies=with_allergies,
            inmates_with_chronic_conditions=with_chronic,
            mental_health_flagged=mental_health,
            on_suicide_watch=suicide_watch,
            encounters_today=encounters_today,
            by_encounter_type=by_type,
            external_referrals_today=external_referrals,
            medications_scheduled_today=meds_scheduled,
            medications_administered_today=meds_administered,
            medications_refused_today=meds_refused,
            medications_missed_today=meds_missed,
            follow_ups_due_week=len(follow_ups),
            physicals_due_month=len(physicals)
        )
