"""
Healthcare Controller - REST API endpoints for healthcare management.

HIPAA NOTE: All endpoints handle Protected Health Information (PHI).
Access must be restricted to authorized medical personnel via RBAC.

Provides endpoints for medical records, encounters, and medication administration.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify
from quart_schema import validate_request

from src.database.async_db import get_async_session
from src.modules.healthcare.service import HealthcareService
from src.modules.healthcare.dtos import (
    MedicalRecordCreateDTO, MedicalRecordUpdateDTO, SuicideWatchUpdateDTO,
    EncounterCreateDTO, MedicationScheduleDTO, MedicationAdministerDTO,
    MedicationRefuseDTO
)
from src.common.enums import EncounterType, MedAdminStatus

# Blueprint for auto-discovery
healthcare_bp = Blueprint('healthcare', __name__, url_prefix='/api/v1/healthcare')
blueprint = healthcare_bp  # Alias for auto-discovery


# =============================================================================
# Medical Record Endpoints
# =============================================================================

@healthcare_bp.route('/records', methods=['POST'])
@validate_request(MedicalRecordCreateDTO)
async def create_medical_record(data: MedicalRecordCreateDTO):
    """
    Create a medical record (intake screening).

    POST /api/v1/healthcare/records

    HIPAA: Requires MEDICAL role.
    """
    # TODO: Get created_by from authenticated user and verify MEDICAL role
    created_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = HealthcareService(session)
        record = await service.create_intake_screening(data, created_by)
        await session.commit()

        return jsonify({
            'id': str(record.id),
            'inmate_id': str(record.inmate_id),
            'mental_health_flag': record.mental_health_flag,
            'suicide_watch': record.suicide_watch,
            'message': 'Medical record created (intake screening completed)'
        }), 201


@healthcare_bp.route('/records', methods=['GET'])
async def get_all_medical_records():
    """
    Get all medical records with optional filters.

    GET /api/v1/healthcare/records?mental_health_flag=true&suicide_watch=true

    HIPAA: Requires MEDICAL role.
    """
    mental_health = request.args.get('mental_health_flag')
    suicide_watch = request.args.get('suicide_watch')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = HealthcareService(session)
        records = await service.get_all_medical_records(
            mental_health_flag=mental_health.lower() == 'true' if mental_health else None,
            suicide_watch=suicide_watch.lower() == 'true' if suicide_watch else None,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(r.id),
            'inmate_id': str(r.inmate_id),
            'inmate_name': r.inmate.full_name if r.inmate else None,
            'blood_type': r.blood_type.value if r.blood_type else None,
            'allergy_count': len(r.allergies) if r.allergies else 0,
            'chronic_condition_count': len(r.chronic_conditions) if r.chronic_conditions else 0,
            'mental_health_flag': r.mental_health_flag,
            'suicide_watch': r.suicide_watch
        } for r in records])


@healthcare_bp.route('/inmates/<uuid:inmate_id>/medical', methods=['GET'])
async def get_inmate_medical_record(inmate_id: UUID):
    """
    Get medical record for a specific inmate.

    GET /api/v1/healthcare/inmates/{id}/medical

    HIPAA: Requires MEDICAL role.
    """
    async with get_async_session() as session:
        service = HealthcareService(session)
        record = await service.get_inmate_medical_record(inmate_id)

        if not record:
            return jsonify({'error': 'Medical record not found'}), 404

        return jsonify({
            'id': str(record.id),
            'inmate_id': str(record.inmate_id),
            'inmate_name': record.inmate.full_name if record.inmate else None,
            'inmate_booking_number': record.inmate.booking_number if record.inmate else None,
            'blood_type': record.blood_type.value if record.blood_type else None,
            'allergies': record.allergies,
            'chronic_conditions': record.chronic_conditions,
            'current_medications': record.current_medications,
            'emergency_contact_name': record.emergency_contact_name,
            'emergency_contact_phone': record.emergency_contact_phone,
            'last_physical_date': record.last_physical_date.isoformat() if record.last_physical_date else None,
            'next_physical_due': record.next_physical_due.isoformat() if record.next_physical_due else None,
            'mental_health_flag': record.mental_health_flag,
            'suicide_watch': record.suicide_watch,
            'dietary_restrictions': record.dietary_restrictions,
            'disability_accommodations': record.disability_accommodations,
            'inserted_date': record.inserted_date.isoformat() if record.inserted_date else None,
            'updated_date': record.updated_date.isoformat() if record.updated_date else None
        })


@healthcare_bp.route('/inmates/<uuid:inmate_id>/medical', methods=['PUT'])
@validate_request(MedicalRecordUpdateDTO)
async def update_inmate_medical_record(inmate_id: UUID, data: MedicalRecordUpdateDTO):
    """
    Update an inmate's medical record.

    PUT /api/v1/healthcare/inmates/{id}/medical

    HIPAA: Requires MEDICAL role.
    """
    async with get_async_session() as session:
        service = HealthcareService(session)
        record = await service.update_medical_record(inmate_id, data)

        if not record:
            return jsonify({'error': 'Medical record not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(record.id),
            'inmate_id': str(record.inmate_id),
            'message': 'Medical record updated successfully'
        })


@healthcare_bp.route('/inmates/<uuid:inmate_id>/medical/suicide-watch', methods=['PUT'])
@validate_request(SuicideWatchUpdateDTO)
async def update_suicide_watch(inmate_id: UUID, data: SuicideWatchUpdateDTO):
    """
    Update suicide watch status - CRITICAL operation.

    PUT /api/v1/healthcare/inmates/{id}/medical/suicide-watch

    HIPAA: Requires MEDICAL role (specifically mental health authority).
    """
    # TODO: Get updated_by from authenticated user
    updated_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = HealthcareService(session)
        record = await service.update_suicide_watch(inmate_id, data, updated_by)

        if not record:
            return jsonify({'error': 'Medical record not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(record.id),
            'inmate_id': str(record.inmate_id),
            'suicide_watch': record.suicide_watch,
            'message': f'Suicide watch {"enabled" if record.suicide_watch else "disabled"}'
        })


@healthcare_bp.route('/suicide-watch', methods=['GET'])
async def get_suicide_watch_inmates():
    """
    Get all inmates currently on suicide watch.

    GET /api/v1/healthcare/suicide-watch

    HIPAA: Requires MEDICAL role. Critical safety list.
    """
    async with get_async_session() as session:
        service = HealthcareService(session)
        inmates = await service.get_suicide_watch_inmates()

        return jsonify([{
            'inmate_id': str(i.inmate_id),
            'inmate_name': i.inmate_name,
            'inmate_booking_number': i.inmate_booking_number,
            'housing_unit': i.housing_unit,
            'suicide_watch_since': i.suicide_watch_since.isoformat() if i.suicide_watch_since else None,
            'mental_health_flag': i.mental_health_flag,
            'last_encounter_date': i.last_encounter_date.isoformat() if i.last_encounter_date else None,
            'last_encounter_type': i.last_encounter_type.value if i.last_encounter_type else None
        } for i in inmates])


# =============================================================================
# Medical Encounter Endpoints
# =============================================================================

@healthcare_bp.route('/encounters', methods=['POST'])
@validate_request(EncounterCreateDTO)
async def create_encounter(data: EncounterCreateDTO):
    """
    Create a medical encounter.

    POST /api/v1/healthcare/encounters

    HIPAA: Requires MEDICAL role.
    """
    # TODO: Get created_by from authenticated user
    created_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = HealthcareService(session)
        encounter = await service.create_encounter(data, created_by)
        await session.commit()

        return jsonify({
            'id': str(encounter.id),
            'inmate_id': str(encounter.inmate_id),
            'encounter_type': encounter.encounter_type.value,
            'encounter_date': encounter.encounter_date.isoformat(),
            'message': 'Medical encounter recorded'
        }), 201


@healthcare_bp.route('/encounters', methods=['GET'])
async def get_encounters():
    """
    Get encounters for a specific date.

    GET /api/v1/healthcare/encounters?date=2026-01-05&encounter_type=SICK_CALL

    HIPAA: Requires MEDICAL role.
    """
    date_str = request.args.get('date')
    encounter_type_str = request.args.get('encounter_type')

    if not date_str:
        return jsonify({'error': 'date parameter is required'}), 400

    try:
        encounter_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    encounter_type = EncounterType(encounter_type_str) if encounter_type_str else None

    async with get_async_session() as session:
        service = HealthcareService(session)
        encounters = await service.get_encounters_by_date(encounter_date, encounter_type)

        return jsonify([{
            'id': str(e.id),
            'inmate_id': str(e.inmate_id),
            'inmate_name': e.inmate.full_name if e.inmate else None,
            'encounter_date': e.encounter_date.isoformat(),
            'encounter_type': e.encounter_type.value,
            'chief_complaint': e.chief_complaint,
            'provider_name': e.provider_name,
            'provider_type': e.provider_type.value,
            'follow_up_required': e.follow_up_required,
            'referred_external': e.referred_external
        } for e in encounters])


@healthcare_bp.route('/inmates/<uuid:inmate_id>/encounters', methods=['GET'])
async def get_inmate_encounters(inmate_id: UUID):
    """
    Get encounters for a specific inmate.

    GET /api/v1/healthcare/inmates/{id}/encounters?encounter_type=MENTAL_HEALTH

    HIPAA: Requires MEDICAL role.
    """
    encounter_type_str = request.args.get('encounter_type')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    encounter_type = EncounterType(encounter_type_str) if encounter_type_str else None

    async with get_async_session() as session:
        service = HealthcareService(session)
        encounters = await service.get_inmate_encounters(
            inmate_id=inmate_id,
            encounter_type=encounter_type,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(e.id),
            'encounter_date': e.encounter_date.isoformat(),
            'encounter_type': e.encounter_type.value,
            'chief_complaint': e.chief_complaint,
            'diagnosis': e.diagnosis,
            'treatment': e.treatment,
            'vitals': e.vitals,
            'provider_name': e.provider_name,
            'provider_type': e.provider_type.value,
            'follow_up_required': e.follow_up_required,
            'follow_up_date': e.follow_up_date.isoformat() if e.follow_up_date else None,
            'referred_external': e.referred_external,
            'external_facility': e.external_facility
        } for e in encounters])


# =============================================================================
# Medication Administration Endpoints
# =============================================================================

@healthcare_bp.route('/medications/schedule', methods=['POST'])
@validate_request(MedicationScheduleDTO)
async def schedule_medication(data: MedicationScheduleDTO):
    """
    Schedule a medication for administration.

    POST /api/v1/healthcare/medications/schedule

    HIPAA: Requires MEDICAL role.
    """
    async with get_async_session() as session:
        service = HealthcareService(session)
        med_admin = await service.schedule_medication(data)
        await session.commit()

        return jsonify({
            'id': str(med_admin.id),
            'inmate_id': str(med_admin.inmate_id),
            'medication_name': med_admin.medication_name,
            'dosage': med_admin.dosage,
            'scheduled_time': med_admin.scheduled_time.isoformat(),
            'status': med_admin.status.value,
            'message': 'Medication scheduled'
        }), 201


@healthcare_bp.route('/medications/due', methods=['GET'])
async def get_medications_due():
    """
    Get medications due within specified minutes.

    GET /api/v1/healthcare/medications/due?within_minutes=60

    HIPAA: Requires MEDICAL role.
    """
    within_minutes = int(request.args.get('within_minutes', 60))

    async with get_async_session() as session:
        service = HealthcareService(session)
        medications = await service.get_upcoming_medications(within_minutes)

        return jsonify([{
            'id': str(m.id),
            'inmate_id': str(m.inmate_id),
            'inmate_name': m.inmate_name,
            'inmate_booking_number': m.inmate_booking_number,
            'medication_name': m.medication_name,
            'dosage': m.dosage,
            'route': m.route.value,
            'scheduled_time': m.scheduled_time.isoformat(),
            'minutes_until_due': m.minutes_until_due,
            'is_overdue': m.is_overdue
        } for m in medications])


@healthcare_bp.route('/medications/<uuid:admin_id>/administer', methods=['POST'])
@validate_request(MedicationAdministerDTO)
async def administer_medication(admin_id: UUID, data: MedicationAdministerDTO):
    """
    Record medication administration.

    POST /api/v1/healthcare/medications/{id}/administer

    HIPAA: Requires MEDICAL role.
    """
    # TODO: Get administered_by from authenticated user
    administered_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = HealthcareService(session)

        try:
            med_admin = await service.administer_medication(admin_id, data, administered_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not med_admin:
            return jsonify({'error': 'Medication administration record not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(med_admin.id),
            'status': med_admin.status.value,
            'administered_time': med_admin.administered_time.isoformat() if med_admin.administered_time else None,
            'message': 'Medication administered'
        })


@healthcare_bp.route('/medications/<uuid:admin_id>/refuse', methods=['POST'])
@validate_request(MedicationRefuseDTO)
async def refuse_medication(admin_id: UUID, data: MedicationRefuseDTO):
    """
    Record medication refusal.

    Requires witness documentation for legal protection.

    POST /api/v1/healthcare/medications/{id}/refuse

    HIPAA: Requires MEDICAL role.
    """
    # TODO: Get recorded_by from authenticated user
    recorded_by = UUID('00000000-0000-0000-0000-000000000000')  # Placeholder

    async with get_async_session() as session:
        service = HealthcareService(session)

        try:
            med_admin = await service.refuse_medication(admin_id, data, recorded_by)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        if not med_admin:
            return jsonify({'error': 'Medication administration record not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(med_admin.id),
            'status': med_admin.status.value,
            'refusal_witnessed_by': str(med_admin.refusal_witnessed_by),
            'message': 'Medication refusal documented'
        })


@healthcare_bp.route('/inmates/<uuid:inmate_id>/medications', methods=['GET'])
async def get_inmate_medications(inmate_id: UUID):
    """
    Get medication administrations for an inmate.

    GET /api/v1/healthcare/inmates/{id}/medications?status=SCHEDULED

    HIPAA: Requires MEDICAL role.
    """
    status_str = request.args.get('status')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    status = MedAdminStatus(status_str) if status_str else None

    async with get_async_session() as session:
        service = HealthcareService(session)
        medications = await service.get_inmate_medications(
            inmate_id=inmate_id,
            status=status,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(m.id),
            'medication_name': m.medication_name,
            'dosage': m.dosage,
            'route': m.route.value,
            'scheduled_time': m.scheduled_time.isoformat(),
            'administered_time': m.administered_time.isoformat() if m.administered_time else None,
            'status': m.status.value,
            'notes': m.notes
        } for m in medications])


# =============================================================================
# Statistics Endpoint
# =============================================================================

@healthcare_bp.route('/statistics', methods=['GET'])
async def get_healthcare_statistics():
    """
    Get comprehensive healthcare statistics.

    GET /api/v1/healthcare/statistics

    HIPAA: Requires MEDICAL role.
    """
    async with get_async_session() as session:
        service = HealthcareService(session)
        stats = await service.get_statistics()

        return jsonify({
            'total_medical_records': stats.total_medical_records,
            'inmates_with_allergies': stats.inmates_with_allergies,
            'inmates_with_chronic_conditions': stats.inmates_with_chronic_conditions,
            'mental_health_flagged': stats.mental_health_flagged,
            'on_suicide_watch': stats.on_suicide_watch,
            'encounters_today': stats.encounters_today,
            'by_encounter_type': stats.by_encounter_type,
            'external_referrals_today': stats.external_referrals_today,
            'medications_scheduled_today': stats.medications_scheduled_today,
            'medications_administered_today': stats.medications_administered_today,
            'medications_refused_today': stats.medications_refused_today,
            'medications_missed_today': stats.medications_missed_today,
            'follow_ups_due_week': stats.follow_ups_due_week,
            'physicals_due_month': stats.physicals_due_month
        })
