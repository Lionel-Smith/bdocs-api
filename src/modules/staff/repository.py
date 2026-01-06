"""
Staff Repository - Data access layer for staff management.

Handles database operations for Staff, StaffShift, and StaffTraining entities.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.staff.models import Staff, StaffShift, StaffTraining
from src.common.enums import (
    StaffRank, Department, StaffStatus,
    ShiftType, ShiftStatus, TrainingType
)


class StaffRepository:
    """Repository for Staff operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, staff: Staff) -> Staff:
        """Create a new staff record."""
        self.session.add(staff)
        await self.session.flush()
        await self.session.refresh(staff)
        return staff

    async def get_by_id(self, staff_id: UUID) -> Optional[Staff]:
        """Get staff by ID."""
        result = await self.session.execute(
            select(Staff)
            .where(and_(Staff.id == staff_id, Staff.is_deleted == False))
            .options(selectinload(Staff.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Staff]:
        """Get staff by linked user ID."""
        result = await self.session.execute(
            select(Staff)
            .where(and_(Staff.user_id == user_id, Staff.is_deleted == False))
        )
        return result.scalar_one_or_none()

    async def get_by_employee_number(self, employee_number: str) -> Optional[Staff]:
        """Get staff by employee number."""
        result = await self.session.execute(
            select(Staff)
            .where(and_(
                Staff.employee_number == employee_number,
                Staff.is_deleted == False
            ))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        department: Optional[Department] = None,
        rank: Optional[StaffRank] = None,
        status: Optional[StaffStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Staff]:
        """Get all staff with optional filters."""
        query = select(Staff).where(Staff.is_deleted == False)

        if department:
            query = query.where(Staff.department == department)
        if rank:
            query = query.where(Staff.rank == rank)
        if status:
            query = query.where(Staff.status == status)
        if is_active is not None:
            query = query.where(Staff.is_active == is_active)

        query = query.order_by(Staff.last_name, Staff.first_name)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_department(self, department: Department) -> List[Staff]:
        """Get all staff in a department."""
        result = await self.session.execute(
            select(Staff)
            .where(and_(
                Staff.department == department,
                Staff.is_deleted == False,
                Staff.is_active == True
            ))
            .order_by(Staff.rank, Staff.last_name)
        )
        return list(result.scalars().all())

    async def get_active_staff(self) -> List[Staff]:
        """Get all active staff."""
        result = await self.session.execute(
            select(Staff)
            .where(and_(
                Staff.is_deleted == False,
                Staff.is_active == True,
                Staff.status == StaffStatus.ACTIVE
            ))
            .order_by(Staff.department, Staff.rank, Staff.last_name)
        )
        return list(result.scalars().all())

    async def update(self, staff: Staff) -> Staff:
        """Update a staff record."""
        await self.session.flush()
        await self.session.refresh(staff)
        return staff

    async def soft_delete(self, staff: Staff) -> Staff:
        """Soft delete a staff record."""
        staff.is_deleted = True
        staff.deleted_at = datetime.utcnow()
        staff.is_active = False
        await self.session.flush()
        return staff

    async def count(
        self,
        department: Optional[Department] = None,
        status: Optional[StaffStatus] = None
    ) -> int:
        """Count staff with optional filters."""
        query = select(func.count(Staff.id)).where(Staff.is_deleted == False)

        if department:
            query = query.where(Staff.department == department)
        if status:
            query = query.where(Staff.status == status)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_next_employee_number(self) -> str:
        """Generate next employee number in sequence."""
        result = await self.session.execute(
            select(func.max(Staff.employee_number))
            .where(Staff.employee_number.like('EMP-%'))
        )
        max_number = result.scalar()

        if max_number:
            current = int(max_number.split('-')[1])
            next_num = current + 1
        else:
            next_num = 1

        return f"EMP-{next_num:05d}"


class StaffShiftRepository:
    """Repository for StaffShift operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, shift: StaffShift) -> StaffShift:
        """Create a new shift."""
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def create_bulk(self, shifts: List[StaffShift]) -> List[StaffShift]:
        """Create multiple shifts."""
        self.session.add_all(shifts)
        await self.session.flush()
        for shift in shifts:
            await self.session.refresh(shift)
        return shifts

    async def get_by_id(self, shift_id: UUID) -> Optional[StaffShift]:
        """Get shift by ID."""
        result = await self.session.execute(
            select(StaffShift)
            .where(StaffShift.id == shift_id)
            .options(
                selectinload(StaffShift.staff),
                selectinload(StaffShift.housing_unit),
                selectinload(StaffShift.creator)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_staff(
        self,
        staff_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StaffShift]:
        """Get shifts for a staff member."""
        query = select(StaffShift).where(StaffShift.staff_id == staff_id)

        if start_date:
            query = query.where(StaffShift.shift_date >= start_date)
        if end_date:
            query = query.where(StaffShift.shift_date <= end_date)

        query = query.order_by(StaffShift.shift_date.desc(), StaffShift.start_time)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_date(
        self,
        shift_date: date,
        shift_type: Optional[ShiftType] = None,
        housing_unit_id: Optional[UUID] = None
    ) -> List[StaffShift]:
        """Get all shifts for a specific date."""
        query = select(StaffShift).where(StaffShift.shift_date == shift_date)

        if shift_type:
            query = query.where(StaffShift.shift_type == shift_type)
        if housing_unit_id:
            query = query.where(StaffShift.housing_unit_id == housing_unit_id)

        query = query.options(
            selectinload(StaffShift.staff),
            selectinload(StaffShift.housing_unit)
        )
        query = query.order_by(StaffShift.shift_type, StaffShift.start_time)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_on_duty(self, as_of: datetime) -> List[StaffShift]:
        """Get shifts currently in progress."""
        today = as_of.date()
        current_time = as_of.time()

        result = await self.session.execute(
            select(StaffShift)
            .where(and_(
                StaffShift.shift_date == today,
                StaffShift.status == ShiftStatus.IN_PROGRESS
            ))
            .options(
                selectinload(StaffShift.staff),
                selectinload(StaffShift.housing_unit)
            )
        )
        return list(result.scalars().all())

    async def get_scheduled_for_today(self, today: date) -> List[StaffShift]:
        """Get all scheduled shifts for today."""
        result = await self.session.execute(
            select(StaffShift)
            .where(and_(
                StaffShift.shift_date == today,
                StaffShift.status.in_([ShiftStatus.SCHEDULED, ShiftStatus.IN_PROGRESS])
            ))
            .options(
                selectinload(StaffShift.staff),
                selectinload(StaffShift.housing_unit)
            )
            .order_by(StaffShift.shift_type, StaffShift.start_time)
        )
        return list(result.scalars().all())

    async def update(self, shift: StaffShift) -> StaffShift:
        """Update a shift."""
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def delete(self, shift: StaffShift) -> None:
        """Hard delete a shift."""
        await self.session.delete(shift)
        await self.session.flush()

    async def count_by_date(self, shift_date: date) -> int:
        """Count shifts for a date."""
        result = await self.session.execute(
            select(func.count(StaffShift.id))
            .where(StaffShift.shift_date == shift_date)
        )
        return result.scalar() or 0


class StaffTrainingRepository:
    """Repository for StaffTraining operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, training: StaffTraining) -> StaffTraining:
        """Create a new training record."""
        self.session.add(training)
        await self.session.flush()
        await self.session.refresh(training)
        return training

    async def get_by_id(self, training_id: UUID) -> Optional[StaffTraining]:
        """Get training record by ID."""
        result = await self.session.execute(
            select(StaffTraining)
            .where(StaffTraining.id == training_id)
            .options(selectinload(StaffTraining.staff))
        )
        return result.scalar_one_or_none()

    async def get_by_staff(
        self,
        staff_id: UUID,
        training_type: Optional[TrainingType] = None,
        current_only: bool = False
    ) -> List[StaffTraining]:
        """Get training records for a staff member."""
        query = select(StaffTraining).where(StaffTraining.staff_id == staff_id)

        if training_type:
            query = query.where(StaffTraining.training_type == training_type)
        if current_only:
            query = query.where(StaffTraining.is_current == True)

        query = query.order_by(StaffTraining.training_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expiring_certifications(
        self,
        days: int = 30,
        training_type: Optional[TrainingType] = None
    ) -> List[StaffTraining]:
        """Get certifications expiring within specified days."""
        today = date.today()
        cutoff = today + timedelta(days=days)

        query = select(StaffTraining).where(and_(
            StaffTraining.is_current == True,
            StaffTraining.expiry_date.isnot(None),
            StaffTraining.expiry_date <= cutoff,
            StaffTraining.expiry_date >= today  # Not already expired
        ))

        if training_type:
            query = query.where(StaffTraining.training_type == training_type)

        query = query.options(selectinload(StaffTraining.staff))
        query = query.order_by(StaffTraining.expiry_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired_certifications(self) -> List[StaffTraining]:
        """Get currently expired certifications."""
        today = date.today()

        result = await self.session.execute(
            select(StaffTraining)
            .where(and_(
                StaffTraining.is_current == True,
                StaffTraining.expiry_date.isnot(None),
                StaffTraining.expiry_date < today
            ))
            .options(selectinload(StaffTraining.staff))
            .order_by(StaffTraining.expiry_date)
        )
        return list(result.scalars().all())

    async def update(self, training: StaffTraining) -> StaffTraining:
        """Update a training record."""
        await self.session.flush()
        await self.session.refresh(training)
        return training

    async def mark_superseded(
        self,
        staff_id: UUID,
        training_type: TrainingType
    ) -> int:
        """Mark previous training of same type as not current."""
        from sqlalchemy import update

        result = await self.session.execute(
            update(StaffTraining)
            .where(and_(
                StaffTraining.staff_id == staff_id,
                StaffTraining.training_type == training_type,
                StaffTraining.is_current == True
            ))
            .values(is_current=False)
        )
        await self.session.flush()
        return result.rowcount

    async def delete(self, training: StaffTraining) -> None:
        """Hard delete a training record."""
        await self.session.delete(training)
        await self.session.flush()

    async def count_expiring(self, days: int = 30) -> int:
        """Count certifications expiring within specified days."""
        today = date.today()
        cutoff = today + timedelta(days=days)

        result = await self.session.execute(
            select(func.count(StaffTraining.id))
            .where(and_(
                StaffTraining.is_current == True,
                StaffTraining.expiry_date.isnot(None),
                StaffTraining.expiry_date <= cutoff,
                StaffTraining.expiry_date >= today
            ))
        )
        return result.scalar() or 0

    async def count_expired(self) -> int:
        """Count expired certifications."""
        today = date.today()

        result = await self.session.execute(
            select(func.count(StaffTraining.id))
            .where(and_(
                StaffTraining.is_current == True,
                StaffTraining.expiry_date.isnot(None),
                StaffTraining.expiry_date < today
            ))
        )
        return result.scalar() or 0
