"""
Dashboard Service - Aggregation queries across all modules.

Uses Redis caching with 5-minute TTL for expensive queries.
All methods return data with timestamps for cache freshness tracking.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import (
    InmateStatus, SecurityLevel, Gender,
    MovementType, MovementStatus,
    CourtType, AppearanceType,
    SentenceType,
    PetitionStatus
)
from src.modules.inmate.models import Inmate
from src.modules.housing.models import HousingUnit, Classification
from src.modules.movement.models import Movement
from src.modules.court.models import CourtCase, CourtAppearance
from src.modules.sentence.models import Sentence
from src.modules.clemency.models import ClemencyPetition
from src.modules.dashboard.dtos import (
    DashboardSummaryResponse, StatusBreakdown, SecurityBreakdown, GenderBreakdown,
    DashboardPopulationResponse, OvercrowdedUnit,
    DashboardMovementsTodayResponse, MovementTypeBreakdown,
    DashboardCourtUpcomingResponse, CourtTypeBreakdown, AppearanceTypeBreakdown,
    DashboardReleasesUpcomingResponse, ReleaseTimeframe, ReleaseTypeBreakdown,
    DashboardClemencyPendingResponse, ClemencyStatusBreakdown, OldestPendingPetition,
    DashboardAlertsResponse, AlertItem
)
from src.cache.cache_decorators import cache_result

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


class DashboardService:
    """Service for dashboard aggregation queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # Summary Endpoint
    # ========================================================================

    async def get_summary(self) -> DashboardSummaryResponse:
        """
        Get overall dashboard summary.

        Returns total inmates with breakdowns by status, security, gender,
        and capacity utilization.
        """
        # Count by status
        status_counts = {}
        for status in InmateStatus:
            query = select(func.count()).select_from(Inmate).where(
                Inmate.status == status,
                Inmate.is_deleted == False  # noqa: E712
            )
            result = await self.session.execute(query)
            status_counts[status.value] = result.scalar() or 0

        # Count by security level (active inmates only)
        security_counts = {}
        active_statuses = [InmateStatus.REMAND, InmateStatus.SENTENCED]
        for level in SecurityLevel:
            query = select(func.count()).select_from(Inmate).where(
                Inmate.security_level == level,
                Inmate.status.in_(active_statuses),
                Inmate.is_deleted == False  # noqa: E712
            )
            result = await self.session.execute(query)
            security_counts[level.value] = result.scalar() or 0

        # Count by gender (active inmates only)
        gender_counts = {}
        for gender in Gender:
            query = select(func.count()).select_from(Inmate).where(
                Inmate.gender == gender,
                Inmate.status.in_(active_statuses),
                Inmate.is_deleted == False  # noqa: E712
            )
            result = await self.session.execute(query)
            gender_counts[gender.value] = result.scalar() or 0

        # Get facility capacity
        capacity_query = select(
            func.sum(HousingUnit.capacity).label('total_capacity'),
            func.sum(HousingUnit.current_occupancy).label('total_population')
        ).where(HousingUnit.is_active == True)  # noqa: E712
        capacity_result = await self.session.execute(capacity_query)
        capacity_row = capacity_result.one()

        total_capacity = capacity_row.total_capacity or 1  # Avoid division by zero
        current_population = capacity_row.total_population or 0
        utilization = (current_population / total_capacity) * 100 if total_capacity > 0 else 0

        total_inmates = sum(status_counts.values())

        return DashboardSummaryResponse(
            total_inmates=total_inmates,
            by_status=StatusBreakdown(
                remand=status_counts.get('REMAND', 0),
                sentenced=status_counts.get('SENTENCED', 0),
                released=status_counts.get('RELEASED', 0),
                transferred=status_counts.get('TRANSFERRED', 0),
                deceased=status_counts.get('DECEASED', 0)
            ),
            by_security_level=SecurityBreakdown(
                maximum=security_counts.get('MAXIMUM', 0),
                medium=security_counts.get('MEDIUM', 0),
                minimum=security_counts.get('MINIMUM', 0)
            ),
            by_gender=GenderBreakdown(
                male=gender_counts.get('MALE', 0),
                female=gender_counts.get('FEMALE', 0)
            ),
            capacity_utilization=round(utilization, 1),
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Population Endpoint
    # ========================================================================

    async def get_population(self) -> DashboardPopulationResponse:
        """
        Get population metrics including capacity and remand ratio.

        The Bahamas targets <40% remand population.
        """
        # Get facility stats
        capacity_query = select(
            func.sum(HousingUnit.capacity).label('total_capacity'),
            func.sum(HousingUnit.current_occupancy).label('total_population')
        ).where(HousingUnit.is_active == True)  # noqa: E712
        capacity_result = await self.session.execute(capacity_query)
        capacity_row = capacity_result.one()

        total_capacity = capacity_row.total_capacity or 0
        current_population = capacity_row.total_population or 0
        available_beds = max(0, total_capacity - current_population)
        utilization = (current_population / total_capacity) * 100 if total_capacity > 0 else 0

        # Get overcrowded units
        overcrowded_query = select(HousingUnit).where(
            HousingUnit.is_active == True,  # noqa: E712
            HousingUnit.current_occupancy > HousingUnit.capacity
        ).order_by(HousingUnit.code)
        overcrowded_result = await self.session.execute(overcrowded_query)
        overcrowded_units_raw = list(overcrowded_result.scalars().all())

        overcrowded_units = []
        for unit in overcrowded_units_raw:
            over_by = unit.current_occupancy - unit.capacity
            unit_util = (unit.current_occupancy / unit.capacity) * 100 if unit.capacity > 0 else 0
            overcrowded_units.append(OvercrowdedUnit(
                id=unit.id,
                code=unit.code,
                name=unit.name,
                capacity=unit.capacity,
                current_occupancy=unit.current_occupancy,
                over_capacity_by=over_by,
                utilization_percent=round(unit_util, 1)
            ))

        # Count remand inmates
        remand_query = select(func.count()).select_from(Inmate).where(
            Inmate.status == InmateStatus.REMAND,
            Inmate.is_deleted == False  # noqa: E712
        )
        remand_result = await self.session.execute(remand_query)
        remand_count = remand_result.scalar() or 0

        # Calculate remand percentage
        remand_percentage = (remand_count / current_population) * 100 if current_population > 0 else 0
        remand_target_met = remand_percentage < 40

        return DashboardPopulationResponse(
            current_population=current_population,
            total_capacity=total_capacity,
            available_beds=available_beds,
            utilization_percent=round(utilization, 1),
            overcrowded_units=overcrowded_units,
            overcrowded_unit_count=len(overcrowded_units),
            remand_count=remand_count,
            remand_percentage=round(remand_percentage, 1),
            remand_target_met=remand_target_met,
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Movements Today Endpoint
    # ========================================================================

    async def get_movements_today(self) -> DashboardMovementsTodayResponse:
        """Get today's movement summary."""
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        # Get movements for today
        movements_query = select(Movement).where(
            Movement.scheduled_time >= start_of_day,
            Movement.scheduled_time <= end_of_day,
            Movement.is_deleted == False  # noqa: E712
        )
        movements_result = await self.session.execute(movements_query)
        movements = list(movements_result.scalars().all())

        # Count by status
        status_counts = {s.value: 0 for s in MovementStatus}
        for m in movements:
            status_counts[m.status] = status_counts.get(m.status, 0) + 1

        # Count by type
        type_counts = {t.value: 0 for t in MovementType}
        for m in movements:
            type_counts[m.movement_type] = type_counts.get(m.movement_type, 0) + 1

        return DashboardMovementsTodayResponse(
            date=datetime.utcnow(),
            total_movements=len(movements),
            scheduled=status_counts.get('SCHEDULED', 0),
            in_progress=status_counts.get('IN_PROGRESS', 0),
            completed=status_counts.get('COMPLETED', 0),
            cancelled=status_counts.get('CANCELLED', 0),
            by_type=MovementTypeBreakdown(
                internal_transfer=type_counts.get('INTERNAL_TRANSFER', 0),
                court_transport=type_counts.get('COURT_TRANSPORT', 0),
                medical_transport=type_counts.get('MEDICAL_TRANSPORT', 0),
                work_release=type_counts.get('WORK_RELEASE', 0),
                temporary_release=type_counts.get('TEMPORARY_RELEASE', 0),
                furlough=type_counts.get('FURLOUGH', 0),
                external_appointment=type_counts.get('EXTERNAL_APPOINTMENT', 0),
                release=type_counts.get('RELEASE', 0)
            ),
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Court Upcoming Endpoint
    # ========================================================================

    async def get_court_upcoming(self, days: int = 7) -> DashboardCourtUpcomingResponse:
        """Get upcoming court appearances for next N days."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        # Get upcoming appearances
        appearances_query = select(CourtAppearance).where(
            CourtAppearance.appearance_date >= now,
            CourtAppearance.appearance_date <= end_date,
            CourtAppearance.outcome == None,  # noqa: E711
            CourtAppearance.is_deleted == False  # noqa: E712
        )
        appearances_result = await self.session.execute(appearances_query)
        appearances = list(appearances_result.scalars().all())

        # Get associated court cases for court type
        case_ids = [a.court_case_id for a in appearances]
        court_type_counts = {ct.value: 0 for ct in CourtType}

        if case_ids:
            cases_query = select(CourtCase).where(CourtCase.id.in_(case_ids))
            cases_result = await self.session.execute(cases_query)
            cases = {c.id: c for c in cases_result.scalars().all()}

            for appearance in appearances:
                case = cases.get(appearance.court_case_id)
                if case:
                    court_type_counts[case.court_type] = court_type_counts.get(case.court_type, 0) + 1

        # Count by appearance type
        appearance_type_counts = {at.value: 0 for at in AppearanceType}
        for a in appearances:
            appearance_type_counts[a.appearance_type] = appearance_type_counts.get(a.appearance_type, 0) + 1

        return DashboardCourtUpcomingResponse(
            period_days=days,
            total_appearances=len(appearances),
            by_court_type=CourtTypeBreakdown(
                magistrates=court_type_counts.get('MAGISTRATES', 0),
                supreme=court_type_counts.get('SUPREME', 0),
                court_of_appeal=court_type_counts.get('COURT_OF_APPEAL', 0),
                privy_council=court_type_counts.get('PRIVY_COUNCIL', 0),
                coroners=court_type_counts.get('CORONERS', 0)
            ),
            by_appearance_type=AppearanceTypeBreakdown(
                arraignment=appearance_type_counts.get('ARRAIGNMENT', 0),
                bail_hearing=appearance_type_counts.get('BAIL_HEARING', 0),
                trial=appearance_type_counts.get('TRIAL', 0),
                sentencing=appearance_type_counts.get('SENTENCING', 0),
                appeal=appearance_type_counts.get('APPEAL', 0),
                motion=appearance_type_counts.get('MOTION', 0)
            ),
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Releases Upcoming Endpoint
    # ========================================================================

    async def get_releases_upcoming(self) -> DashboardReleasesUpcomingResponse:
        """Get upcoming releases for next 30/60/90 days."""
        today = date.today()

        def get_release_count(days: int) -> tuple:
            """Helper to count releases and by type."""
            cutoff = today + timedelta(days=days)
            return cutoff

        # Build queries for each timeframe
        async def count_releases_in_days(days: int) -> int:
            cutoff = today + timedelta(days=days)
            query = select(func.count()).select_from(Sentence).where(
                Sentence.expected_release_date != None,  # noqa: E711
                Sentence.expected_release_date >= today,
                Sentence.expected_release_date <= cutoff,
                Sentence.actual_release_date == None,  # noqa: E711
                Sentence.life_sentence == False,  # noqa: E712
                Sentence.is_death_sentence == False,  # noqa: E712
                Sentence.is_deleted == False  # noqa: E712
            )
            result = await self.session.execute(query)
            return result.scalar() or 0

        count_30 = await count_releases_in_days(30)
        count_60 = await count_releases_in_days(60)
        count_90 = await count_releases_in_days(90)

        # Get by type for next 90 days
        cutoff_90 = today + timedelta(days=90)
        type_counts = {st.value: 0 for st in SentenceType}

        sentences_query = select(Sentence).where(
            Sentence.expected_release_date != None,  # noqa: E711
            Sentence.expected_release_date >= today,
            Sentence.expected_release_date <= cutoff_90,
            Sentence.actual_release_date == None,  # noqa: E711
            Sentence.life_sentence == False,  # noqa: E712
            Sentence.is_death_sentence == False,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        )
        sentences_result = await self.session.execute(sentences_query)
        sentences = list(sentences_result.scalars().all())

        for s in sentences:
            type_counts[s.sentence_type] = type_counts.get(s.sentence_type, 0) + 1

        return DashboardReleasesUpcomingResponse(
            by_timeframe=ReleaseTimeframe(
                next_30_days=count_30,
                next_60_days=count_60,
                next_90_days=count_90
            ),
            by_type=ReleaseTypeBreakdown(
                imprisonment=type_counts.get('IMPRISONMENT', 0),
                time_served=type_counts.get('TIME_SERVED', 0),
                suspended=type_counts.get('SUSPENDED', 0),
                probation=type_counts.get('PROBATION', 0)
            ),
            total_upcoming=count_90,
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Clemency Pending Endpoint
    # ========================================================================

    async def get_clemency_pending(self) -> DashboardClemencyPendingResponse:
        """Get pending clemency petition summary."""
        # Pending statuses (not terminal)
        pending_statuses = [
            PetitionStatus.SUBMITTED.value,
            PetitionStatus.UNDER_REVIEW.value,
            PetitionStatus.COMMITTEE_SCHEDULED.value,
            PetitionStatus.AWAITING_MINISTER.value,
            PetitionStatus.GOVERNOR_GENERAL.value,
            PetitionStatus.DEFERRED.value
        ]

        # Count by status
        status_counts = {}
        for status in pending_statuses:
            query = select(func.count()).select_from(ClemencyPetition).where(
                ClemencyPetition.status == status,
                ClemencyPetition.is_deleted == False  # noqa: E712
            )
            result = await self.session.execute(query)
            status_counts[status] = result.scalar() or 0

        total_pending = sum(status_counts.values())

        # Get oldest pending petition
        oldest_query = select(ClemencyPetition).where(
            ClemencyPetition.status.in_(pending_statuses),
            ClemencyPetition.is_deleted == False  # noqa: E712
        ).order_by(ClemencyPetition.filed_date.asc()).limit(1)
        oldest_result = await self.session.execute(oldest_query)
        oldest = oldest_result.scalar_one_or_none()

        oldest_pending = None
        if oldest:
            days_pending = (date.today() - oldest.filed_date).days
            oldest_pending = OldestPendingPetition(
                id=oldest.id,
                petition_number=oldest.petition_number,
                status=oldest.status,
                filed_date=datetime.combine(oldest.filed_date, datetime.min.time()),
                days_pending=days_pending,
                petitioner_name=oldest.petitioner_name
            )

        # Calculate average days in status (simplified - would need status history for accuracy)
        avg_days = {}
        for status in pending_statuses:
            petitions_query = select(ClemencyPetition).where(
                ClemencyPetition.status == status,
                ClemencyPetition.is_deleted == False  # noqa: E712
            )
            petitions_result = await self.session.execute(petitions_query)
            petitions = list(petitions_result.scalars().all())

            if petitions:
                total_days = sum((date.today() - p.filed_date).days for p in petitions)
                avg_days[status] = round(total_days / len(petitions), 1)
            else:
                avg_days[status] = 0.0

        return DashboardClemencyPendingResponse(
            total_pending=total_pending,
            by_status=ClemencyStatusBreakdown(
                submitted=status_counts.get('SUBMITTED', 0),
                under_review=status_counts.get('UNDER_REVIEW', 0),
                committee_scheduled=status_counts.get('COMMITTEE_SCHEDULED', 0),
                awaiting_minister=status_counts.get('AWAITING_MINISTER', 0),
                governor_general=status_counts.get('GOVERNOR_GENERAL', 0),
                deferred=status_counts.get('DEFERRED', 0)
            ),
            avg_days_in_status=avg_days,
            oldest_pending=oldest_pending,
            generated_at=datetime.utcnow()
        )

    # ========================================================================
    # Alerts Endpoint
    # ========================================================================

    async def get_alerts(self) -> DashboardAlertsResponse:
        """
        Get system alerts requiring attention.

        Categories:
        - Overcrowded units
        - Overdue classifications (review date passed)
        - Missed court dates (appearance without outcome, date passed)
        - Expiring sentences with no release plan
        """
        alerts_overcrowded = []
        alerts_classification = []
        alerts_court = []
        alerts_sentence = []

        # Overcrowded units
        overcrowded_query = select(HousingUnit).where(
            HousingUnit.is_active == True,  # noqa: E712
            HousingUnit.current_occupancy > HousingUnit.capacity
        )
        overcrowded_result = await self.session.execute(overcrowded_query)
        overcrowded_units = list(overcrowded_result.scalars().all())

        for unit in overcrowded_units:
            over_by = unit.current_occupancy - unit.capacity
            alerts_overcrowded.append(AlertItem(
                id=unit.id,
                type="OVERCROWDED_UNIT",
                severity="HIGH" if over_by > 10 else "MEDIUM",
                message=f"Unit {unit.code} is {over_by} over capacity ({unit.current_occupancy}/{unit.capacity})",
                related_entity="housing_unit",
                related_id=unit.id,
                created_at=datetime.utcnow()
            ))

        # Overdue classifications (review date in the past)
        today = date.today()
        overdue_class_query = select(Classification).where(
            Classification.review_date < today,
            Classification.is_current == True,  # noqa: E712
            Classification.is_deleted == False  # noqa: E712
        ).limit(50)  # Limit to avoid huge result sets
        overdue_class_result = await self.session.execute(overdue_class_query)
        overdue_classifications = list(overdue_class_result.scalars().all())

        for classification in overdue_classifications:
            days_overdue = (today - classification.review_date).days
            alerts_classification.append(AlertItem(
                id=classification.id,
                type="OVERDUE_CLASSIFICATION",
                severity="HIGH" if days_overdue > 30 else "MEDIUM",
                message=f"Classification review overdue by {days_overdue} days",
                related_entity="inmate",
                related_id=classification.inmate_id,
                created_at=datetime.utcnow()
            ))

        # Missed court dates (appearance date in past, no outcome)
        yesterday = datetime.combine(today - timedelta(days=1), datetime.max.time())
        missed_court_query = select(CourtAppearance).where(
            CourtAppearance.appearance_date < yesterday,
            CourtAppearance.outcome == None,  # noqa: E711
            CourtAppearance.is_deleted == False  # noqa: E712
        ).limit(50)
        missed_court_result = await self.session.execute(missed_court_query)
        missed_appearances = list(missed_court_result.scalars().all())

        for appearance in missed_appearances:
            days_missed = (today - appearance.appearance_date.date()).days
            alerts_court.append(AlertItem(
                id=appearance.id,
                type="MISSED_COURT_DATE",
                severity="HIGH",
                message=f"Court appearance {days_missed} days ago without recorded outcome",
                related_entity="court_appearance",
                related_id=appearance.id,
                created_at=datetime.utcnow()
            ))

        # Expiring sentences with no release plan (releasing in 7 days, no movement scheduled)
        week_from_now = today + timedelta(days=7)
        expiring_query = select(Sentence).where(
            Sentence.expected_release_date != None,  # noqa: E711
            Sentence.expected_release_date >= today,
            Sentence.expected_release_date <= week_from_now,
            Sentence.actual_release_date == None,  # noqa: E711
            Sentence.is_deleted == False  # noqa: E712
        )
        expiring_result = await self.session.execute(expiring_query)
        expiring_sentences = list(expiring_result.scalars().all())

        for sentence in expiring_sentences:
            # Check if release movement exists
            release_movement_query = select(func.count()).select_from(Movement).where(
                Movement.inmate_id == sentence.inmate_id,
                Movement.movement_type == MovementType.RELEASE.value,
                Movement.status.in_([MovementStatus.SCHEDULED.value, MovementStatus.IN_PROGRESS.value]),
                Movement.is_deleted == False  # noqa: E712
            )
            release_result = await self.session.execute(release_movement_query)
            has_release_plan = (release_result.scalar() or 0) > 0

            if not has_release_plan:
                days_until = (sentence.expected_release_date - today).days
                alerts_sentence.append(AlertItem(
                    id=sentence.id,
                    type="EXPIRING_SENTENCE_NO_PLAN",
                    severity="HIGH" if days_until <= 3 else "MEDIUM",
                    message=f"Release in {days_until} days with no scheduled release movement",
                    related_entity="sentence",
                    related_id=sentence.id,
                    created_at=datetime.utcnow()
                ))

        # Combine all alerts
        all_alerts = alerts_overcrowded + alerts_classification + alerts_court + alerts_sentence

        return DashboardAlertsResponse(
            total_alerts=len(all_alerts),
            high_severity=sum(1 for a in all_alerts if a.severity == "HIGH"),
            medium_severity=sum(1 for a in all_alerts if a.severity == "MEDIUM"),
            low_severity=sum(1 for a in all_alerts if a.severity == "LOW"),
            overcrowded_units=alerts_overcrowded,
            overdue_classifications=alerts_classification,
            missed_court_dates=alerts_court,
            expiring_sentences_no_plan=alerts_sentence,
            generated_at=datetime.utcnow()
        )
