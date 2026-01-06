"""
Reports Repository - Database access layer for report definitions and executions.

Provides CRUD operations and specialized queries for report management.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reports.models import ReportDefinition, ReportExecution
from src.common.enums import ReportCategory, ReportStatus


class ReportDefinitionRepository:
    """Repository for ReportDefinition operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, definition_id: UUID) -> Optional[ReportDefinition]:
        """Get report definition by ID."""
        result = await self.session.execute(
            select(ReportDefinition).where(ReportDefinition.id == definition_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ReportDefinition]:
        """Get report definition by unique code."""
        result = await self.session.execute(
            select(ReportDefinition).where(ReportDefinition.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        category: Optional[ReportCategory] = None,
        is_scheduled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportDefinition]:
        """Get all report definitions with optional filters."""
        query = select(ReportDefinition)

        conditions = []
        if category:
            conditions.append(ReportDefinition.category == category)
        if is_scheduled is not None:
            conditions.append(ReportDefinition.is_scheduled == is_scheduled)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(ReportDefinition.category, ReportDefinition.code)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scheduled(self) -> List[ReportDefinition]:
        """Get all scheduled report definitions."""
        result = await self.session.execute(
            select(ReportDefinition)
            .where(ReportDefinition.is_scheduled == True)
            .order_by(ReportDefinition.code)
        )
        return list(result.scalars().all())

    async def count(
        self,
        category: Optional[ReportCategory] = None
    ) -> int:
        """Count report definitions."""
        query = select(func.count(ReportDefinition.id))
        if category:
            query = query.where(ReportDefinition.category == category)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, definition: ReportDefinition) -> ReportDefinition:
        """Create a new report definition."""
        self.session.add(definition)
        await self.session.flush()
        await self.session.refresh(definition)
        return definition

    async def update(self, definition: ReportDefinition) -> ReportDefinition:
        """Update a report definition."""
        await self.session.flush()
        await self.session.refresh(definition)
        return definition

    async def update_last_generated(
        self,
        definition_id: UUID,
        generated_at: datetime
    ) -> None:
        """Update the last_generated timestamp."""
        definition = await self.get_by_id(definition_id)
        if definition:
            definition.last_generated = generated_at
            await self.session.flush()


class ReportExecutionRepository:
    """Repository for ReportExecution operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, execution_id: UUID) -> Optional[ReportExecution]:
        """Get report execution by ID."""
        result = await self.session.execute(
            select(ReportExecution).where(ReportExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        report_definition_id: Optional[UUID] = None,
        status: Optional[ReportStatus] = None,
        requested_by: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportExecution]:
        """Get report executions with optional filters."""
        query = select(ReportExecution)

        conditions = []
        if report_definition_id:
            conditions.append(ReportExecution.report_definition_id == report_definition_id)
        if status:
            conditions.append(ReportExecution.status == status)
        if requested_by:
            conditions.append(ReportExecution.requested_by == requested_by)
        if start_date:
            conditions.append(ReportExecution.started_at >= start_date)
        if end_date:
            conditions.append(ReportExecution.started_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(ReportExecution.started_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_definition(
        self,
        definition_id: UUID,
        limit: int = 10
    ) -> List[ReportExecution]:
        """Get recent executions for a specific report definition."""
        result = await self.session.execute(
            select(ReportExecution)
            .where(ReportExecution.report_definition_id == definition_id)
            .order_by(ReportExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active(self) -> List[ReportExecution]:
        """Get all active (queued or generating) executions."""
        result = await self.session.execute(
            select(ReportExecution)
            .where(ReportExecution.status.in_([
                ReportStatus.QUEUED,
                ReportStatus.GENERATING
            ]))
            .order_by(ReportExecution.started_at)
        )
        return list(result.scalars().all())

    async def get_user_history(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[ReportExecution]:
        """Get report history for a specific user."""
        result = await self.session.execute(
            select(ReportExecution)
            .where(ReportExecution.requested_by == user_id)
            .order_by(ReportExecution.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(
        self,
        report_definition_id: Optional[UUID] = None,
        status: Optional[ReportStatus] = None,
        requested_by: Optional[UUID] = None
    ) -> int:
        """Count report executions."""
        query = select(func.count(ReportExecution.id))

        conditions = []
        if report_definition_id:
            conditions.append(ReportExecution.report_definition_id == report_definition_id)
        if status:
            conditions.append(ReportExecution.status == status)
        if requested_by:
            conditions.append(ReportExecution.requested_by == requested_by)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, execution: ReportExecution) -> ReportExecution:
        """Create a new report execution."""
        self.session.add(execution)
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def update(self, execution: ReportExecution) -> ReportExecution:
        """Update a report execution."""
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def update_status(
        self,
        execution_id: UUID,
        status: ReportStatus,
        completed_at: Optional[datetime] = None,
        file_path: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ReportExecution]:
        """Update execution status and related fields."""
        execution = await self.get_by_id(execution_id)
        if execution:
            execution.status = status
            if completed_at:
                execution.completed_at = completed_at
            if file_path:
                execution.file_path = file_path
            if file_size_bytes is not None:
                execution.file_size_bytes = file_size_bytes
            if error_message:
                execution.error_message = error_message
            await self.session.flush()
        return execution

    async def get_stats_by_definition(
        self,
        definition_id: UUID
    ) -> dict:
        """Get execution statistics for a report definition."""
        # Total executions
        total = await self.count(report_definition_id=definition_id)

        # By status
        completed = await self.count(
            report_definition_id=definition_id,
            status=ReportStatus.COMPLETED
        )
        failed = await self.count(
            report_definition_id=definition_id,
            status=ReportStatus.FAILED
        )

        # Average duration (completed only)
        avg_duration_query = select(
            func.avg(
                func.extract('epoch', ReportExecution.completed_at) -
                func.extract('epoch', ReportExecution.started_at)
            )
        ).where(
            and_(
                ReportExecution.report_definition_id == definition_id,
                ReportExecution.status == ReportStatus.COMPLETED,
                ReportExecution.completed_at.isnot(None)
            )
        )
        result = await self.session.execute(avg_duration_query)
        avg_duration = result.scalar()

        return {
            'total_executions': total,
            'completed': completed,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'average_duration_seconds': int(avg_duration) if avg_duration else None
        }
