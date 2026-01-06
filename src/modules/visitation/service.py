"""
Visitation Service - Business logic for visitation management.

Handles visitor approval, visit scheduling, and check-in/out processes.
Key features:
- Background check requirement for visitor approval
- Conflict detection for visit scheduling
- Check-in/out workflow with security logging
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.visitation.models import ApprovedVisitor, VisitSchedule, VisitLog
from src.modules.visitation.repository import (
    ApprovedVisitorRepository, VisitScheduleRepository, VisitLogRepository
)
from src.modules.visitation.dtos import (
    VisitorCreateDTO, VisitorUpdateDTO, VisitorApprovalDTO, VisitorDenialDTO,
    VisitScheduleCreateDTO, VisitScheduleUpdateDTO, VisitCancelDTO,
    CheckInDTO, CheckOutDTO, TodaysVisitDTO, VisitationStatisticsDTO
)
from src.common.enums import CheckStatus, VisitStatus, VisitType


class VisitationService:
    """Service for visitation management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.visitor_repo = ApprovedVisitorRepository(session)
        self.schedule_repo = VisitScheduleRepository(session)
        self.log_repo = VisitLogRepository(session)

    # =========================================================================
    # Visitor Operations
    # =========================================================================

    async def register_visitor(self, data: VisitorCreateDTO) -> ApprovedVisitor:
        """
        Register a new visitor for an inmate.

        Visitor starts with PENDING background check status and is_approved=False.

        Args:
            data: Visitor registration data

        Returns:
            Created ApprovedVisitor entity
        """
        visitor = ApprovedVisitor(
            id=uuid4(),
            inmate_id=data.inmate_id,
            first_name=data.first_name,
            last_name=data.last_name,
            relationship=data.relationship,
            phone=data.phone,
            email=data.email,
            id_type=data.id_type,
            id_number=data.id_number,
            date_of_birth=data.date_of_birth,
            photo_url=data.photo_url,
            background_check_status=CheckStatus.PENDING,
            is_approved=False,
            is_active=True
        )

        return await self.visitor_repo.create(visitor)

    async def get_visitor(self, visitor_id: UUID) -> Optional[ApprovedVisitor]:
        """Get visitor by ID."""
        return await self.visitor_repo.get_by_id(visitor_id)

    async def get_all_visitors(
        self,
        check_status: Optional[CheckStatus] = None,
        is_approved: Optional[bool] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ApprovedVisitor]:
        """Get all visitors with optional filters."""
        return await self.visitor_repo.get_all(
            check_status=check_status,
            is_approved=is_approved,
            is_active=is_active,
            skip=skip,
            limit=limit
        )

    async def get_inmate_visitors(
        self,
        inmate_id: UUID,
        approved_only: bool = False
    ) -> List[ApprovedVisitor]:
        """Get all visitors registered for an inmate."""
        return await self.visitor_repo.get_by_inmate(
            inmate_id=inmate_id,
            approved_only=approved_only
        )

    async def update_visitor(
        self,
        visitor_id: UUID,
        data: VisitorUpdateDTO
    ) -> Optional[ApprovedVisitor]:
        """Update visitor information."""
        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(visitor, field, value)

        return await self.visitor_repo.update(visitor)

    async def approve_visitor(
        self,
        visitor_id: UUID,
        data: VisitorApprovalDTO,
        approved_by: UUID
    ) -> Optional[ApprovedVisitor]:
        """
        Approve a visitor after background check.

        Requires background_check_date to be set - this ensures
        the security team has performed a background check.

        Args:
            visitor_id: Visitor to approve
            data: Approval data including background check date
            approved_by: User ID of approving officer

        Returns:
            Updated ApprovedVisitor or None if not found
        """
        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            return None

        # Require background check date
        if not data.background_check_date:
            raise ValueError("Background check date is required for approval")

        visitor.background_check_date = data.background_check_date
        visitor.background_check_status = data.background_check_status

        if data.background_check_status == CheckStatus.APPROVED:
            visitor.is_approved = True
            visitor.approval_date = date.today()
            visitor.approved_by = approved_by
            visitor.denied_reason = None
        else:
            visitor.is_approved = False

        return await self.visitor_repo.update(visitor)

    async def deny_visitor(
        self,
        visitor_id: UUID,
        data: VisitorDenialDTO,
        denied_by: UUID
    ) -> Optional[ApprovedVisitor]:
        """
        Deny a visitor.

        Args:
            visitor_id: Visitor to deny
            data: Denial data including reason
            denied_by: User ID of denying officer

        Returns:
            Updated ApprovedVisitor or None if not found
        """
        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            return None

        visitor.background_check_status = CheckStatus.DENIED
        visitor.is_approved = False
        visitor.denied_reason = data.denied_reason
        visitor.approved_by = denied_by

        if data.background_check_date:
            visitor.background_check_date = data.background_check_date

        return await self.visitor_repo.update(visitor)

    async def deactivate_visitor(self, visitor_id: UUID) -> Optional[ApprovedVisitor]:
        """Deactivate a visitor."""
        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            return None

        visitor.is_active = False
        return await self.visitor_repo.update(visitor)

    # =========================================================================
    # Visit Schedule Operations
    # =========================================================================

    async def schedule_visit(
        self,
        data: VisitScheduleCreateDTO,
        created_by: UUID
    ) -> VisitSchedule:
        """
        Schedule a new visit.

        Validates:
        1. Visitor is approved and active
        2. No conflicting visits for the inmate at the same time

        Args:
            data: Visit scheduling data
            created_by: User ID creating the schedule

        Returns:
            Created VisitSchedule entity

        Raises:
            ValueError: If visitor not approved or time conflict exists
        """
        # Verify visitor is approved
        visitor = await self.visitor_repo.get_by_id(data.visitor_id)
        if not visitor:
            raise ValueError("Visitor not found")
        if not visitor.is_approved:
            raise ValueError("Visitor is not approved for visits")
        if not visitor.is_active:
            raise ValueError("Visitor is not active")

        # Check for time conflicts
        has_conflict = await self.schedule_repo.check_conflict(
            inmate_id=data.inmate_id,
            visit_date=data.scheduled_date,
            start_time=data.scheduled_time,
            duration_minutes=data.duration_minutes
        )

        if has_conflict:
            raise ValueError("Time conflict with existing visit")

        schedule = VisitSchedule(
            id=uuid4(),
            inmate_id=data.inmate_id,
            visitor_id=data.visitor_id,
            scheduled_date=data.scheduled_date,
            scheduled_time=data.scheduled_time,
            duration_minutes=data.duration_minutes,
            visit_type=data.visit_type,
            status=VisitStatus.SCHEDULED,
            location=data.location,
            notes=data.notes,
            created_by=created_by
        )

        return await self.schedule_repo.create(schedule)

    async def get_visit_schedule(self, schedule_id: UUID) -> Optional[VisitSchedule]:
        """Get visit schedule by ID."""
        return await self.schedule_repo.get_by_id(schedule_id)

    async def get_visits_by_date(
        self,
        visit_date: date,
        status: Optional[VisitStatus] = None,
        visit_type: Optional[VisitType] = None
    ) -> List[VisitSchedule]:
        """Get all visits for a specific date."""
        return await self.schedule_repo.get_by_date(
            visit_date=visit_date,
            status=status,
            visit_type=visit_type
        )

    async def get_todays_visits(self) -> List[TodaysVisitDTO]:
        """
        Get all visits scheduled for today with status info.

        Returns:
            List of TodaysVisitDTO with visit and check-in status
        """
        today = date.today()
        visits = await self.schedule_repo.get_by_date(today)

        result = []
        for visit in visits:
            result.append(TodaysVisitDTO(
                visit_id=visit.id,
                inmate_id=visit.inmate_id,
                inmate_name=visit.inmate.full_name if visit.inmate else "Unknown",
                inmate_booking_number=visit.inmate.booking_number if visit.inmate else "",
                visitor_id=visit.visitor_id,
                visitor_name=visit.visitor.full_name if visit.visitor else "Unknown",
                relationship=visit.visitor.relationship if visit.visitor else None,
                scheduled_time=visit.scheduled_time,
                duration_minutes=visit.duration_minutes,
                visit_type=visit.visit_type,
                status=visit.status,
                location=visit.location,
                is_checked_in=visit.visit_log is not None,
                checked_in_at=visit.visit_log.checked_in_at if visit.visit_log else None
            ))

        return result

    async def update_visit_schedule(
        self,
        schedule_id: UUID,
        data: VisitScheduleUpdateDTO
    ) -> Optional[VisitSchedule]:
        """Update a visit schedule."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            return None

        # Only allow updates if visit is still scheduled
        if schedule.status != VisitStatus.SCHEDULED:
            raise ValueError(f"Cannot update visit with status {schedule.status.value}")

        # Check for conflicts if date/time is being changed
        update_data = data.model_dump(exclude_unset=True)

        if 'scheduled_date' in update_data or 'scheduled_time' in update_data or 'duration_minutes' in update_data:
            new_date = update_data.get('scheduled_date', schedule.scheduled_date)
            new_time = update_data.get('scheduled_time', schedule.scheduled_time)
            new_duration = update_data.get('duration_minutes', schedule.duration_minutes)

            has_conflict = await self.schedule_repo.check_conflict(
                inmate_id=schedule.inmate_id,
                visit_date=new_date,
                start_time=new_time,
                duration_minutes=new_duration,
                exclude_id=schedule_id
            )

            if has_conflict:
                raise ValueError("Time conflict with existing visit")

        for field, value in update_data.items():
            setattr(schedule, field, value)

        return await self.schedule_repo.update(schedule)

    async def cancel_visit(
        self,
        schedule_id: UUID,
        data: VisitCancelDTO
    ) -> Optional[VisitSchedule]:
        """Cancel a scheduled visit."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            return None

        # Can only cancel scheduled visits
        if schedule.status not in [VisitStatus.SCHEDULED, VisitStatus.CHECKED_IN]:
            raise ValueError(f"Cannot cancel visit with status {schedule.status.value}")

        schedule.status = VisitStatus.CANCELLED
        schedule.cancelled_reason = data.cancelled_reason

        return await self.schedule_repo.update(schedule)

    # =========================================================================
    # Check-In/Out Operations
    # =========================================================================

    async def check_in_visitor(
        self,
        schedule_id: UUID,
        data: CheckInDTO,
        processed_by: UUID
    ) -> VisitLog:
        """
        Check in a visitor for their scheduled visit.

        Creates a VisitLog record and updates schedule status.

        Args:
            schedule_id: Visit schedule to check in
            data: Check-in data including search status and stored items
            processed_by: Staff member processing check-in

        Returns:
            Created VisitLog

        Raises:
            ValueError: If visit not found or not in SCHEDULED status
        """
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Visit schedule not found")

        if schedule.status != VisitStatus.SCHEDULED:
            raise ValueError(f"Cannot check in visit with status {schedule.status.value}")

        # Create visit log
        now = datetime.utcnow()
        log = VisitLog(
            id=uuid4(),
            visit_schedule_id=schedule_id,
            checked_in_at=now,
            visitor_searched=data.visitor_searched,
            items_stored=data.items_stored or [],
            contraband_found=False,
            notes=data.notes,
            processed_by=processed_by
        )

        # Update schedule status
        schedule.status = VisitStatus.CHECKED_IN
        schedule.actual_start_time = now

        await self.schedule_repo.update(schedule)
        return await self.log_repo.create(log)

    async def start_visit(self, schedule_id: UUID) -> Optional[VisitSchedule]:
        """Mark a visit as in progress."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            return None

        if schedule.status != VisitStatus.CHECKED_IN:
            raise ValueError(f"Cannot start visit with status {schedule.status.value}")

        schedule.status = VisitStatus.IN_PROGRESS
        if not schedule.actual_start_time:
            schedule.actual_start_time = datetime.utcnow()

        return await self.schedule_repo.update(schedule)

    async def check_out_visitor(
        self,
        schedule_id: UUID,
        data: CheckOutDTO
    ) -> Optional[VisitLog]:
        """
        Check out a visitor after their visit.

        Updates VisitLog with checkout time and any incident info.

        Args:
            schedule_id: Visit schedule to check out
            data: Check-out data including contraband and incident info

        Returns:
            Updated VisitLog or None if not found
        """
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Visit schedule not found")

        if schedule.status not in [VisitStatus.CHECKED_IN, VisitStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot check out visit with status {schedule.status.value}")

        log = await self.log_repo.get_by_schedule(schedule_id)
        if not log:
            raise ValueError("Visit log not found")

        # Update log
        now = datetime.utcnow()
        log.checked_out_at = now
        log.contraband_found = data.contraband_found
        log.incident_id = data.incident_id

        if data.notes:
            existing_notes = log.notes or ""
            log.notes = f"{existing_notes}\nCheckout: {data.notes}".strip()

        # Update schedule
        schedule.status = VisitStatus.COMPLETED
        schedule.actual_end_time = now

        await self.schedule_repo.update(schedule)
        return await self.log_repo.update(log)

    async def mark_no_show(self, schedule_id: UUID) -> Optional[VisitSchedule]:
        """Mark a visitor as no-show."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            return None

        if schedule.status != VisitStatus.SCHEDULED:
            raise ValueError(f"Cannot mark no-show for visit with status {schedule.status.value}")

        schedule.status = VisitStatus.NO_SHOW

        return await self.schedule_repo.update(schedule)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_statistics(self) -> VisitationStatisticsDTO:
        """
        Get comprehensive visitation statistics.

        Returns:
            VisitationStatisticsDTO with counts and metrics
        """
        today = date.today()
        week_ago = datetime.combine(today - timedelta(days=7), time.min)
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)

        # Visitor counts
        total_approved = await self.visitor_repo.count(is_approved=True)
        pending = await self.visitor_repo.count(check_status=CheckStatus.PENDING)
        active = await self.visitor_repo.count(is_active=True)

        # Today's visit counts
        status_counts = await self.schedule_repo.count_by_status(today)
        scheduled = status_counts.get(VisitStatus.SCHEDULED.value, 0)
        completed = status_counts.get(VisitStatus.COMPLETED.value, 0)
        in_progress = (
            status_counts.get(VisitStatus.CHECKED_IN.value, 0) +
            status_counts.get(VisitStatus.IN_PROGRESS.value, 0)
        )
        no_shows = status_counts.get(VisitStatus.NO_SHOW.value, 0)
        cancellations = status_counts.get(VisitStatus.CANCELLED.value, 0)

        # Visit types today
        todays_visits = await self.schedule_repo.get_by_date(today)
        by_type = {}
        for visit in todays_visits:
            type_key = visit.visit_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

        # Security stats
        contraband_week = await self.log_repo.count_contraband_incidents(week_ago, today_end)
        searched_today = await self.log_repo.count_searched_today(today)

        # Average duration
        avg_duration = await self.log_repo.get_average_duration(today)

        return VisitationStatisticsDTO(
            total_approved_visitors=total_approved,
            pending_approval=pending,
            active_visitors=active,
            visits_scheduled_today=scheduled + completed + in_progress,
            visits_completed_today=completed,
            visits_in_progress=in_progress,
            no_shows_today=no_shows,
            cancellations_today=cancellations,
            by_visit_type=by_type,
            contraband_incidents_week=contraband_week,
            total_visitors_searched_today=searched_today,
            average_visit_duration_minutes=avg_duration
        )
