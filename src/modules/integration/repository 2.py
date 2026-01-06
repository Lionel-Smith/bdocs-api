"""
Integration Repository - Data access layer for external system logs.

Handles database operations for ExternalSystemLog entities.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.integration.models import ExternalSystemLog
from src.common.enums import RequestType, IntegrationStatus


class ExternalSystemLogRepository:
    """Repository for ExternalSystemLog operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: ExternalSystemLog) -> ExternalSystemLog:
        """Create a new log entry."""
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: UUID) -> Optional[ExternalSystemLog]:
        """Get log by ID."""
        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(ExternalSystemLog.id == log_id)
            .options(selectinload(ExternalSystemLog.initiator))
        )
        return result.scalar_one_or_none()

    async def get_by_correlation_id(
        self,
        correlation_id: UUID
    ) -> List[ExternalSystemLog]:
        """Get all logs with a correlation ID."""
        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(ExternalSystemLog.correlation_id == correlation_id)
            .options(selectinload(ExternalSystemLog.initiator))
            .order_by(ExternalSystemLog.request_time)
        )
        return list(result.scalars().all())

    async def get_all(
        self,
        system_name: Optional[str] = None,
        request_type: Optional[RequestType] = None,
        status: Optional[IntegrationStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExternalSystemLog]:
        """Get all logs with optional filters."""
        query = select(ExternalSystemLog)

        conditions = []
        if system_name:
            conditions.append(ExternalSystemLog.system_name == system_name)
        if request_type:
            conditions.append(ExternalSystemLog.request_type == request_type)
        if status:
            conditions.append(ExternalSystemLog.status == status)
        if start_date:
            conditions.append(ExternalSystemLog.request_time >= start_date)
        if end_date:
            conditions.append(ExternalSystemLog.request_time <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.options(selectinload(ExternalSystemLog.initiator))
        query = query.order_by(ExternalSystemLog.request_time.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, log: ExternalSystemLog) -> ExternalSystemLog:
        """Update a log entry."""
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def count(
        self,
        system_name: Optional[str] = None,
        request_type: Optional[RequestType] = None,
        status: Optional[IntegrationStatus] = None
    ) -> int:
        """Count logs with optional filters."""
        query = select(func.count(ExternalSystemLog.id))

        conditions = []
        if system_name:
            conditions.append(ExternalSystemLog.system_name == system_name)
        if request_type:
            conditions.append(ExternalSystemLog.request_type == request_type)
        if status:
            conditions.append(ExternalSystemLog.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_last_successful(
        self,
        system_name: str
    ) -> Optional[ExternalSystemLog]:
        """Get the last successful request for a system."""
        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(and_(
                ExternalSystemLog.system_name == system_name,
                ExternalSystemLog.status == IntegrationStatus.SUCCESS
            ))
            .order_by(ExternalSystemLog.request_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_last_failed(
        self,
        system_name: str
    ) -> Optional[ExternalSystemLog]:
        """Get the last failed request for a system."""
        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(and_(
                ExternalSystemLog.system_name == system_name,
                ExternalSystemLog.status.in_([
                    IntegrationStatus.FAILED,
                    IntegrationStatus.TIMEOUT
                ])
            ))
            .order_by(ExternalSystemLog.request_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_success_rate(
        self,
        system_name: str,
        hours: int = 24
    ) -> float:
        """Calculate success rate for a system in the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Total count
        total_result = await self.session.execute(
            select(func.count(ExternalSystemLog.id))
            .where(and_(
                ExternalSystemLog.system_name == system_name,
                ExternalSystemLog.request_time >= cutoff
            ))
        )
        total = total_result.scalar() or 0

        if total == 0:
            return 100.0  # No requests means no failures

        # Success count
        success_result = await self.session.execute(
            select(func.count(ExternalSystemLog.id))
            .where(and_(
                ExternalSystemLog.system_name == system_name,
                ExternalSystemLog.request_time >= cutoff,
                ExternalSystemLog.status == IntegrationStatus.SUCCESS
            ))
        )
        success = success_result.scalar() or 0

        return (success / total) * 100

    async def get_average_response_time(
        self,
        system_name: str,
        hours: int = 24
    ) -> Optional[int]:
        """Calculate average response time in ms for successful requests."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(and_(
                ExternalSystemLog.system_name == system_name,
                ExternalSystemLog.request_time >= cutoff,
                ExternalSystemLog.status == IntegrationStatus.SUCCESS,
                ExternalSystemLog.response_time.isnot(None)
            ))
        )
        logs = result.scalars().all()

        if not logs:
            return None

        total_ms = sum(
            log.response_time_ms for log in logs
            if log.response_time_ms is not None
        )
        return int(total_ms / len(logs)) if logs else None

    async def get_recent_by_system(
        self,
        system_name: str,
        limit: int = 10
    ) -> List[ExternalSystemLog]:
        """Get recent logs for a specific system."""
        result = await self.session.execute(
            select(ExternalSystemLog)
            .where(ExternalSystemLog.system_name == system_name)
            .order_by(ExternalSystemLog.request_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
