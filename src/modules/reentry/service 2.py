"""
Reentry Planning Service - Business logic for reentry operations.

Key features:
1. Auto-generated checklist items on plan creation
2. Readiness score calculation based on checklist completion
3. Upcoming release alerts and not-ready plan identification
4. Service referral tracking and outcome management

Standard checklist items are generated across all ChecklistType categories
to ensure comprehensive release preparation.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reentry.models import (
    ReentryPlan,
    ReentryChecklist,
    ReentryReferral
)
from src.modules.reentry.repository import (
    ReentryPlanRepository,
    ReentryChecklistRepository,
    ReentryReferralRepository
)
from src.modules.reentry.dtos import (
    ReentryPlanCreate,
    ReentryPlanUpdate,
    ReentryPlanResponse,
    ReentryPlanSummary,
    ReentryChecklistCreate,
    ReentryChecklistResponse,
    ReentryChecklistListResponse,
    ReentryReferralCreate,
    ReentryReferralStatusUpdate,
    ReentryReferralResponse,
    UpcomingReleaseItem,
    UpcomingReleasesResponse,
    NotReadyPlanItem,
    NotReadyPlansResponse,
    ReentryStatistics
)
from src.common.enums import (
    PlanStatus, HousingPlan, ChecklistType,
    ServiceType, ReferralStatus
)


# Standard checklist items generated for each new plan
STANDARD_CHECKLIST_ITEMS = [
    # Documentation
    (ChecklistType.DOCUMENTATION, "Obtain or verify government-issued ID"),
    (ChecklistType.DOCUMENTATION, "Obtain or verify birth certificate"),
    (ChecklistType.DOCUMENTATION, "Obtain or verify NIB card"),
    (ChecklistType.DOCUMENTATION, "Collect any court documents needed"),
    # Housing
    (ChecklistType.HOUSING, "Confirm post-release housing arrangement"),
    (ChecklistType.HOUSING, "Verify housing address and contact"),
    (ChecklistType.HOUSING, "Coordinate move-in date if needed"),
    # Employment
    (ChecklistType.EMPLOYMENT, "Develop job search strategy"),
    (ChecklistType.EMPLOYMENT, "Update or create resume"),
    (ChecklistType.EMPLOYMENT, "Identify potential employers"),
    # Healthcare
    (ChecklistType.HEALTHCARE, "Schedule medical check-up before release"),
    (ChecklistType.HEALTHCARE, "Arrange prescription medications"),
    (ChecklistType.HEALTHCARE, "Identify community healthcare provider"),
    # Family
    (ChecklistType.FAMILY, "Notify family of expected release date"),
    (ChecklistType.FAMILY, "Arrange family visit if appropriate"),
    (ChecklistType.FAMILY, "Discuss reintegration plan with family"),
    # Financial
    (ChecklistType.FINANCIAL, "Review savings account balance"),
    (ChecklistType.FINANCIAL, "Arrange access to funds post-release"),
    (ChecklistType.FINANCIAL, "Develop initial budget plan"),
    # Supervision
    (ChecklistType.SUPERVISION, "Review any post-release reporting requirements"),
    (ChecklistType.SUPERVISION, "Confirm probation officer if applicable"),
    (ChecklistType.SUPERVISION, "Understand conditions of release"),
]

# Critical items that must be completed for readiness
CRITICAL_ITEMS = [
    "Obtain or verify government-issued ID",
    "Obtain or verify NIB card",
    "Confirm post-release housing arrangement",
]


class ReentryService:
    """Service for reentry planning business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.plan_repo = ReentryPlanRepository(session)
        self.checklist_repo = ReentryChecklistRepository(session)
        self.referral_repo = ReentryReferralRepository(session)

    # ========================================================================
    # Plan Operations
    # ========================================================================

    async def create_plan(
        self,
        data: ReentryPlanCreate,
        created_by: Optional[UUID] = None
    ) -> ReentryPlan:
        """
        Create a new reentry plan with auto-generated checklist items.

        Validates that inmate doesn't have an existing active plan.
        """
        # Check for existing active plan
        existing = await self.plan_repo.get_active_plan(data.inmate_id)
        if existing:
            raise ValueError(
                f"Inmate already has an active reentry plan (status: {existing.status})"
            )

        # Create the plan
        plan = ReentryPlan(
            inmate_id=data.inmate_id,
            expected_release_date=data.expected_release_date,
            status=PlanStatus.DRAFT.value,
            housing_plan=data.housing_plan.value,
            housing_address=data.housing_address,
            employment_plan=data.employment_plan,
            has_id_documents=data.has_id_documents,
            has_birth_certificate=data.has_birth_certificate,
            has_nib_card=data.has_nib_card,
            transportation_arranged=data.transportation_arranged,
            family_contact_name=data.family_contact_name,
            family_contact_phone=data.family_contact_phone,
            support_services=data.support_services,
            risk_factors=data.risk_factors,
            notes=data.notes,
            created_by=created_by
        )

        plan = await self.plan_repo.create(plan)

        # Auto-generate standard checklist items
        checklist_items = []
        for item_type, description in STANDARD_CHECKLIST_ITEMS:
            item = ReentryChecklist(
                reentry_plan_id=plan.id,
                item_type=item_type.value,
                description=description,
                is_completed=False
            )
            checklist_items.append(item)

        await self.checklist_repo.create_many(checklist_items)

        # Refresh to get checklist items
        return await self.plan_repo.get_by_id(plan.id)

    async def get_plan(
        self,
        plan_id: UUID,
        include_referrals: bool = False
    ) -> Optional[ReentryPlan]:
        """Get plan by ID with readiness calculations."""
        return await self.plan_repo.get_by_id(
            plan_id,
            include_checklist=True,
            include_referrals=include_referrals
        )

    async def get_inmate_plan(self, inmate_id: UUID) -> Optional[ReentryPlan]:
        """Get the current active plan for an inmate."""
        return await self.plan_repo.get_active_plan(inmate_id)

    async def get_inmate_plans(
        self,
        inmate_id: UUID,
        include_completed: bool = True
    ) -> List[ReentryPlan]:
        """Get all plans for an inmate."""
        return await self.plan_repo.get_by_inmate(inmate_id, include_completed)

    async def update_plan(
        self,
        plan_id: UUID,
        data: ReentryPlanUpdate
    ) -> Optional[ReentryPlan]:
        """Update plan details."""
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == 'housing_plan' and value:
                setattr(plan, field, value.value)
            else:
                setattr(plan, field, value)

        return await self.plan_repo.update(plan)

    async def update_plan_status(
        self,
        plan_id: UUID,
        status: PlanStatus,
        notes: Optional[str] = None
    ) -> ReentryPlan:
        """Update plan status with validation."""
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        # Validate status transition
        current = PlanStatus(plan.status)
        valid_transitions = {
            PlanStatus.DRAFT: [PlanStatus.IN_PROGRESS],
            PlanStatus.IN_PROGRESS: [PlanStatus.READY, PlanStatus.DRAFT],
            PlanStatus.READY: [PlanStatus.COMPLETED, PlanStatus.IN_PROGRESS],
            PlanStatus.COMPLETED: []  # Terminal state
        }

        if status not in valid_transitions.get(current, []):
            raise ValueError(
                f"Invalid status transition: {current.value} → {status.value}"
            )

        # For READY status, verify readiness score
        if status == PlanStatus.READY:
            score = self.calculate_readiness_score(plan)
            if score < 100:
                raise ValueError(
                    f"Cannot mark as READY. Readiness score is {score}%. "
                    f"All checklist items must be complete."
                )

        plan.status = status.value
        if notes:
            plan.notes = f"{plan.notes or ''}\n[{status.value}] {date.today()}: {notes}".strip()

        return await self.plan_repo.update(plan)

    async def approve_plan(
        self,
        plan_id: UUID,
        approved_by: Optional[UUID] = None
    ) -> ReentryPlan:
        """
        Approve a plan as READY for release.

        Validates all checklist items are complete.
        """
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if plan.status != PlanStatus.IN_PROGRESS.value:
            raise ValueError(
                f"Can only approve IN_PROGRESS plans. Current status: {plan.status}"
            )

        # Check readiness
        score = self.calculate_readiness_score(plan)
        if score < 100:
            # Get incomplete critical items
            missing_critical = self.get_missing_critical_items(plan)
            raise ValueError(
                f"Plan not ready for approval. Score: {score}%. "
                f"Missing critical items: {', '.join(missing_critical)}"
            )

        plan.status = PlanStatus.READY.value
        plan.approved_by = approved_by
        plan.approval_date = date.today()

        return await self.plan_repo.update(plan)

    async def complete_plan(
        self,
        plan_id: UUID,
        notes: Optional[str] = None
    ) -> ReentryPlan:
        """Mark plan as COMPLETED (inmate released)."""
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if plan.status != PlanStatus.READY.value:
            raise ValueError("Can only complete READY plans")

        plan.status = PlanStatus.COMPLETED.value
        if notes:
            plan.notes = f"{plan.notes or ''}\n[COMPLETED] {date.today()}: {notes}".strip()

        return await self.plan_repo.update(plan)

    async def delete_plan(self, plan_id: UUID) -> bool:
        """Soft delete a plan."""
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            return False

        if plan.status == PlanStatus.COMPLETED.value:
            raise ValueError("Cannot delete completed plans")

        return await self.plan_repo.soft_delete(plan)

    # ========================================================================
    # Readiness Calculation
    # ========================================================================

    def calculate_readiness_score(self, plan: ReentryPlan) -> int:
        """
        Calculate readiness score as percentage of completed checklist items.

        Returns 0-100 representing percentage complete.
        """
        if not plan.checklist_items:
            return 0

        total = len(plan.checklist_items)
        completed = sum(1 for item in plan.checklist_items if item.is_completed)

        if total == 0:
            return 0

        return int((completed / total) * 100)

    def get_missing_critical_items(self, plan: ReentryPlan) -> List[str]:
        """Get list of incomplete critical items."""
        if not plan.checklist_items:
            return CRITICAL_ITEMS.copy()

        missing = []
        for critical in CRITICAL_ITEMS:
            item = next(
                (i for i in plan.checklist_items if i.description == critical),
                None
            )
            if not item or not item.is_completed:
                missing.append(critical)

        return missing

    def get_incomplete_items(self, plan: ReentryPlan) -> List[str]:
        """Get list of all incomplete item descriptions."""
        if not plan.checklist_items:
            return []

        return [
            item.description
            for item in plan.checklist_items
            if not item.is_completed
        ]

    # ========================================================================
    # Checklist Operations
    # ========================================================================

    async def add_checklist_item(
        self,
        plan_id: UUID,
        data: ReentryChecklistCreate
    ) -> ReentryChecklist:
        """Add a custom checklist item to a plan."""
        plan = await self.plan_repo.get_by_id(plan_id, include_checklist=False)
        if not plan:
            raise ValueError("Plan not found")

        if plan.status == PlanStatus.COMPLETED.value:
            raise ValueError("Cannot add items to completed plans")

        item = ReentryChecklist(
            reentry_plan_id=plan_id,
            item_type=data.item_type.value,
            description=data.description,
            is_completed=False,
            due_date=data.due_date,
            notes=data.notes
        )

        return await self.checklist_repo.create(item)

    async def get_checklist_item(self, item_id: UUID) -> Optional[ReentryChecklist]:
        """Get a checklist item by ID."""
        return await self.checklist_repo.get_by_id(item_id)

    async def get_plan_checklist(
        self,
        plan_id: UUID,
        completed_only: bool = False,
        incomplete_only: bool = False
    ) -> List[ReentryChecklist]:
        """Get checklist items for a plan."""
        return await self.checklist_repo.get_by_plan(
            plan_id, completed_only, incomplete_only
        )

    async def complete_checklist_item(
        self,
        item_id: UUID,
        completed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> ReentryChecklist:
        """Mark a checklist item as complete."""
        item = await self.checklist_repo.get_by_id(item_id)
        if not item:
            raise ValueError("Checklist item not found")

        if item.is_completed:
            raise ValueError("Item is already completed")

        item.is_completed = True
        item.completed_date = date.today()
        item.completed_by = completed_by
        if notes:
            item.notes = f"{item.notes or ''}\n[COMPLETED] {notes}".strip()

        return await self.checklist_repo.update(item)

    async def uncomplete_checklist_item(
        self,
        item_id: UUID,
        reason: str
    ) -> ReentryChecklist:
        """Mark a completed item as incomplete (undo)."""
        item = await self.checklist_repo.get_by_id(item_id)
        if not item:
            raise ValueError("Checklist item not found")

        if not item.is_completed:
            raise ValueError("Item is not completed")

        item.is_completed = False
        item.completed_date = None
        item.completed_by = None
        item.notes = f"{item.notes or ''}\n[UNCOMPLETED] {date.today()}: {reason}".strip()

        return await self.checklist_repo.update(item)

    async def delete_checklist_item(self, item_id: UUID) -> bool:
        """Delete a checklist item."""
        item = await self.checklist_repo.get_by_id(item_id)
        if not item:
            return False

        return await self.checklist_repo.delete(item)

    # ========================================================================
    # Referral Operations
    # ========================================================================

    async def create_referral(
        self,
        data: ReentryReferralCreate,
        created_by: Optional[UUID] = None
    ) -> ReentryReferral:
        """Create a service referral."""
        # Verify plan exists
        plan = await self.plan_repo.get_by_id(data.reentry_plan_id, include_checklist=False)
        if not plan:
            raise ValueError("Reentry plan not found")

        referral = ReentryReferral(
            reentry_plan_id=data.reentry_plan_id,
            inmate_id=data.inmate_id,
            service_type=data.service_type.value,
            provider_name=data.provider_name,
            provider_contact=data.provider_contact,
            referral_date=data.referral_date,
            status=ReferralStatus.PENDING.value,
            appointment_date=data.appointment_date,
            notes=data.notes,
            created_by=created_by
        )

        return await self.referral_repo.create(referral)

    async def get_referral(self, referral_id: UUID) -> Optional[ReentryReferral]:
        """Get referral by ID."""
        return await self.referral_repo.get_by_id(referral_id)

    async def get_plan_referrals(
        self,
        plan_id: UUID,
        active_only: bool = False
    ) -> List[ReentryReferral]:
        """Get referrals for a plan."""
        return await self.referral_repo.get_by_plan(plan_id, active_only)

    async def update_referral_status(
        self,
        referral_id: UUID,
        data: ReentryReferralStatusUpdate
    ) -> ReentryReferral:
        """Update referral status."""
        referral = await self.referral_repo.get_by_id(referral_id)
        if not referral:
            raise ValueError("Referral not found")

        # Validate status transition
        current = ReferralStatus(referral.status)
        valid_transitions = {
            ReferralStatus.PENDING: [
                ReferralStatus.ACCEPTED,
                ReferralStatus.DECLINED
            ],
            ReferralStatus.ACCEPTED: [
                ReferralStatus.IN_PROGRESS,
                ReferralStatus.DECLINED
            ],
            ReferralStatus.IN_PROGRESS: [
                ReferralStatus.COMPLETED,
                ReferralStatus.DECLINED
            ],
            ReferralStatus.COMPLETED: [],
            ReferralStatus.DECLINED: []
        }

        if data.status not in valid_transitions.get(current, []):
            raise ValueError(
                f"Invalid status transition: {current.value} → {data.status.value}"
            )

        referral.status = data.status.value
        if data.outcome:
            referral.outcome = data.outcome
        if data.notes:
            referral.notes = f"{referral.notes or ''}\n[{data.status.value}] {data.notes}".strip()

        return await self.referral_repo.update(referral)

    async def delete_referral(self, referral_id: UUID) -> bool:
        """Soft delete a referral."""
        referral = await self.referral_repo.get_by_id(referral_id)
        if not referral:
            return False

        return await self.referral_repo.soft_delete(referral)

    # ========================================================================
    # Reports and Queries
    # ========================================================================

    async def get_plans_for_upcoming_releases(
        self,
        days: int = 90
    ) -> UpcomingReleasesResponse:
        """Get plans with releases in the next N days."""
        plans = await self.plan_repo.get_upcoming_releases(days)

        items = []
        ready_count = 0
        not_ready_count = 0

        for plan in plans:
            score = self.calculate_readiness_score(plan)
            is_ready = plan.status == PlanStatus.READY.value

            if is_ready:
                ready_count += 1
            else:
                not_ready_count += 1

            items.append(UpcomingReleaseItem(
                plan_id=plan.id,
                inmate_id=plan.inmate_id,
                inmate_name=plan.inmate.full_name if plan.inmate else None,
                booking_number=plan.inmate.booking_number if plan.inmate else None,
                expected_release_date=plan.expected_release_date,
                days_until_release=plan.days_until_release,
                status=plan.status,
                readiness_score=score,
                housing_plan=plan.housing_plan,
                is_ready=is_ready
            ))

        return UpcomingReleasesResponse(
            items=items,
            total=len(items),
            ready_count=ready_count,
            not_ready_count=not_ready_count
        )

    async def get_not_ready_plans(
        self,
        days_threshold: int = 30
    ) -> NotReadyPlansResponse:
        """Get plans that are not ready and releasing within threshold days."""
        plans = await self.plan_repo.get_not_ready_plans(days_threshold)

        items = []
        for plan in plans:
            score = self.calculate_readiness_score(plan)
            incomplete = self.get_incomplete_items(plan)
            missing_critical = self.get_missing_critical_items(plan)

            items.append(NotReadyPlanItem(
                plan_id=plan.id,
                inmate_id=plan.inmate_id,
                inmate_name=plan.inmate.full_name if plan.inmate else None,
                expected_release_date=plan.expected_release_date,
                days_until_release=plan.days_until_release,
                readiness_score=score,
                incomplete_items=incomplete,
                missing_critical=missing_critical
            ))

        return NotReadyPlansResponse(
            items=items,
            total=len(items)
        )

    async def get_inmate_reentry_summary(
        self,
        inmate_id: UUID
    ) -> ReentryPlanSummary:
        """Get reentry summary for an inmate."""
        plan = await self.plan_repo.get_active_plan(inmate_id)

        if not plan:
            return ReentryPlanSummary(
                plan_id=None,
                status=None,
                expected_release_date=None,
                days_until_release=None,
                readiness_score=None,
                housing_plan=None,
                has_critical_items=False,
                incomplete_items=0,
                active_referrals=0
            )

        score = self.calculate_readiness_score(plan)
        missing_critical = self.get_missing_critical_items(plan)
        incomplete = [i for i in plan.checklist_items if not i.is_completed]
        active_referrals = await self.referral_repo.get_by_plan(plan.id, active_only=True)

        return ReentryPlanSummary(
            plan_id=plan.id,
            status=plan.status,
            expected_release_date=plan.expected_release_date,
            days_until_release=plan.days_until_release,
            readiness_score=score,
            housing_plan=plan.housing_plan,
            has_critical_items=len(missing_critical) == 0,
            incomplete_items=len(incomplete),
            active_referrals=len(active_referrals)
        )

    async def get_statistics(self) -> ReentryStatistics:
        """Get overall reentry planning statistics."""
        status_counts = await self.plan_repo.count_by_status()
        releases_30 = await self.plan_repo.count_upcoming_releases(30)
        releases_90 = await self.plan_repo.count_upcoming_releases(90)
        active_referrals = await self.referral_repo.count_active()

        # Calculate completed referrals this month
        today = date.today()
        month_start = today.replace(day=1)
        completed_referrals = await self.referral_repo.count_completed_in_period(
            month_start, today
        )

        # Get all active plans for average readiness
        active_plans = await self.plan_repo.get_all_active()
        total_active = len(active_plans)

        if total_active > 0:
            scores = [self.calculate_readiness_score(p) for p in active_plans]
            avg_score = sum(scores) / len(scores)
            below_50 = sum(1 for s in scores if s < 50)
        else:
            avg_score = 0.0
            below_50 = 0

        return ReentryStatistics(
            total_active_plans=total_active,
            draft_plans=status_counts.get(PlanStatus.DRAFT.value, 0),
            in_progress_plans=status_counts.get(PlanStatus.IN_PROGRESS.value, 0),
            ready_plans=status_counts.get(PlanStatus.READY.value, 0),
            releases_next_30_days=releases_30,
            releases_next_90_days=releases_90,
            average_readiness_score=round(avg_score, 1),
            plans_below_50_percent=below_50,
            active_referrals=active_referrals,
            completed_referrals_this_month=completed_referrals
        )
