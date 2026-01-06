"""
Clemency Repository - Data access layer for clemency petitions.

Provides specialized queries for:
- Petitions by status, type, inmate
- Pending committee/minister queues
- Statistics and reporting
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import PetitionType, PetitionStatus
from src.modules.clemency.models import ClemencyPetition, ClemencyStatusHistory


class ClemencyPetitionRepository(AsyncBaseRepository[ClemencyPetition]):
    """Repository for ClemencyPetition entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ClemencyPetition, session)

    async def get_by_petition_number(self, petition_number: str) -> Optional[ClemencyPetition]:
        """Get petition by petition number."""
        query = select(ClemencyPetition).where(
            ClemencyPetition.petition_number == petition_number.upper(),
            ClemencyPetition.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[ClemencyPetition]:
        """Get all petitions for an inmate."""
        query = select(ClemencyPetition).where(ClemencyPetition.inmate_id == inmate_id)

        if not include_deleted:
            query = query.where(ClemencyPetition.is_deleted == False)  # noqa: E712

        query = query.order_by(ClemencyPetition.filed_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_sentence(
        self,
        sentence_id: UUID,
        include_deleted: bool = False
    ) -> List[ClemencyPetition]:
        """Get all petitions for a sentence."""
        query = select(ClemencyPetition).where(ClemencyPetition.sentence_id == sentence_id)

        if not include_deleted:
            query = query.where(ClemencyPetition.is_deleted == False)  # noqa: E712

        query = query.order_by(ClemencyPetition.filed_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: PetitionStatus,
        include_deleted: bool = False
    ) -> List[ClemencyPetition]:
        """Get petitions by status."""
        query = select(ClemencyPetition).where(ClemencyPetition.status == status.value)

        if not include_deleted:
            query = query.where(ClemencyPetition.is_deleted == False)  # noqa: E712

        query = query.order_by(ClemencyPetition.filed_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_committee(self) -> List[ClemencyPetition]:
        """Get petitions awaiting committee review."""
        query = select(ClemencyPetition).where(
            ClemencyPetition.status == PetitionStatus.COMMITTEE_SCHEDULED.value,
            ClemencyPetition.is_deleted == False  # noqa: E712
        ).order_by(ClemencyPetition.filed_date.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_minister(self) -> List[ClemencyPetition]:
        """Get petitions awaiting minister review."""
        query = select(ClemencyPetition).where(
            ClemencyPetition.status == PetitionStatus.AWAITING_MINISTER.value,
            ClemencyPetition.is_deleted == False  # noqa: E712
        ).order_by(ClemencyPetition.filed_date.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_governor_general(self) -> List[ClemencyPetition]:
        """Get petitions awaiting Governor-General decision."""
        query = select(ClemencyPetition).where(
            ClemencyPetition.status == PetitionStatus.GOVERNOR_GENERAL.value,
            ClemencyPetition.is_deleted == False  # noqa: E712
        ).order_by(ClemencyPetition.filed_date.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        petition_type: PetitionType,
        include_deleted: bool = False
    ) -> List[ClemencyPetition]:
        """Get petitions by type."""
        query = select(ClemencyPetition).where(
            ClemencyPetition.petition_type == petition_type.value
        )

        if not include_deleted:
            query = query.where(ClemencyPetition.is_deleted == False)  # noqa: E712

        query = query.order_by(ClemencyPetition.filed_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_petition_number(self) -> str:
        """Generate the next petition number (CP-YYYY-NNNNN)."""
        current_year = date.today().year
        prefix = f"CP-{current_year}-"

        # Find the highest number for this year
        query = select(func.max(ClemencyPetition.petition_number)).where(
            ClemencyPetition.petition_number.like(f"{prefix}%")
        )
        result = await self.session.execute(query)
        max_number = result.scalar()

        if max_number:
            # Extract the sequence number and increment
            seq = int(max_number.split('-')[-1]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:05d}"

    async def count_by_status(self) -> dict:
        """Count petitions by status."""
        result = {}
        for status in PetitionStatus:
            query = select(func.count()).select_from(ClemencyPetition).where(
                ClemencyPetition.status == status.value,
                ClemencyPetition.is_deleted == False  # noqa: E712
            )
            count = await self.session.execute(query)
            result[status.value] = count.scalar() or 0
        return result

    async def count_by_type(self) -> dict:
        """Count petitions by type."""
        result = {}
        for ptype in PetitionType:
            query = select(func.count()).select_from(ClemencyPetition).where(
                ClemencyPetition.petition_type == ptype.value,
                ClemencyPetition.is_deleted == False  # noqa: E712
            )
            count = await self.session.execute(query)
            result[ptype.value] = count.scalar() or 0
        return result

    async def count_decisions_last_year(self) -> dict:
        """Count granted and denied decisions in the last year."""
        one_year_ago = date.today() - timedelta(days=365)

        granted_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.status == PetitionStatus.GRANTED.value,
            ClemencyPetition.decision_date >= one_year_ago,
            ClemencyPetition.is_deleted == False  # noqa: E712
        )
        denied_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.status == PetitionStatus.DENIED.value,
            ClemencyPetition.decision_date >= one_year_ago,
            ClemencyPetition.is_deleted == False  # noqa: E712
        )

        granted_count = await self.session.execute(granted_query)
        denied_count = await self.session.execute(denied_query)

        return {
            "granted": granted_count.scalar() or 0,
            "denied": denied_count.scalar() or 0
        }

    async def count_by_inmate_status(self, inmate_id: UUID) -> dict:
        """Count petitions by status for an inmate."""
        pending = [
            PetitionStatus.SUBMITTED.value,
            PetitionStatus.UNDER_REVIEW.value,
            PetitionStatus.COMMITTEE_SCHEDULED.value,
            PetitionStatus.AWAITING_MINISTER.value,
            PetitionStatus.GOVERNOR_GENERAL.value,
            PetitionStatus.DEFERRED.value,
        ]

        total_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.inmate_id == inmate_id,
            ClemencyPetition.is_deleted == False  # noqa: E712
        )
        pending_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.inmate_id == inmate_id,
            ClemencyPetition.status.in_(pending),
            ClemencyPetition.is_deleted == False  # noqa: E712
        )
        granted_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.inmate_id == inmate_id,
            ClemencyPetition.status == PetitionStatus.GRANTED.value,
            ClemencyPetition.is_deleted == False  # noqa: E712
        )
        denied_query = select(func.count()).select_from(ClemencyPetition).where(
            ClemencyPetition.inmate_id == inmate_id,
            ClemencyPetition.status == PetitionStatus.DENIED.value,
            ClemencyPetition.is_deleted == False  # noqa: E712
        )

        total = await self.session.execute(total_query)
        pending_count = await self.session.execute(pending_query)
        granted = await self.session.execute(granted_query)
        denied = await self.session.execute(denied_query)

        return {
            "total": total.scalar() or 0,
            "pending": pending_count.scalar() or 0,
            "granted": granted.scalar() or 0,
            "denied": denied.scalar() or 0
        }


class ClemencyStatusHistoryRepository(AsyncBaseRepository[ClemencyStatusHistory]):
    """Repository for ClemencyStatusHistory entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ClemencyStatusHistory, session)

    async def get_by_petition(self, petition_id: UUID) -> List[ClemencyStatusHistory]:
        """Get all status history for a petition."""
        query = select(ClemencyStatusHistory).where(
            ClemencyStatusHistory.petition_id == petition_id
        ).order_by(ClemencyStatusHistory.changed_date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, petition_id: UUID) -> Optional[ClemencyStatusHistory]:
        """Get the most recent status change for a petition."""
        query = select(ClemencyStatusHistory).where(
            ClemencyStatusHistory.petition_id == petition_id
        ).order_by(ClemencyStatusHistory.changed_date.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
