"""
Reentry Planning Repository - Data access for reentry operations.

Three repository classes:
- ReentryPlanRepository: Master plan CRUD and queries
- ReentryChecklistRepository: Checklist item management
- ReentryReferralRepository: Service referral tracking

Key queries:
- get_upcoming_releases(days): Plans with release in next N days
- get_not_ready_plans(): Active plans below readiness threshold
- get_active_plan(inmate_id): Current non-completed plan for inmate
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.reentry.models import (
    ReentryPlan,
    ReentryChecklist,
    ReentryReferral
)
from src.common.enums import PlanStatus, ReferralStatus


class ReentryPlanRepository:
    """Repository for reentry plan operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, plan: ReentryPlan) -> ReentryPlan:
        """Create a new reentry plan."""
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_by_id(
        self,
        plan_id: UUID,
        include_checklist: bool = True,
        include_referrals: bool = False
    ) -> Optional[ReentryPlan]:
        """Get plan by ID with optional related data."""
        query = select(ReentryPlan).where(
            ReentryPlan.id == plan_id,
            ReentryPlan.is_deleted == False
        )

        if include_checklist:
            query = query.options(selectinload(ReentryPlan.checklist_items))

        if include_referrals:
            query = query.options(selectinload(ReentryPlan.referrals))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_plan(self, inmate_id: UUID) -> Optional[ReentryPlan]:
        """Get the current active (non-completed) plan for an inmate."""
        query = select(ReentryPlan).where(
            ReentryPlan.inmate_id == inmate_id,
            ReentryPlan.status != PlanStatus.COMPLETED.value,
            ReentryPlan.is_deleted == False
        ).options(
            selectinload(ReentryPlan.checklist_items),
            selectinload(ReentryPlan.referrals)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_completed: bool = True
    ) -> List[ReentryPlan]:
        """Get all plans for an inmate."""
        query = select(ReentryPlan).where(
            ReentryPlan.inmate_id == inmate_id,
            ReentryPlan.is_deleted == False
        ).options(selectinload(ReentryPlan.checklist_items))

        if not include_completed:
            query = query.where(ReentryPlan.status != PlanStatus.COMPLETED.value)

        query = query.order_by(ReentryPlan.expected_release_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[ReentryPlan]:
        """Get all plans with a specific status."""
        query = select(ReentryPlan).where(
            ReentryPlan.status == status,
            ReentryPlan.is_deleted == False
        ).options(
            selectinload(ReentryPlan.checklist_items),
            selectinload(ReentryPlan.inmate)
        ).order_by(ReentryPlan.expected_release_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_releases(
        self,
        days: int = 90
    ) -> List[ReentryPlan]:
        """Get plans with release dates in the next N days."""
        today = date.today()
        future_date = today + timedelta(days=days)

        query = select(ReentryPlan).where(
            ReentryPlan.expected_release_date >= today,
            ReentryPlan.expected_release_date <= future_date,
            ReentryPlan.status.in_([
                PlanStatus.DRAFT.value,
                PlanStatus.IN_PROGRESS.value,
                PlanStatus.READY.value
            ]),
            ReentryPlan.is_deleted == False
        ).options(
            selectinload(ReentryPlan.checklist_items),
            selectinload(ReentryPlan.inmate)
        ).order_by(ReentryPlan.expected_release_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_not_ready_plans(
        self,
        days_threshold: int = 30
    ) -> List[ReentryPlan]:
        """
        Get plans that are not ready and releasing within threshold days.

        These require immediate attention.
        """
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)

        query = select(ReentryPlan).where(
            ReentryPlan.expected_release_date <= threshold_date,
            ReentryPlan.status.in_([
                PlanStatus.DRAFT.value,
                PlanStatus.IN_PROGRESS.value
            ]),
            ReentryPlan.is_deleted == False
        ).options(
            selectinload(ReentryPlan.checklist_items),
            selectinload(ReentryPlan.inmate)
        ).order_by(ReentryPlan.expected_release_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_active(self) -> List[ReentryPlan]:
        """Get all non-completed plans."""
        query = select(ReentryPlan).where(
            ReentryPlan.status != PlanStatus.COMPLETED.value,
            ReentryPlan.is_deleted == False
        ).options(
            selectinload(ReentryPlan.checklist_items),
            selectinload(ReentryPlan.inmate)
        ).order_by(ReentryPlan.expected_release_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, plan: ReentryPlan) -> ReentryPlan:
        """Update a plan."""
        await self.session.flush()
        return plan

    async def soft_delete(self, plan: ReentryPlan) -> bool:
        """Soft delete a plan."""
        plan.is_deleted = True
        plan.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def count_by_status(self) -> dict:
        """Count plans by status."""
        query = select(
            ReentryPlan.status,
            func.count(ReentryPlan.id)
        ).where(
            ReentryPlan.is_deleted == False
        ).group_by(ReentryPlan.status)

        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def count_upcoming_releases(self, days: int) -> int:
        """Count releases in the next N days."""
        today = date.today()
        future_date = today + timedelta(days=days)

        query = select(func.count(ReentryPlan.id)).where(
            ReentryPlan.expected_release_date >= today,
            ReentryPlan.expected_release_date <= future_date,
            ReentryPlan.status != PlanStatus.COMPLETED.value,
            ReentryPlan.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar() or 0


class ReentryChecklistRepository:
    """Repository for reentry checklist operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, item: ReentryChecklist) -> ReentryChecklist:
        """Create a checklist item."""
        self.session.add(item)
        await self.session.flush()
        return item

    async def create_many(self, items: List[ReentryChecklist]) -> List[ReentryChecklist]:
        """Create multiple checklist items."""
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def get_by_id(self, item_id: UUID) -> Optional[ReentryChecklist]:
        """Get checklist item by ID."""
        query = select(ReentryChecklist).where(ReentryChecklist.id == item_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_plan(
        self,
        plan_id: UUID,
        completed_only: bool = False,
        incomplete_only: bool = False
    ) -> List[ReentryChecklist]:
        """Get checklist items for a plan."""
        query = select(ReentryChecklist).where(
            ReentryChecklist.reentry_plan_id == plan_id
        )

        if completed_only:
            query = query.where(ReentryChecklist.is_completed == True)
        elif incomplete_only:
            query = query.where(ReentryChecklist.is_completed == False)

        query = query.order_by(
            ReentryChecklist.item_type,
            ReentryChecklist.due_date.nullsfirst()
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        plan_id: UUID,
        item_type: str
    ) -> List[ReentryChecklist]:
        """Get checklist items of a specific type."""
        query = select(ReentryChecklist).where(
            ReentryChecklist.reentry_plan_id == plan_id,
            ReentryChecklist.item_type == item_type
        ).order_by(ReentryChecklist.due_date.nullsfirst())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue(self, plan_id: UUID) -> List[ReentryChecklist]:
        """Get overdue incomplete items."""
        today = date.today()
        query = select(ReentryChecklist).where(
            ReentryChecklist.reentry_plan_id == plan_id,
            ReentryChecklist.is_completed == False,
            ReentryChecklist.due_date < today
        ).order_by(ReentryChecklist.due_date)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, item: ReentryChecklist) -> ReentryChecklist:
        """Update a checklist item."""
        await self.session.flush()
        return item

    async def delete(self, item: ReentryChecklist) -> bool:
        """Delete a checklist item (hard delete - no soft delete for checklist)."""
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def count_completion(self, plan_id: UUID) -> dict:
        """Count completed vs total items for a plan."""
        query = select(
            func.count(ReentryChecklist.id).label('total'),
            func.sum(
                func.cast(ReentryChecklist.is_completed, type_=func.coalesce)
            ).label('completed')
        ).where(ReentryChecklist.reentry_plan_id == plan_id)

        # Alternative approach for counting
        total_query = select(func.count(ReentryChecklist.id)).where(
            ReentryChecklist.reentry_plan_id == plan_id
        )
        completed_query = select(func.count(ReentryChecklist.id)).where(
            ReentryChecklist.reentry_plan_id == plan_id,
            ReentryChecklist.is_completed == True
        )

        total_result = await self.session.execute(total_query)
        completed_result = await self.session.execute(completed_query)

        total = total_result.scalar() or 0
        completed = completed_result.scalar() or 0

        return {
            'total': total,
            'completed': completed,
            'incomplete': total - completed
        }


class ReentryReferralRepository:
    """Repository for reentry referral operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, referral: ReentryReferral) -> ReentryReferral:
        """Create a referral."""
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def get_by_id(self, referral_id: UUID) -> Optional[ReentryReferral]:
        """Get referral by ID."""
        query = select(ReentryReferral).where(
            ReentryReferral.id == referral_id,
            ReentryReferral.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_plan(
        self,
        plan_id: UUID,
        active_only: bool = False
    ) -> List[ReentryReferral]:
        """Get referrals for a plan."""
        query = select(ReentryReferral).where(
            ReentryReferral.reentry_plan_id == plan_id,
            ReentryReferral.is_deleted == False
        )

        if active_only:
            query = query.where(
                ReentryReferral.status.in_([
                    ReferralStatus.PENDING.value,
                    ReferralStatus.ACCEPTED.value,
                    ReferralStatus.IN_PROGRESS.value
                ])
            )

        query = query.order_by(ReentryReferral.referral_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        active_only: bool = False
    ) -> List[ReentryReferral]:
        """Get referrals for an inmate."""
        query = select(ReentryReferral).where(
            ReentryReferral.inmate_id == inmate_id,
            ReentryReferral.is_deleted == False
        )

        if active_only:
            query = query.where(
                ReentryReferral.status.in_([
                    ReferralStatus.PENDING.value,
                    ReferralStatus.ACCEPTED.value,
                    ReferralStatus.IN_PROGRESS.value
                ])
            )

        query = query.order_by(ReentryReferral.referral_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[ReentryReferral]:
        """Get referrals by status."""
        query = select(ReentryReferral).where(
            ReentryReferral.status == status,
            ReentryReferral.is_deleted == False
        ).order_by(ReentryReferral.referral_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, referral: ReentryReferral) -> ReentryReferral:
        """Update a referral."""
        await self.session.flush()
        return referral

    async def soft_delete(self, referral: ReentryReferral) -> bool:
        """Soft delete a referral."""
        referral.is_deleted = True
        referral.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def count_active(self) -> int:
        """Count active referrals."""
        query = select(func.count(ReentryReferral.id)).where(
            ReentryReferral.status.in_([
                ReferralStatus.PENDING.value,
                ReferralStatus.ACCEPTED.value,
                ReferralStatus.IN_PROGRESS.value
            ]),
            ReentryReferral.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_completed_in_period(
        self,
        start_date: date,
        end_date: date
    ) -> int:
        """Count referrals completed within a date range."""
        query = select(func.count(ReentryReferral.id)).where(
            ReentryReferral.status == ReferralStatus.COMPLETED.value,
            ReentryReferral.updated_date >= start_date,
            ReentryReferral.updated_date <= end_date,
            ReentryReferral.is_deleted == False
        )

        result = await self.session.execute(query)
        return result.scalar() or 0
