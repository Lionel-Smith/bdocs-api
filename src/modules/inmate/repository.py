"""
Inmate Repository - Data access layer for inmate records.

Extends AsyncBaseRepository with inmate-specific queries.
"""
from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_repository import AsyncBaseRepository
from src.common.enums import InmateStatus, SecurityLevel
from src.modules.inmate.models import Inmate


class InmateRepository(AsyncBaseRepository[Inmate]):
    """Repository for Inmate entity operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Inmate, session)

    async def get_by_booking_number(self, booking_number: str) -> Optional[Inmate]:
        """Get inmate by their unique booking number."""
        result = await self.session.execute(
            select(Inmate).where(
                and_(
                    Inmate.booking_number == booking_number,
                    Inmate.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_nib_number(self, nib_number: str) -> Optional[Inmate]:
        """Get inmate by National Insurance Board number."""
        result = await self.session.execute(
            select(Inmate).where(
                and_(
                    Inmate.nib_number == nib_number,
                    Inmate.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def search_by_name(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Inmate], int]:
        """
        Search inmates by name (first, middle, last) or booking number.

        Returns:
            Tuple of (list of inmates, total count)
        """
        search_term = f"%{query.lower()}%"

        # Build search conditions
        conditions = or_(
            func.lower(Inmate.first_name).like(search_term),
            func.lower(Inmate.middle_name).like(search_term),
            func.lower(Inmate.last_name).like(search_term),
            func.lower(Inmate.booking_number).like(search_term),
        )

        # Count query
        count_query = select(func.count()).select_from(Inmate).where(
            and_(conditions, Inmate.is_deleted == False)  # noqa: E712
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        data_query = (
            select(Inmate)
            .where(and_(conditions, Inmate.is_deleted == False))  # noqa: E712
            .order_by(Inmate.last_name, Inmate.first_name)
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.session.execute(data_query)
        inmates = list(data_result.scalars().all())

        return inmates, total

    async def get_by_status(
        self,
        status: InmateStatus,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Inmate], int]:
        """Get inmates filtered by status."""
        # Count
        count_query = select(func.count()).select_from(Inmate).where(
            and_(
                Inmate.status == status,
                Inmate.is_deleted == False  # noqa: E712
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data
        data_query = (
            select(Inmate)
            .where(and_(Inmate.status == status, Inmate.is_deleted == False))  # noqa: E712
            .order_by(Inmate.admission_date.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.session.execute(data_query)
        inmates = list(data_result.scalars().all())

        return inmates, total

    async def get_active_inmates(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Inmate], int]:
        """Get inmates currently in custody (REMAND or SENTENCED)."""
        active_statuses = [InmateStatus.REMAND, InmateStatus.SENTENCED]

        # Count
        count_query = select(func.count()).select_from(Inmate).where(
            and_(
                Inmate.status.in_(active_statuses),
                Inmate.is_deleted == False  # noqa: E712
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data
        data_query = (
            select(Inmate)
            .where(and_(Inmate.status.in_(active_statuses), Inmate.is_deleted == False))  # noqa: E712
            .order_by(Inmate.admission_date.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.session.execute(data_query)
        inmates = list(data_result.scalars().all())

        return inmates, total

    async def get_by_security_level(
        self,
        security_level: SecurityLevel,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Inmate], int]:
        """Get inmates by security classification level."""
        # Count
        count_query = select(func.count()).select_from(Inmate).where(
            and_(
                Inmate.security_level == security_level,
                Inmate.status.in_([InmateStatus.REMAND, InmateStatus.SENTENCED]),
                Inmate.is_deleted == False  # noqa: E712
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data
        data_query = (
            select(Inmate)
            .where(
                and_(
                    Inmate.security_level == security_level,
                    Inmate.status.in_([InmateStatus.REMAND, InmateStatus.SENTENCED]),
                    Inmate.is_deleted == False  # noqa: E712
                )
            )
            .order_by(Inmate.last_name, Inmate.first_name)
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.session.execute(data_query)
        inmates = list(data_result.scalars().all())

        return inmates, total

    async def get_next_booking_sequence(self, year: int) -> int:
        """
        Get the next booking sequence number for a given year.

        Booking format: BDOCS-{year}-{5-digit-sequence}
        Example: BDOCS-2026-00001
        """
        prefix = f"BDOCS-{year}-"

        result = await self.session.execute(
            select(func.max(Inmate.booking_number))
            .where(Inmate.booking_number.like(f"{prefix}%"))
        )
        max_booking = result.scalar()

        if max_booking is None:
            return 1

        # Extract sequence number from BDOCS-YYYY-NNNNN
        try:
            sequence = int(max_booking.split('-')[-1])
            return sequence + 1
        except (ValueError, IndexError):
            return 1

    async def list_with_filters(
        self,
        status: Optional[InmateStatus] = None,
        security_level: Optional[SecurityLevel] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Inmate], int]:
        """List inmates with optional filters."""
        conditions = [Inmate.is_deleted == False]  # noqa: E712

        if status:
            conditions.append(Inmate.status == status)
        if security_level:
            conditions.append(Inmate.security_level == security_level)

        # Count
        count_query = select(func.count()).select_from(Inmate).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data
        data_query = (
            select(Inmate)
            .where(and_(*conditions))
            .order_by(Inmate.admission_date.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.session.execute(data_query)
        inmates = list(data_result.scalars().all())

        return inmates, total
