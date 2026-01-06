"""
Sentence Repository - Data access layer for sentences and adjustments.

Provides specialized queries for:
- Sentences by inmate, case, type
- Releasing soon queries
- Death sentence tracking
- Adjustment summaries
"""
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import SentenceType, AdjustmentType
from src.modules.sentence.models import Sentence, SentenceAdjustment


class SentenceRepository(AsyncBaseRepository[Sentence]):
    """Repository for Sentence entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Sentence, session)

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[Sentence]:
        """Get all sentences for an inmate."""
        query = select(Sentence).where(Sentence.inmate_id == inmate_id)

        if not include_deleted:
            query = query.where(Sentence.is_deleted == False)  # noqa: E712

        query = query.order_by(Sentence.sentence_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_court_case(
        self,
        court_case_id: UUID,
        include_deleted: bool = False
    ) -> List[Sentence]:
        """Get sentences for a court case."""
        query = select(Sentence).where(Sentence.court_case_id == court_case_id)

        if not include_deleted:
            query = query.where(Sentence.is_deleted == False)  # noqa: E712

        query = query.order_by(Sentence.sentence_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_current_sentence(self, inmate_id: UUID) -> Optional[Sentence]:
        """Get the current active sentence for an inmate (most recent without actual release)."""
        query = select(Sentence).where(
            Sentence.inmate_id == inmate_id,
            Sentence.actual_release_date == None,  # noqa: E711
            Sentence.is_deleted == False  # noqa: E712
        ).order_by(Sentence.start_date.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_releasing_soon(
        self,
        days_ahead: int = 30
    ) -> List[Sentence]:
        """Get sentences with expected release within specified days."""
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        query = select(Sentence).where(
            Sentence.expected_release_date != None,  # noqa: E711
            Sentence.expected_release_date >= today,
            Sentence.expected_release_date <= cutoff,
            Sentence.actual_release_date == None,  # noqa: E711
            Sentence.life_sentence == False,  # noqa: E712
            Sentence.is_death_sentence == False,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        ).order_by(Sentence.expected_release_date.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_death_sentences(self) -> List[Sentence]:
        """Get all death sentences (capital cases)."""
        query = select(Sentence).where(
            Sentence.is_death_sentence == True,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        ).order_by(Sentence.sentence_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_life_sentences(self) -> List[Sentence]:
        """Get all life sentences."""
        query = select(Sentence).where(
            Sentence.life_sentence == True,  # noqa: E712
            Sentence.is_death_sentence == False,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        ).order_by(Sentence.sentence_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        sentence_type: SentenceType,
        include_deleted: bool = False
    ) -> List[Sentence]:
        """Get sentences by type."""
        query = select(Sentence).where(Sentence.sentence_type == sentence_type.value)

        if not include_deleted:
            query = query.where(Sentence.is_deleted == False)  # noqa: E712

        query = query.order_by(Sentence.sentence_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_inmate(self, inmate_id: UUID) -> int:
        """Count sentences for an inmate."""
        query = select(func.count()).select_from(Sentence).where(
            Sentence.inmate_id == inmate_id,
            Sentence.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def has_life_or_death_sentence(self, inmate_id: UUID) -> dict:
        """Check if inmate has life or death sentence."""
        life_query = select(func.count()).select_from(Sentence).where(
            Sentence.inmate_id == inmate_id,
            Sentence.life_sentence == True,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        )
        death_query = select(func.count()).select_from(Sentence).where(
            Sentence.inmate_id == inmate_id,
            Sentence.is_death_sentence == True,  # noqa: E712
            Sentence.is_deleted == False  # noqa: E712
        )

        life_result = await self.session.execute(life_query)
        death_result = await self.session.execute(death_query)

        return {
            "has_life_sentence": (life_result.scalar() or 0) > 0,
            "has_death_sentence": (death_result.scalar() or 0) > 0
        }


class SentenceAdjustmentRepository(AsyncBaseRepository[SentenceAdjustment]):
    """Repository for SentenceAdjustment entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(SentenceAdjustment, session)

    async def get_by_sentence(
        self,
        sentence_id: UUID,
        include_deleted: bool = False
    ) -> List[SentenceAdjustment]:
        """Get all adjustments for a sentence."""
        query = select(SentenceAdjustment).where(
            SentenceAdjustment.sentence_id == sentence_id
        )

        if not include_deleted:
            query = query.where(SentenceAdjustment.is_deleted == False)  # noqa: E712

        query = query.order_by(SentenceAdjustment.effective_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        sentence_id: UUID,
        adjustment_type: AdjustmentType
    ) -> List[SentenceAdjustment]:
        """Get adjustments by type for a sentence."""
        query = select(SentenceAdjustment).where(
            SentenceAdjustment.sentence_id == sentence_id,
            SentenceAdjustment.adjustment_type == adjustment_type.value,
            SentenceAdjustment.is_deleted == False  # noqa: E712
        ).order_by(SentenceAdjustment.effective_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_adjustment_days(self, sentence_id: UUID) -> int:
        """Get sum of all adjustment days for a sentence."""
        query = select(func.coalesce(func.sum(SentenceAdjustment.days), 0)).where(
            SentenceAdjustment.sentence_id == sentence_id,
            SentenceAdjustment.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_adjustment_summary(self, sentence_id: UUID) -> dict:
        """Get summary of adjustments by type."""
        adjustments = await self.get_by_sentence(sentence_id)

        summary = {
            "total_days": 0,
            "by_type": {}
        }

        for adj in adjustments:
            summary["total_days"] += adj.days
            adj_type = adj.adjustment_type
            if adj_type not in summary["by_type"]:
                summary["by_type"][adj_type] = 0
            summary["by_type"][adj_type] += adj.days

        return summary
