"""
BTVI Certification Repository - Data access layer for BTVI certifications.

Provides specialized queries for:
- Certifications by inmate, trade, skill level
- Verification status queries
- Statistics and reporting
- Trade-based aggregations
"""
from datetime import date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import BTVICertType, SkillLevel
from src.modules.btvi.models import BTVICertification


class BTVICertificationRepository(AsyncBaseRepository[BTVICertification]):
    """Repository for BTVICertification entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BTVICertification, session)

    async def get_by_certification_number(
        self,
        certification_number: str
    ) -> Optional[BTVICertification]:
        """Get certification by certification number."""
        query = select(BTVICertification).where(
            BTVICertification.certification_number == certification_number.upper(),
            BTVICertification.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_inmate(
        self,
        inmate_id: UUID,
        include_deleted: bool = False
    ) -> List[BTVICertification]:
        """Get all certifications for an inmate."""
        query = select(BTVICertification).where(
            BTVICertification.inmate_id == inmate_id
        )
        if not include_deleted:
            query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
        query = query.order_by(BTVICertification.issued_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_trade(
        self,
        certification_type: BTVICertType,
        include_deleted: bool = False
    ) -> List[BTVICertification]:
        """Get certifications by trade type."""
        query = select(BTVICertification).where(
            BTVICertification.certification_type == certification_type.value
        )
        if not include_deleted:
            query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
        query = query.order_by(BTVICertification.issued_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_skill_level(
        self,
        skill_level: SkillLevel,
        include_deleted: bool = False
    ) -> List[BTVICertification]:
        """Get certifications by skill level."""
        query = select(BTVICertification).where(
            BTVICertification.skill_level == skill_level.value
        )
        if not include_deleted:
            query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
        query = query.order_by(BTVICertification.issued_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_enrollment(
        self,
        programme_enrollment_id: UUID
    ) -> Optional[BTVICertification]:
        """Get certification linked to a programme enrollment."""
        query = select(BTVICertification).where(
            BTVICertification.programme_enrollment_id == programme_enrollment_id,
            BTVICertification.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_verified(
        self,
        include_deleted: bool = False
    ) -> List[BTVICertification]:
        """Get all verified certifications."""
        query = select(BTVICertification).where(
            BTVICertification.is_verified == True  # noqa: E712
        )
        if not include_deleted:
            query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
        query = query.order_by(BTVICertification.issued_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired(
        self,
        include_deleted: bool = False
    ) -> List[BTVICertification]:
        """Get all expired certifications."""
        today = date.today()
        query = select(BTVICertification).where(
            BTVICertification.expiry_date.isnot(None),
            BTVICertification.expiry_date < today
        )
        if not include_deleted:
            query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
        query = query.order_by(BTVICertification.expiry_date.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_certification_number(self) -> str:
        """Generate the next certification number (BTVI-YYYY-NNNNN)."""
        current_year = date.today().year
        prefix = f"BTVI-{current_year}-"

        # Find the highest number for this year
        query = select(func.max(BTVICertification.certification_number)).where(
            BTVICertification.certification_number.like(f"{prefix}%")
        )
        result = await self.session.execute(query)
        max_number = result.scalar()

        if max_number:
            # Extract the sequence number and increment
            seq = int(max_number.split('-')[-1]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:05d}"

    async def count_by_trade(self, include_deleted: bool = False) -> dict:
        """Count certifications by trade type."""
        result = {}
        for cert_type in BTVICertType:
            query = select(func.count()).select_from(BTVICertification).where(
                BTVICertification.certification_type == cert_type.value
            )
            if not include_deleted:
                query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
            count = await self.session.execute(query)
            result[cert_type.value] = count.scalar() or 0
        return result

    async def count_by_skill_level(self, include_deleted: bool = False) -> dict:
        """Count certifications by skill level."""
        result = {}
        for level in SkillLevel:
            query = select(func.count()).select_from(BTVICertification).where(
                BTVICertification.skill_level == level.value
            )
            if not include_deleted:
                query = query.where(BTVICertification.is_deleted == False)  # noqa: E712
            count = await self.session.execute(query)
            result[level.value] = count.scalar() or 0
        return result

    async def count_by_inmate_status(self, inmate_id: UUID) -> dict:
        """Count certifications by status for an inmate."""
        today = date.today()

        # Total (not deleted)
        total_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.inmate_id == inmate_id,
            BTVICertification.is_deleted == False  # noqa: E712
        )

        # Valid (not expired, not deleted)
        valid_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.inmate_id == inmate_id,
            BTVICertification.is_deleted == False,  # noqa: E712
            (BTVICertification.expiry_date.is_(None)) |
            (BTVICertification.expiry_date >= today)
        )

        # Expired
        expired_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.inmate_id == inmate_id,
            BTVICertification.is_deleted == False,  # noqa: E712
            BTVICertification.expiry_date.isnot(None),
            BTVICertification.expiry_date < today
        )

        # Verified
        verified_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.inmate_id == inmate_id,
            BTVICertification.is_deleted == False,  # noqa: E712
            BTVICertification.is_verified == True  # noqa: E712
        )

        # Total training hours
        hours_query = select(func.sum(BTVICertification.hours_training)).where(
            BTVICertification.inmate_id == inmate_id,
            BTVICertification.is_deleted == False  # noqa: E712
        )

        total = await self.session.execute(total_query)
        valid = await self.session.execute(valid_query)
        expired = await self.session.execute(expired_query)
        verified = await self.session.execute(verified_query)
        hours = await self.session.execute(hours_query)

        # By trade
        by_trade = {}
        for cert_type in BTVICertType:
            trade_query = select(func.count()).select_from(BTVICertification).where(
                BTVICertification.inmate_id == inmate_id,
                BTVICertification.certification_type == cert_type.value,
                BTVICertification.is_deleted == False  # noqa: E712
            )
            trade_count = await self.session.execute(trade_query)
            count = trade_count.scalar() or 0
            if count > 0:
                by_trade[cert_type.value] = count

        # By skill level
        by_level = {}
        for level in SkillLevel:
            level_query = select(func.count()).select_from(BTVICertification).where(
                BTVICertification.inmate_id == inmate_id,
                BTVICertification.skill_level == level.value,
                BTVICertification.is_deleted == False  # noqa: E712
            )
            level_count = await self.session.execute(level_query)
            count = level_count.scalar() or 0
            if count > 0:
                by_level[level.value] = count

        return {
            "total": total.scalar() or 0,
            "valid": valid.scalar() or 0,
            "expired": expired.scalar() or 0,
            "verified": verified.scalar() or 0,
            "total_training_hours": hours.scalar() or 0,
            "by_trade": by_trade,
            "by_skill_level": by_level
        }

    async def count_issued_this_year(self) -> int:
        """Count certifications issued this year."""
        current_year = date.today().year
        query = select(func.count()).select_from(BTVICertification).where(
            extract('year', BTVICertification.issued_date) == current_year,
            BTVICertification.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_average_training_hours(self) -> Optional[float]:
        """Get average training hours across all certifications."""
        query = select(func.avg(BTVICertification.hours_training)).where(
            BTVICertification.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else None

    async def get_average_assessment_score(self) -> Optional[float]:
        """Get average assessment score across all certifications."""
        query = select(func.avg(BTVICertification.assessment_score)).where(
            BTVICertification.is_deleted == False,  # noqa: E712
            BTVICertification.assessment_score.isnot(None)
        )
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else None

    async def get_trade_statistics(self, certification_type: BTVICertType) -> dict:
        """Get statistics for a specific trade."""
        today = date.today()

        # Count total
        total_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.certification_type == certification_type.value,
            BTVICertification.is_deleted == False  # noqa: E712
        )

        # Count by skill level
        by_level = {}
        for level in SkillLevel:
            level_query = select(func.count()).select_from(BTVICertification).where(
                BTVICertification.certification_type == certification_type.value,
                BTVICertification.skill_level == level.value,
                BTVICertification.is_deleted == False  # noqa: E712
            )
            level_count = await self.session.execute(level_query)
            by_level[level.value] = level_count.scalar() or 0

        # Average training hours
        avg_hours_query = select(func.avg(BTVICertification.hours_training)).where(
            BTVICertification.certification_type == certification_type.value,
            BTVICertification.is_deleted == False  # noqa: E712
        )

        # Average assessment score
        avg_score_query = select(func.avg(BTVICertification.assessment_score)).where(
            BTVICertification.certification_type == certification_type.value,
            BTVICertification.is_deleted == False,  # noqa: E712
            BTVICertification.assessment_score.isnot(None)
        )

        # Count verified
        verified_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.certification_type == certification_type.value,
            BTVICertification.is_verified == True,  # noqa: E712
            BTVICertification.is_deleted == False  # noqa: E712
        )

        # Count expired
        expired_query = select(func.count()).select_from(BTVICertification).where(
            BTVICertification.certification_type == certification_type.value,
            BTVICertification.expiry_date.isnot(None),
            BTVICertification.expiry_date < today,
            BTVICertification.is_deleted == False  # noqa: E712
        )

        total = await self.session.execute(total_query)
        avg_hours = await self.session.execute(avg_hours_query)
        avg_score = await self.session.execute(avg_score_query)
        verified = await self.session.execute(verified_query)
        expired = await self.session.execute(expired_query)

        return {
            "total": total.scalar() or 0,
            "by_skill_level": by_level,
            "average_training_hours": float(avg_hours.scalar()) if avg_hours.scalar() else None,
            "average_assessment_score": float(avg_score.scalar()) if avg_score.scalar() else None,
            "verified_count": verified.scalar() or 0,
            "expired_count": expired.scalar() or 0
        }

    async def get_most_popular_trades(self, limit: int = 5) -> List[dict]:
        """Get trades with most certifications."""
        query = (
            select(
                BTVICertification.certification_type,
                func.count(BTVICertification.id).label('count')
            )
            .where(BTVICertification.is_deleted == False)  # noqa: E712
            .group_by(BTVICertification.certification_type)
            .order_by(func.count(BTVICertification.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [
            {
                "trade": row.certification_type,
                "count": row.count
            }
            for row in result.all()
        ]
