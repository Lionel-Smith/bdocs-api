"""
Sentence Service - Business logic for sentence management.

Key features:
- Sentence CRUD operations
- Release date calculation (Bahamian 1/3 remission rule)
- Adjustment tracking
- Releasing soon queries
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import SentenceType, AdjustmentType
from src.modules.sentence.models import Sentence, SentenceAdjustment
from src.modules.sentence.repository import SentenceRepository, SentenceAdjustmentRepository
from src.modules.sentence.dtos import (
    SentenceCreate,
    SentenceUpdate,
    SentenceResponse,
    SentenceListResponse,
    SentenceAdjustmentCreate,
    SentenceAdjustmentResponse,
    SentenceAdjustmentListResponse,
    ReleaseCalculation,
    ReleasingSoonResponse,
    InmateSentenceSummary,
)


# ============================================================================
# Constants
# ============================================================================

# Bahamas allows up to 1/3 remission for good behavior
MAX_REMISSION_FRACTION = 1 / 3

# Days per month for calculations
DAYS_PER_MONTH = 30


# ============================================================================
# Custom Exceptions
# ============================================================================

class SentenceNotFoundError(Exception):
    """Raised when a sentence is not found."""
    pass


class AdjustmentNotFoundError(Exception):
    """Raised when an adjustment is not found."""
    pass


class InvalidSentenceError(Exception):
    """Raised for invalid sentence operations."""
    pass


# ============================================================================
# Sentence Service
# ============================================================================

class SentenceService:
    """Service layer for sentence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sentence_repo = SentenceRepository(session)
        self.adjustment_repo = SentenceAdjustmentRepository(session)

    # ------------------------------------------------------------------------
    # Release Date Calculation
    # ------------------------------------------------------------------------

    def calculate_expected_release(
        self,
        sentence: Sentence,
        total_adjustment_days: int = 0
    ) -> ReleaseCalculation:
        """
        Calculate expected release date for a sentence.

        Bahamas remission rules:
        - Up to 1/3 of sentence may be remitted for good behavior
        - Pre-trial detention is credited as time served
        - Good time credits accumulate daily
        - Clemency may further reduce sentence

        For life/death sentences, release date is not calculable.
        """
        # Handle special sentence types
        if sentence.is_death_sentence:
            return ReleaseCalculation(
                sentence_id=sentence.id,
                inmate_id=sentence.inmate_id,
                sentence_type=SentenceType(sentence.sentence_type),
                original_term_months=None,
                life_sentence=False,
                is_death_sentence=True,
                start_date=sentence.start_date,
                time_served_days=sentence.time_served_days,
                good_time_days=sentence.good_time_days,
                adjustment_days=total_adjustment_days,
                total_credits=sentence.time_served_days + sentence.good_time_days + total_adjustment_days,
                eligible_remission_days=0,
                max_remission_days=0,
                original_release_date=None,
                expected_release_date=None,
                days_remaining=None,
                is_eligible_for_release=False,
                release_notes="Death sentence - release date not applicable"
            )

        if sentence.life_sentence:
            min_term = sentence.minimum_term_months
            if min_term:
                min_date = sentence.start_date + timedelta(days=min_term * DAYS_PER_MONTH)
                notes = f"Life sentence with minimum term of {min_term} months"
            else:
                min_date = None
                notes = "Life sentence - release date not determinable"

            return ReleaseCalculation(
                sentence_id=sentence.id,
                inmate_id=sentence.inmate_id,
                sentence_type=SentenceType(sentence.sentence_type),
                original_term_months=sentence.original_term_months,
                life_sentence=True,
                is_death_sentence=False,
                start_date=sentence.start_date,
                time_served_days=sentence.time_served_days,
                good_time_days=sentence.good_time_days,
                adjustment_days=total_adjustment_days,
                total_credits=sentence.time_served_days + sentence.good_time_days + total_adjustment_days,
                eligible_remission_days=0,
                max_remission_days=0,
                original_release_date=min_date,
                expected_release_date=min_date,
                days_remaining=None if not min_date else max(0, (min_date - date.today()).days),
                is_eligible_for_release=False,
                release_notes=notes
            )

        # Handle non-custodial sentences
        if sentence.sentence_type in [
            SentenceType.SUSPENDED.value,
            SentenceType.PROBATION.value,
            SentenceType.FINE.value,
            SentenceType.TIME_SERVED.value
        ]:
            return ReleaseCalculation(
                sentence_id=sentence.id,
                inmate_id=sentence.inmate_id,
                sentence_type=SentenceType(sentence.sentence_type),
                original_term_months=sentence.original_term_months,
                life_sentence=False,
                is_death_sentence=False,
                start_date=sentence.start_date,
                time_served_days=sentence.time_served_days,
                good_time_days=0,
                adjustment_days=0,
                total_credits=0,
                eligible_remission_days=0,
                max_remission_days=0,
                original_release_date=sentence.start_date,
                expected_release_date=sentence.start_date,
                days_remaining=0,
                is_eligible_for_release=True,
                release_notes=f"{sentence.sentence_type} - no custody required"
            )

        # Calculate for fixed-term imprisonment
        if not sentence.original_term_months:
            return ReleaseCalculation(
                sentence_id=sentence.id,
                inmate_id=sentence.inmate_id,
                sentence_type=SentenceType(sentence.sentence_type),
                original_term_months=None,
                life_sentence=False,
                is_death_sentence=False,
                start_date=sentence.start_date,
                time_served_days=sentence.time_served_days,
                good_time_days=sentence.good_time_days,
                adjustment_days=total_adjustment_days,
                total_credits=0,
                eligible_remission_days=0,
                max_remission_days=0,
                original_release_date=None,
                expected_release_date=None,
                days_remaining=None,
                is_eligible_for_release=False,
                release_notes="No term specified - cannot calculate release"
            )

        # Calculate original sentence in days
        original_days = sentence.original_term_months * DAYS_PER_MONTH

        # Calculate maximum remission (1/3 of sentence)
        max_remission = int(original_days * MAX_REMISSION_FRACTION)

        # Calculate total credits
        total_credits = (
            sentence.time_served_days +
            sentence.good_time_days +
            total_adjustment_days
        )

        # Cap at maximum remission
        eligible_remission = min(total_credits, max_remission)

        # Calculate dates
        original_release = sentence.start_date + timedelta(days=original_days)
        expected_release = sentence.start_date + timedelta(days=original_days - eligible_remission)

        # Ensure release date is not in the past
        today = date.today()
        if expected_release < today:
            days_remaining = 0
            is_eligible = True
            notes = "Eligible for immediate release"
        else:
            days_remaining = (expected_release - today).days
            is_eligible = days_remaining <= 0
            notes = f"Expected release in {days_remaining} days"

        return ReleaseCalculation(
            sentence_id=sentence.id,
            inmate_id=sentence.inmate_id,
            sentence_type=SentenceType(sentence.sentence_type),
            original_term_months=sentence.original_term_months,
            life_sentence=False,
            is_death_sentence=False,
            start_date=sentence.start_date,
            time_served_days=sentence.time_served_days,
            good_time_days=sentence.good_time_days,
            adjustment_days=total_adjustment_days,
            total_credits=total_credits,
            eligible_remission_days=eligible_remission,
            max_remission_days=max_remission,
            original_release_date=original_release,
            expected_release_date=expected_release,
            days_remaining=days_remaining,
            is_eligible_for_release=is_eligible,
            release_notes=notes
        )

    async def _update_expected_release(self, sentence: Sentence) -> None:
        """Update the expected release date for a sentence."""
        total_adjustments = await self.adjustment_repo.get_total_adjustment_days(sentence.id)
        calc = self.calculate_expected_release(sentence, total_adjustments)
        sentence.expected_release_date = calc.expected_release_date

    # ------------------------------------------------------------------------
    # Sentence CRUD Operations
    # ------------------------------------------------------------------------

    async def create_sentence(
        self,
        data: SentenceCreate,
        created_by: Optional[UUID] = None
    ) -> SentenceResponse:
        """Create a new sentence."""
        sentence = Sentence(
            inmate_id=data.inmate_id,
            court_case_id=data.court_case_id,
            sentence_date=data.sentence_date,
            sentence_type=data.sentence_type.value,
            original_term_months=data.original_term_months,
            life_sentence=data.life_sentence,
            is_death_sentence=data.is_death_sentence,
            minimum_term_months=data.minimum_term_months,
            start_date=data.start_date,
            time_served_days=data.time_served_days,
            sentencing_judge=data.sentencing_judge,
            notes=data.notes,
            created_by=created_by,
            inserted_by=str(created_by) if created_by else 'system'
        )

        # Calculate initial expected release date
        calc = self.calculate_expected_release(sentence, 0)
        sentence.expected_release_date = calc.expected_release_date

        created = await self.sentence_repo.create(sentence)
        response = SentenceResponse.model_validate(created)
        response.total_adjustment_days = 0
        response.days_remaining = calc.days_remaining
        return response

    async def get_sentence(self, sentence_id: UUID) -> SentenceResponse:
        """Get a sentence by ID."""
        sentence = await self.sentence_repo.get_by_id(sentence_id)
        if not sentence or sentence.is_deleted:
            raise SentenceNotFoundError(f"Sentence {sentence_id} not found")

        total_adjustments = await self.adjustment_repo.get_total_adjustment_days(sentence_id)
        calc = self.calculate_expected_release(sentence, total_adjustments)

        response = SentenceResponse.model_validate(sentence)
        response.total_adjustment_days = total_adjustments
        response.days_remaining = calc.days_remaining
        return response

    async def update_sentence(
        self,
        sentence_id: UUID,
        data: SentenceUpdate,
        updated_by: Optional[str] = None
    ) -> SentenceResponse:
        """Update a sentence."""
        sentence = await self.sentence_repo.get_by_id(sentence_id)
        if not sentence or sentence.is_deleted:
            raise SentenceNotFoundError(f"Sentence {sentence_id} not found")

        # Apply updates
        if data.original_term_months is not None:
            sentence.original_term_months = data.original_term_months
        if data.minimum_term_months is not None:
            sentence.minimum_term_months = data.minimum_term_months
        if data.start_date is not None:
            sentence.start_date = data.start_date
        if data.time_served_days is not None:
            sentence.time_served_days = data.time_served_days
        if data.good_time_days is not None:
            sentence.good_time_days = data.good_time_days
        if data.sentencing_judge is not None:
            sentence.sentencing_judge = data.sentencing_judge
        if data.actual_release_date is not None:
            sentence.actual_release_date = data.actual_release_date
        if data.notes is not None:
            sentence.notes = data.notes

        sentence.updated_by = updated_by
        sentence.updated_date = datetime.utcnow()

        # Recalculate expected release
        await self._update_expected_release(sentence)

        updated = await self.sentence_repo.update(sentence)

        total_adjustments = await self.adjustment_repo.get_total_adjustment_days(sentence_id)
        calc = self.calculate_expected_release(updated, total_adjustments)

        response = SentenceResponse.model_validate(updated)
        response.total_adjustment_days = total_adjustments
        response.days_remaining = calc.days_remaining
        return response

    async def get_sentences_by_inmate(self, inmate_id: UUID) -> SentenceListResponse:
        """Get all sentences for an inmate."""
        sentences = await self.sentence_repo.get_by_inmate(inmate_id)
        items = []
        for s in sentences:
            total_adj = await self.adjustment_repo.get_total_adjustment_days(s.id)
            calc = self.calculate_expected_release(s, total_adj)
            response = SentenceResponse.model_validate(s)
            response.total_adjustment_days = total_adj
            response.days_remaining = calc.days_remaining
            items.append(response)

        return SentenceListResponse(items=items, total=len(items))

    async def get_current_sentence(self, inmate_id: UUID) -> Optional[SentenceResponse]:
        """Get the current active sentence for an inmate."""
        sentence = await self.sentence_repo.get_current_sentence(inmate_id)
        if not sentence:
            return None

        total_adjustments = await self.adjustment_repo.get_total_adjustment_days(sentence.id)
        calc = self.calculate_expected_release(sentence, total_adjustments)

        response = SentenceResponse.model_validate(sentence)
        response.total_adjustment_days = total_adjustments
        response.days_remaining = calc.days_remaining
        return response

    async def get_all_sentences(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> SentenceListResponse:
        """Get all sentences with pagination."""
        sentences = await self.sentence_repo.get_all(skip=skip, limit=limit)
        items = []
        for s in sentences:
            total_adj = await self.adjustment_repo.get_total_adjustment_days(s.id)
            calc = self.calculate_expected_release(s, total_adj)
            response = SentenceResponse.model_validate(s)
            response.total_adjustment_days = total_adj
            response.days_remaining = calc.days_remaining
            items.append(response)

        return SentenceListResponse(items=items, total=len(items))

    # ------------------------------------------------------------------------
    # Adjustment Operations
    # ------------------------------------------------------------------------

    async def create_adjustment(
        self,
        sentence_id: UUID,
        data: SentenceAdjustmentCreate,
        approved_by: Optional[UUID] = None
    ) -> SentenceAdjustmentResponse:
        """Create a sentence adjustment."""
        sentence = await self.sentence_repo.get_by_id(sentence_id)
        if not sentence or sentence.is_deleted:
            raise SentenceNotFoundError(f"Sentence {sentence_id} not found")

        adjustment = SentenceAdjustment(
            sentence_id=sentence_id,
            adjustment_type=data.adjustment_type.value,
            days=data.days,
            effective_date=data.effective_date,
            reason=data.reason,
            document_reference=data.document_reference,
            approved_by=approved_by,
            inserted_by=str(approved_by) if approved_by else 'system'
        )

        created = await self.adjustment_repo.create(adjustment)

        # Update sentence good_time_days if it's a good time adjustment
        if data.adjustment_type == AdjustmentType.GOOD_TIME:
            sentence.good_time_days += data.days
            await self.sentence_repo.update(sentence)

        # Recalculate expected release
        await self._update_expected_release(sentence)
        await self.sentence_repo.update(sentence)

        return SentenceAdjustmentResponse.model_validate(created)

    async def get_adjustments(
        self,
        sentence_id: UUID
    ) -> SentenceAdjustmentListResponse:
        """Get all adjustments for a sentence."""
        sentence = await self.sentence_repo.get_by_id(sentence_id)
        if not sentence or sentence.is_deleted:
            raise SentenceNotFoundError(f"Sentence {sentence_id} not found")

        adjustments = await self.adjustment_repo.get_by_sentence(sentence_id)
        total_days = sum(a.days for a in adjustments)

        return SentenceAdjustmentListResponse(
            items=[SentenceAdjustmentResponse.model_validate(a) for a in adjustments],
            total=len(adjustments),
            total_days_adjusted=total_days
        )

    # ------------------------------------------------------------------------
    # Query Operations
    # ------------------------------------------------------------------------

    async def get_releasing_soon(self, days_ahead: int = 30) -> ReleasingSoonResponse:
        """Get sentences with expected release within specified days."""
        sentences = await self.sentence_repo.get_releasing_soon(days_ahead)
        items = []
        for s in sentences:
            total_adj = await self.adjustment_repo.get_total_adjustment_days(s.id)
            calc = self.calculate_expected_release(s, total_adj)
            response = SentenceResponse.model_validate(s)
            response.total_adjustment_days = total_adj
            response.days_remaining = calc.days_remaining
            items.append(response)

        return ReleasingSoonResponse(
            items=items,
            total=len(items),
            days_ahead=days_ahead,
            cutoff_date=date.today() + timedelta(days=days_ahead)
        )

    async def calculate_release(self, sentence_id: UUID) -> ReleaseCalculation:
        """Calculate release date for a sentence."""
        sentence = await self.sentence_repo.get_by_id(sentence_id)
        if not sentence or sentence.is_deleted:
            raise SentenceNotFoundError(f"Sentence {sentence_id} not found")

        total_adjustments = await self.adjustment_repo.get_total_adjustment_days(sentence_id)
        return self.calculate_expected_release(sentence, total_adjustments)

    # ------------------------------------------------------------------------
    # Summary Operations
    # ------------------------------------------------------------------------

    async def get_inmate_sentence_summary(
        self,
        inmate_id: UUID
    ) -> InmateSentenceSummary:
        """Get complete sentence summary for an inmate."""
        sentences = await self.sentence_repo.get_by_inmate(inmate_id)
        life_death = await self.sentence_repo.has_life_or_death_sentence(inmate_id)

        items = []
        total_months = 0
        earliest_release = None
        active_count = 0

        for s in sentences:
            total_adj = await self.adjustment_repo.get_total_adjustment_days(s.id)
            calc = self.calculate_expected_release(s, total_adj)
            response = SentenceResponse.model_validate(s)
            response.total_adjustment_days = total_adj
            response.days_remaining = calc.days_remaining
            items.append(response)

            if s.actual_release_date is None:
                active_count += 1

            if s.original_term_months:
                total_months += s.original_term_months

            if calc.expected_release_date:
                if earliest_release is None or calc.expected_release_date < earliest_release:
                    earliest_release = calc.expected_release_date

        return InmateSentenceSummary(
            inmate_id=inmate_id,
            total_sentences=len(sentences),
            active_sentences=active_count,
            total_term_months=total_months if total_months > 0 else None,
            has_life_sentence=life_death["has_life_sentence"],
            has_death_sentence=life_death["has_death_sentence"],
            earliest_release_date=earliest_release,
            sentences=items
        )
