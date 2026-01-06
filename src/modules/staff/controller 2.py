"""
Staff Controller - REST API endpoints for staff management.

Provides endpoints for staff records, shift scheduling, and training management.
All endpoints require authentication.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify
from quart_schema import validate_request, validate_querystring

from src.database.async_db import get_async_session
from src.modules.staff.service import StaffService
from src.modules.staff.dtos import (
    StaffCreateDTO, StaffUpdateDTO, StaffDTO, StaffListDTO,
    ShiftCreateDTO, ShiftUpdateDTO, ShiftDTO,
    TrainingCreateDTO, TrainingUpdateDTO, TrainingDTO,
    BulkShiftCreateDTO
)
from src.common.enums import Department, StaffRank, StaffStatus, ShiftType, TrainingType

# Blueprint for auto-discovery
staff_bp = Blueprint('staff', __name__, url_prefix='/api/v1/staff')
blueprint = staff_bp  # Alias for auto-discovery


# =============================================================================
# Staff Endpoints
# =============================================================================

@staff_bp.route('', methods=['POST'])
@validate_request(StaffCreateDTO)
async def create_staff(data: StaffCreateDTO):
    """
    Create a new staff record.

    POST /api/v1/staff
    """
    async with get_async_session() as session:
        service = StaffService(session)
        staff = await service.create_staff(data)
        await session.commit()

        return jsonify({
            'id': str(staff.id),
            'employee_number': staff.employee_number,
            'full_name': staff.full_name,
            'message': 'Staff record created successfully'
        }), 201


@staff_bp.route('', methods=['GET'])
async def get_all_staff():
    """
    Get all staff with optional filters.

    GET /api/v1/staff?department=SECURITY&rank=OFFICER&status=ACTIVE&is_active=true&skip=0&limit=100
    """
    department = request.args.get('department')
    rank = request.args.get('rank')
    status = request.args.get('status')
    is_active = request.args.get('is_active')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    async with get_async_session() as session:
        service = StaffService(session)
        staff_list = await service.get_all_staff(
            department=Department(department) if department else None,
            rank=StaffRank(rank) if rank else None,
            status=StaffStatus(status) if status else None,
            is_active=is_active.lower() == 'true' if is_active else None,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(s.id),
            'employee_number': s.employee_number,
            'full_name': s.full_name,
            'rank': s.rank.value,
            'department': s.department.value,
            'status': s.status.value,
            'is_active': s.is_active
        } for s in staff_list])


@staff_bp.route('/<uuid:staff_id>', methods=['GET'])
async def get_staff(staff_id: UUID):
    """
    Get staff by ID.

    GET /api/v1/staff/{id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        staff = await service.get_staff(staff_id)

        if not staff:
            return jsonify({'error': 'Staff not found'}), 404

        return jsonify({
            'id': str(staff.id),
            'user_id': str(staff.user_id),
            'employee_number': staff.employee_number,
            'first_name': staff.first_name,
            'last_name': staff.last_name,
            'full_name': staff.full_name,
            'rank': staff.rank.value,
            'department': staff.department.value,
            'hire_date': staff.hire_date.isoformat(),
            'years_of_service': staff.years_of_service,
            'status': staff.status.value,
            'phone': staff.phone,
            'emergency_contact_name': staff.emergency_contact_name,
            'emergency_contact_phone': staff.emergency_contact_phone,
            'certifications': staff.certifications,
            'is_active': staff.is_active,
            'inserted_date': staff.inserted_date.isoformat() if staff.inserted_date else None,
            'updated_date': staff.updated_date.isoformat() if staff.updated_date else None
        })


@staff_bp.route('/<uuid:staff_id>', methods=['PUT'])
@validate_request(StaffUpdateDTO)
async def update_staff(staff_id: UUID, data: StaffUpdateDTO):
    """
    Update staff record.

    PUT /api/v1/staff/{id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        staff = await service.update_staff(staff_id, data)

        if not staff:
            return jsonify({'error': 'Staff not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(staff.id),
            'employee_number': staff.employee_number,
            'full_name': staff.full_name,
            'message': 'Staff record updated successfully'
        })


@staff_bp.route('/<uuid:staff_id>', methods=['DELETE'])
async def delete_staff(staff_id: UUID):
    """
    Soft delete staff record.

    DELETE /api/v1/staff/{id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        success = await service.delete_staff(staff_id)

        if not success:
            return jsonify({'error': 'Staff not found'}), 404

        await session.commit()

        return jsonify({'message': 'Staff record deleted successfully'})


@staff_bp.route('/by-department/<department>', methods=['GET'])
async def get_staff_by_department(department: str):
    """
    Get all active staff in a department.

    GET /api/v1/staff/by-department/{dept}
    """
    try:
        dept = Department(department)
    except ValueError:
        return jsonify({'error': f'Invalid department: {department}'}), 400

    async with get_async_session() as session:
        service = StaffService(session)
        staff_list = await service.get_staff_by_department(dept)

        return jsonify([{
            'id': str(s.id),
            'employee_number': s.employee_number,
            'full_name': s.full_name,
            'rank': s.rank.value,
            'status': s.status.value,
            'is_active': s.is_active
        } for s in staff_list])


@staff_bp.route('/on-duty', methods=['GET'])
async def get_staff_on_duty():
    """
    Get staff currently on duty.

    GET /api/v1/staff/on-duty
    """
    async with get_async_session() as session:
        service = StaffService(session)
        on_duty = await service.get_staff_on_duty()

        return jsonify([{
            'staff_id': str(s.staff_id),
            'employee_number': s.employee_number,
            'staff_name': s.staff_name,
            'rank': s.rank.value,
            'department': s.department.value,
            'shift_id': str(s.shift_id),
            'shift_type': s.shift_type.value,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat(),
            'housing_unit_name': s.housing_unit_name
        } for s in on_duty])


# =============================================================================
# Shift Endpoints
# =============================================================================

@staff_bp.route('/<uuid:staff_id>/shifts', methods=['POST'])
@validate_request(ShiftCreateDTO)
async def create_shift(staff_id: UUID, data: ShiftCreateDTO):
    """
    Create a shift for a staff member.

    POST /api/v1/staff/{id}/shifts
    """
    # Override staff_id from URL
    data.staff_id = staff_id

    # TODO: Get created_by from authenticated user
    created_by = staff_id  # Placeholder

    async with get_async_session() as session:
        service = StaffService(session)
        shift = await service.assign_shift(data, created_by)
        await session.commit()

        return jsonify({
            'id': str(shift.id),
            'staff_id': str(shift.staff_id),
            'shift_date': shift.shift_date.isoformat(),
            'shift_type': shift.shift_type.value,
            'status': shift.status.value,
            'message': 'Shift assigned successfully'
        }), 201


@staff_bp.route('/<uuid:staff_id>/shifts', methods=['GET'])
async def get_staff_shifts(staff_id: UUID):
    """
    Get shifts for a staff member.

    GET /api/v1/staff/{id}/shifts?start_date=2026-01-01&end_date=2026-01-31
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    start_date = date.fromisoformat(start_date_str) if start_date_str else None
    end_date = date.fromisoformat(end_date_str) if end_date_str else None

    async with get_async_session() as session:
        service = StaffService(session)
        shifts = await service.get_staff_shifts(
            staff_id=staff_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

        return jsonify([{
            'id': str(s.id),
            'staff_id': str(s.staff_id),
            'shift_date': s.shift_date.isoformat(),
            'shift_type': s.shift_type.value,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat(),
            'housing_unit_id': str(s.housing_unit_id) if s.housing_unit_id else None,
            'status': s.status.value,
            'notes': s.notes
        } for s in shifts])


@staff_bp.route('/shifts/date/<shift_date>', methods=['GET'])
async def get_shifts_by_date(shift_date: str):
    """
    Get all shifts for a specific date.

    GET /api/v1/staff/shifts/date/{date}?shift_type=DAY
    """
    try:
        parsed_date = date.fromisoformat(shift_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    shift_type_str = request.args.get('shift_type')
    shift_type = ShiftType(shift_type_str) if shift_type_str else None

    async with get_async_session() as session:
        service = StaffService(session)
        schedule = await service.get_daily_schedule(parsed_date)

        if shift_type:
            # Filter to specific shift type
            if shift_type == ShiftType.DAY:
                shifts = schedule.day_shifts
            elif shift_type == ShiftType.EVENING:
                shifts = schedule.evening_shifts
            else:
                shifts = schedule.night_shifts

            return jsonify([s.model_dump() for s in shifts])

        # Return full schedule
        return jsonify({
            'date': schedule.date.isoformat(),
            'day_shifts': [s.model_dump() for s in schedule.day_shifts],
            'evening_shifts': [s.model_dump() for s in schedule.evening_shifts],
            'night_shifts': [s.model_dump() for s in schedule.night_shifts],
            'total_staff': schedule.total_staff
        })


@staff_bp.route('/shifts/<uuid:shift_id>', methods=['PUT'])
@validate_request(ShiftUpdateDTO)
async def update_shift(shift_id: UUID, data: ShiftUpdateDTO):
    """
    Update a shift.

    PUT /api/v1/staff/shifts/{shift_id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        shift = await service.update_shift(shift_id, data)

        if not shift:
            return jsonify({'error': 'Shift not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(shift.id),
            'status': shift.status.value,
            'message': 'Shift updated successfully'
        })


@staff_bp.route('/shifts/<uuid:shift_id>/start', methods=['POST'])
async def start_shift(shift_id: UUID):
    """
    Mark a shift as in progress.

    POST /api/v1/staff/shifts/{shift_id}/start
    """
    async with get_async_session() as session:
        service = StaffService(session)
        shift = await service.start_shift(shift_id)

        if not shift:
            return jsonify({'error': 'Shift not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(shift.id),
            'status': shift.status.value,
            'message': 'Shift started'
        })


@staff_bp.route('/shifts/<uuid:shift_id>/complete', methods=['POST'])
async def complete_shift(shift_id: UUID):
    """
    Mark a shift as completed.

    POST /api/v1/staff/shifts/{shift_id}/complete
    """
    async with get_async_session() as session:
        service = StaffService(session)
        shift = await service.complete_shift(shift_id)

        if not shift:
            return jsonify({'error': 'Shift not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(shift.id),
            'status': shift.status.value,
            'message': 'Shift completed'
        })


@staff_bp.route('/shifts/<uuid:shift_id>', methods=['DELETE'])
async def delete_shift(shift_id: UUID):
    """
    Delete a shift.

    DELETE /api/v1/staff/shifts/{shift_id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        success = await service.delete_shift(shift_id)

        if not success:
            return jsonify({'error': 'Shift not found'}), 404

        await session.commit()

        return jsonify({'message': 'Shift deleted successfully'})


# =============================================================================
# Training Endpoints
# =============================================================================

@staff_bp.route('/<uuid:staff_id>/training', methods=['POST'])
@validate_request(TrainingCreateDTO)
async def add_training(staff_id: UUID, data: TrainingCreateDTO):
    """
    Add a training record for a staff member.

    POST /api/v1/staff/{id}/training
    """
    # Override staff_id from URL
    data.staff_id = staff_id

    async with get_async_session() as session:
        service = StaffService(session)
        training = await service.add_training(data)
        await session.commit()

        return jsonify({
            'id': str(training.id),
            'staff_id': str(training.staff_id),
            'training_type': training.training_type.value,
            'training_date': training.training_date.isoformat(),
            'expiry_date': training.expiry_date.isoformat() if training.expiry_date else None,
            'message': 'Training record added successfully'
        }), 201


@staff_bp.route('/<uuid:staff_id>/training', methods=['GET'])
async def get_staff_training(staff_id: UUID):
    """
    Get training records for a staff member.

    GET /api/v1/staff/{id}/training?training_type=CPR&current_only=true
    """
    training_type_str = request.args.get('training_type')
    current_only = request.args.get('current_only', 'false').lower() == 'true'

    training_type = TrainingType(training_type_str) if training_type_str else None

    async with get_async_session() as session:
        service = StaffService(session)
        training_list = await service.get_staff_training(
            staff_id=staff_id,
            training_type=training_type,
            current_only=current_only
        )

        return jsonify([{
            'id': str(t.id),
            'training_type': t.training_type.value,
            'training_date': t.training_date.isoformat(),
            'expiry_date': t.expiry_date.isoformat() if t.expiry_date else None,
            'hours': t.hours,
            'instructor': t.instructor,
            'certification_number': t.certification_number,
            'is_current': t.is_current,
            'is_expired': t.is_expired,
            'days_until_expiry': t.days_until_expiry
        } for t in training_list])


@staff_bp.route('/training/expiring', methods=['GET'])
async def get_expiring_certifications():
    """
    Get certifications expiring within specified days.

    GET /api/v1/staff/training/expiring?days=30&training_type=CPR
    """
    days = int(request.args.get('days', 30))
    training_type_str = request.args.get('training_type')

    training_type = TrainingType(training_type_str) if training_type_str else None

    async with get_async_session() as session:
        service = StaffService(session)
        expiring = await service.get_expiring_certifications(
            days=days,
            training_type=training_type
        )

        return jsonify([{
            'training_id': str(e.training_id),
            'staff_id': str(e.staff_id),
            'staff_name': e.staff_name,
            'employee_number': e.employee_number,
            'department': e.department.value,
            'training_type': e.training_type.value,
            'expiry_date': e.expiry_date.isoformat(),
            'days_until_expiry': e.days_until_expiry
        } for e in expiring])


@staff_bp.route('/training/<uuid:training_id>', methods=['PUT'])
@validate_request(TrainingUpdateDTO)
async def update_training(training_id: UUID, data: TrainingUpdateDTO):
    """
    Update a training record.

    PUT /api/v1/staff/training/{training_id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        training = await service.update_training(training_id, data)

        if not training:
            return jsonify({'error': 'Training record not found'}), 404

        await session.commit()

        return jsonify({
            'id': str(training.id),
            'message': 'Training record updated successfully'
        })


@staff_bp.route('/training/<uuid:training_id>', methods=['DELETE'])
async def delete_training(training_id: UUID):
    """
    Delete a training record.

    DELETE /api/v1/staff/training/{training_id}
    """
    async with get_async_session() as session:
        service = StaffService(session)
        success = await service.delete_training(training_id)

        if not success:
            return jsonify({'error': 'Training record not found'}), 404

        await session.commit()

        return jsonify({'message': 'Training record deleted successfully'})


# =============================================================================
# Statistics Endpoint
# =============================================================================

@staff_bp.route('/statistics', methods=['GET'])
async def get_staff_statistics():
    """
    Get comprehensive staff statistics.

    GET /api/v1/staff/statistics
    """
    async with get_async_session() as session:
        service = StaffService(session)
        stats = await service.get_statistics()

        return jsonify({
            'total_staff': stats.total_staff,
            'active_staff': stats.active_staff,
            'on_leave': stats.on_leave,
            'suspended': stats.suspended,
            'by_department': stats.by_department,
            'by_rank': stats.by_rank,
            'shifts_today': stats.shifts_today,
            'staff_on_duty': stats.staff_on_duty,
            'expiring_certifications_30_days': stats.expiring_certifications_30_days,
            'expired_certifications': stats.expired_certifications,
            'average_years_of_service': stats.average_years_of_service
        })
