"""
Staff Service - Business logic for staff management.

Handles staff records, shift scheduling, and training/certification tracking.
Key features:
- Employee number auto-generation (EMP-NNNNN)
- Shift assignment and on-duty tracking
- Certification expiry monitoring
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.staff.models import Staff, StaffShift, StaffTraining
from src.modules.staff.repository import (
    StaffRepository, StaffShiftRepository, StaffTrainingRepository
)
from src.modules.staff.dtos import (
    StaffCreateDTO, StaffUpdateDTO, StaffDTO, StaffListDTO,
    ShiftCreateDTO, ShiftUpdateDTO, ShiftDTO, ShiftListDTO,
    TrainingCreateDTO, TrainingUpdateDTO, TrainingDTO, TrainingListDTO,
    OnDutyStaffDTO, DailyScheduleDTO, ExpiringCertificationDTO,
    StaffStatisticsDTO, BulkShiftCreateDTO
)
from src.common.enums import (
    StaffRank, Department, StaffStatus,
    ShiftType, ShiftStatus, TrainingType
)


class StaffService:
    """Service for staff management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.staff_repo = StaffRepository(session)
        self.shift_repo = StaffShiftRepository(session)
        self.training_repo = StaffTrainingRepository(session)

    # =========================================================================
    # Staff Operations
    # =========================================================================

    async def create_staff(self, data: StaffCreateDTO) -> Staff:
        """
        Create a new staff record with auto-generated employee number.

        Args:
            data: Staff creation data

        Returns:
            Created Staff entity
        """
        # Generate employee number
        employee_number = await self.staff_repo.get_next_employee_number()

        staff = Staff(
            id=uuid4(),
            user_id=data.user_id,
            employee_number=employee_number,
            first_name=data.first_name,
            last_name=data.last_name,
            rank=data.rank,
            department=data.department,
            hire_date=data.hire_date,
            status=StaffStatus.ACTIVE,
            phone=data.phone,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            certifications=[],
            is_active=True
        )

        return await self.staff_repo.create(staff)

    async def get_staff(self, staff_id: UUID) -> Optional[Staff]:
        """Get staff by ID."""
        return await self.staff_repo.get_by_id(staff_id)

    async def get_staff_by_employee_number(self, employee_number: str) -> Optional[Staff]:
        """Get staff by employee number."""
        return await self.staff_repo.get_by_employee_number(employee_number)

    async def get_all_staff(
        self,
        department: Optional[Department] = None,
        rank: Optional[StaffRank] = None,
        status: Optional[StaffStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Staff]:
        """Get all staff with optional filters."""
        return await self.staff_repo.get_all(
            department=department,
            rank=rank,
            status=status,
            is_active=is_active,
            skip=skip,
            limit=limit
        )

    async def get_staff_by_department(self, department: Department) -> List[Staff]:
        """Get all active staff in a department."""
        return await self.staff_repo.get_by_department(department)

    async def update_staff(self, staff_id: UUID, data: StaffUpdateDTO) -> Optional[Staff]:
        """Update staff record."""
        staff = await self.staff_repo.get_by_id(staff_id)
        if not staff:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(staff, field, value)

        return await self.staff_repo.update(staff)

    async def deactivate_staff(self, staff_id: UUID) -> Optional[Staff]:
        """Deactivate a staff member."""
        staff = await self.staff_repo.get_by_id(staff_id)
        if not staff:
            return None

        staff.is_active = False
        staff.status = StaffStatus.TERMINATED
        return await self.staff_repo.update(staff)

    async def delete_staff(self, staff_id: UUID) -> bool:
        """Soft delete a staff record."""
        staff = await self.staff_repo.get_by_id(staff_id)
        if not staff:
            return False

        await self.staff_repo.soft_delete(staff)
        return True

    # =========================================================================
    # Shift Operations
    # =========================================================================

    async def assign_shift(
        self,
        data: ShiftCreateDTO,
        created_by: UUID
    ) -> StaffShift:
        """
        Assign a shift to a staff member.

        Args:
            data: Shift creation data
            created_by: Staff ID of the person creating the schedule

        Returns:
            Created StaffShift entity
        """
        shift = StaffShift(
            id=uuid4(),
            staff_id=data.staff_id,
            shift_date=data.shift_date,
            shift_type=data.shift_type,
            start_time=data.start_time,
            end_time=data.end_time,
            housing_unit_id=data.housing_unit_id,
            status=ShiftStatus.SCHEDULED,
            notes=data.notes,
            created_by=created_by
        )

        return await self.shift_repo.create(shift)

    async def assign_bulk_shifts(
        self,
        data: BulkShiftCreateDTO,
        created_by: UUID
    ) -> List[StaffShift]:
        """Create multiple shifts at once."""
        shifts = []
        for shift_data in data.shifts:
            shift = StaffShift(
                id=uuid4(),
                staff_id=shift_data.staff_id,
                shift_date=shift_data.shift_date,
                shift_type=shift_data.shift_type,
                start_time=shift_data.start_time,
                end_time=shift_data.end_time,
                housing_unit_id=shift_data.housing_unit_id,
                status=ShiftStatus.SCHEDULED,
                notes=shift_data.notes,
                created_by=created_by
            )
            shifts.append(shift)

        return await self.shift_repo.create_bulk(shifts)

    async def get_shift(self, shift_id: UUID) -> Optional[StaffShift]:
        """Get shift by ID."""
        return await self.shift_repo.get_by_id(shift_id)

    async def get_staff_shifts(
        self,
        staff_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffShift]:
        """Get shifts for a staff member."""
        return await self.shift_repo.get_by_staff(
            staff_id=staff_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

    async def get_shifts_by_date(
        self,
        shift_date: date,
        shift_type: Optional[ShiftType] = None
    ) -> List[StaffShift]:
        """Get all shifts for a specific date."""
        return await self.shift_repo.get_by_date(
            shift_date=shift_date,
            shift_type=shift_type
        )

    async def get_daily_schedule(self, schedule_date: date) -> DailyScheduleDTO:
        """
        Get complete daily schedule organized by shift type.

        Args:
            schedule_date: Date to get schedule for

        Returns:
            DailyScheduleDTO with shifts organized by type
        """
        all_shifts = await self.shift_repo.get_by_date(schedule_date)

        day_shifts = []
        evening_shifts = []
        night_shifts = []

        for shift in all_shifts:
            shift_dto = ShiftListDTO(
                id=shift.id,
                staff_name=shift.staff.full_name if shift.staff else "Unknown",
                employee_number=shift.staff.employee_number if shift.staff else "",
                shift_date=shift.shift_date,
                shift_type=shift.shift_type,
                start_time=shift.start_time,
                end_time=shift.end_time,
                status=shift.status,
                housing_unit_name=shift.housing_unit.name if shift.housing_unit else None
            )

            if shift.shift_type == ShiftType.DAY:
                day_shifts.append(shift_dto)
            elif shift.shift_type == ShiftType.EVENING:
                evening_shifts.append(shift_dto)
            else:
                night_shifts.append(shift_dto)

        return DailyScheduleDTO(
            date=schedule_date,
            day_shifts=day_shifts,
            evening_shifts=evening_shifts,
            night_shifts=night_shifts,
            total_staff=len(all_shifts),
            coverage_gaps=None  # Could implement gap analysis here
        )

    async def get_staff_on_duty(self, as_of: Optional[datetime] = None) -> List[OnDutyStaffDTO]:
        """
        Get staff currently on duty.

        Args:
            as_of: Datetime to check (defaults to now)

        Returns:
            List of OnDutyStaffDTO with current duty information
        """
        if as_of is None:
            as_of = datetime.utcnow()

        shifts = await self.shift_repo.get_on_duty(as_of)

        result = []
        for shift in shifts:
            if shift.staff:
                result.append(OnDutyStaffDTO(
                    staff_id=shift.staff.id,
                    employee_number=shift.staff.employee_number,
                    staff_name=shift.staff.full_name,
                    rank=shift.staff.rank,
                    department=shift.staff.department,
                    shift_id=shift.id,
                    shift_type=shift.shift_type,
                    start_time=shift.start_time,
                    end_time=shift.end_time,
                    housing_unit_name=shift.housing_unit.name if shift.housing_unit else None
                ))

        return result

    async def update_shift(self, shift_id: UUID, data: ShiftUpdateDTO) -> Optional[StaffShift]:
        """Update a shift."""
        shift = await self.shift_repo.get_by_id(shift_id)
        if not shift:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shift, field, value)

        return await self.shift_repo.update(shift)

    async def start_shift(self, shift_id: UUID) -> Optional[StaffShift]:
        """Mark a shift as in progress."""
        shift = await self.shift_repo.get_by_id(shift_id)
        if not shift:
            return None

        shift.status = ShiftStatus.IN_PROGRESS
        return await self.shift_repo.update(shift)

    async def complete_shift(self, shift_id: UUID) -> Optional[StaffShift]:
        """Mark a shift as completed."""
        shift = await self.shift_repo.get_by_id(shift_id)
        if not shift:
            return None

        shift.status = ShiftStatus.COMPLETED
        return await self.shift_repo.update(shift)

    async def delete_shift(self, shift_id: UUID) -> bool:
        """Delete a shift."""
        shift = await self.shift_repo.get_by_id(shift_id)
        if not shift:
            return False

        await self.shift_repo.delete(shift)
        return True

    # =========================================================================
    # Training Operations
    # =========================================================================

    async def add_training(self, data: TrainingCreateDTO) -> StaffTraining:
        """
        Add a training record for a staff member.

        Automatically marks previous training of same type as not current.

        Args:
            data: Training creation data

        Returns:
            Created StaffTraining entity
        """
        # Mark previous training of same type as superseded
        await self.training_repo.mark_superseded(data.staff_id, data.training_type)

        training = StaffTraining(
            id=uuid4(),
            staff_id=data.staff_id,
            training_type=data.training_type,
            training_date=data.training_date,
            expiry_date=data.expiry_date,
            hours=data.hours,
            instructor=data.instructor,
            certification_number=data.certification_number,
            is_current=True
        )

        return await self.training_repo.create(training)

    async def get_training(self, training_id: UUID) -> Optional[StaffTraining]:
        """Get training record by ID."""
        return await self.training_repo.get_by_id(training_id)

    async def get_staff_training(
        self,
        staff_id: UUID,
        training_type: Optional[TrainingType] = None,
        current_only: bool = False
    ) -> List[StaffTraining]:
        """Get training records for a staff member."""
        return await self.training_repo.get_by_staff(
            staff_id=staff_id,
            training_type=training_type,
            current_only=current_only
        )

    async def get_expiring_certifications(
        self,
        days: int = 30,
        training_type: Optional[TrainingType] = None
    ) -> List[ExpiringCertificationDTO]:
        """
        Get certifications expiring within specified days.

        Args:
            days: Number of days to look ahead (default 30)
            training_type: Optional filter by training type

        Returns:
            List of ExpiringCertificationDTO sorted by expiry date
        """
        training_records = await self.training_repo.get_expiring_certifications(
            days=days,
            training_type=training_type
        )

        result = []
        for training in training_records:
            if training.staff and training.expiry_date:
                result.append(ExpiringCertificationDTO(
                    training_id=training.id,
                    staff_id=training.staff.id,
                    staff_name=training.staff.full_name,
                    employee_number=training.staff.employee_number,
                    department=training.staff.department,
                    training_type=training.training_type,
                    expiry_date=training.expiry_date,
                    days_until_expiry=(training.expiry_date - date.today()).days
                ))

        return result

    async def get_expired_certifications(self) -> List[StaffTraining]:
        """Get all currently expired certifications."""
        return await self.training_repo.get_expired_certifications()

    async def update_training(
        self,
        training_id: UUID,
        data: TrainingUpdateDTO
    ) -> Optional[StaffTraining]:
        """Update a training record."""
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(training, field, value)

        return await self.training_repo.update(training)

    async def delete_training(self, training_id: UUID) -> bool:
        """Delete a training record."""
        training = await self.training_repo.get_by_id(training_id)
        if not training:
            return False

        await self.training_repo.delete(training)
        return True

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_statistics(self) -> StaffStatisticsDTO:
        """
        Get comprehensive staff statistics.

        Returns:
            StaffStatisticsDTO with counts and breakdowns
        """
        # Get counts by status
        total = await self.staff_repo.count()
        active = await self.staff_repo.count(status=StaffStatus.ACTIVE)
        on_leave = await self.staff_repo.count(status=StaffStatus.ON_LEAVE)
        suspended = await self.staff_repo.count(status=StaffStatus.SUSPENDED)

        # Get counts by department
        by_department = {}
        for dept in Department:
            count = await self.staff_repo.count(department=dept)
            if count > 0:
                by_department[dept.value] = count

        # Get all staff for rank breakdown
        all_staff = await self.staff_repo.get_all(limit=10000)
        by_rank = {}
        total_years = 0
        for staff in all_staff:
            rank_key = staff.rank.value
            by_rank[rank_key] = by_rank.get(rank_key, 0) + 1
            total_years += staff.years_of_service

        avg_years = total_years / len(all_staff) if all_staff else 0

        # Shift statistics for today
        today = date.today()
        shifts_today = await self.shift_repo.count_by_date(today)
        on_duty = await self.get_staff_on_duty()

        # Training statistics
        expiring_30 = await self.training_repo.count_expiring(30)
        expired = await self.training_repo.count_expired()

        return StaffStatisticsDTO(
            total_staff=total,
            active_staff=active,
            on_leave=on_leave,
            suspended=suspended,
            by_department=by_department,
            by_rank=by_rank,
            shifts_today=shifts_today,
            staff_on_duty=len(on_duty),
            expiring_certifications_30_days=expiring_30,
            expired_certifications=expired,
            average_years_of_service=round(avg_years, 1)
        )
