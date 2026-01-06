"""
Compliance Repository - Data access layer for ACA compliance management.

Handles database operations for ACAStandard, ComplianceAudit, and AuditFinding entities.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.compliance.models import ACAStandard, ComplianceAudit, AuditFinding
from src.common.enums import (
    ACACategory, AuditType, AuditStatus, ComplianceStatus
)


class ACAStandardRepository:
    """Repository for ACAStandard operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, standard_id: UUID) -> Optional[ACAStandard]:
        """Get standard by ID."""
        result = await self.session.execute(
            select(ACAStandard).where(ACAStandard.id == standard_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, standard_number: str) -> Optional[ACAStandard]:
        """Get standard by number (e.g., '4-4001')."""
        result = await self.session.execute(
            select(ACAStandard).where(ACAStandard.standard_number == standard_number)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        category: Optional[ACACategory] = None,
        is_mandatory: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ACAStandard]:
        """Get all standards with optional filters."""
        query = select(ACAStandard)

        if category:
            query = query.where(ACAStandard.category == category)
        if is_mandatory is not None:
            query = query.where(ACAStandard.is_mandatory == is_mandatory)

        query = query.order_by(ACAStandard.standard_number)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_category(self, category: ACACategory) -> List[ACAStandard]:
        """Get all standards in a category."""
        result = await self.session.execute(
            select(ACAStandard)
            .where(ACAStandard.category == category)
            .order_by(ACAStandard.standard_number)
        )
        return list(result.scalars().all())

    async def count(
        self,
        category: Optional[ACACategory] = None,
        is_mandatory: Optional[bool] = None
    ) -> int:
        """Count standards with optional filters."""
        query = select(func.count(ACAStandard.id))

        if category:
            query = query.where(ACAStandard.category == category)
        if is_mandatory is not None:
            query = query.where(ACAStandard.is_mandatory == is_mandatory)

        result = await self.session.execute(query)
        return result.scalar() or 0


class ComplianceAuditRepository:
    """Repository for ComplianceAudit operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, audit: ComplianceAudit) -> ComplianceAudit:
        """Create a new audit."""
        self.session.add(audit)
        await self.session.flush()
        await self.session.refresh(audit)
        return audit

    async def get_by_id(self, audit_id: UUID) -> Optional[ComplianceAudit]:
        """Get audit by ID."""
        result = await self.session.execute(
            select(ComplianceAudit)
            .where(ComplianceAudit.id == audit_id)
            .options(
                selectinload(ComplianceAudit.creator),
                selectinload(ComplianceAudit.findings)
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        audit_type: Optional[AuditType] = None,
        status: Optional[AuditStatus] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ComplianceAudit]:
        """Get all audits with optional filters."""
        query = select(ComplianceAudit)

        if audit_type:
            query = query.where(ComplianceAudit.audit_type == audit_type)
        if status:
            query = query.where(ComplianceAudit.status == status)
        if year:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            query = query.where(and_(
                ComplianceAudit.audit_date >= start_date,
                ComplianceAudit.audit_date <= end_date
            ))

        query = query.options(selectinload(ComplianceAudit.creator))
        query = query.order_by(ComplianceAudit.audit_date.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, audit_type: Optional[AuditType] = None) -> Optional[ComplianceAudit]:
        """Get most recent audit."""
        query = select(ComplianceAudit)

        if audit_type:
            query = query.where(ComplianceAudit.audit_type == audit_type)

        query = query.order_by(ComplianceAudit.audit_date.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_next_scheduled(self) -> Optional[ComplianceAudit]:
        """Get next scheduled audit."""
        today = date.today()

        result = await self.session.execute(
            select(ComplianceAudit)
            .where(and_(
                ComplianceAudit.status == AuditStatus.SCHEDULED,
                ComplianceAudit.audit_date >= today
            ))
            .order_by(ComplianceAudit.audit_date)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, audit: ComplianceAudit) -> ComplianceAudit:
        """Update an audit."""
        await self.session.flush()
        await self.session.refresh(audit)
        return audit

    async def count_by_year(self, year: int) -> int:
        """Count audits for a year."""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        result = await self.session.execute(
            select(func.count(ComplianceAudit.id))
            .where(and_(
                ComplianceAudit.audit_date >= start_date,
                ComplianceAudit.audit_date <= end_date
            ))
        )
        return result.scalar() or 0


class AuditFindingRepository:
    """Repository for AuditFinding operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, finding: AuditFinding) -> AuditFinding:
        """Create a new finding."""
        self.session.add(finding)
        await self.session.flush()
        await self.session.refresh(finding)
        return finding

    async def create_bulk(self, findings: List[AuditFinding]) -> List[AuditFinding]:
        """Create multiple findings."""
        self.session.add_all(findings)
        await self.session.flush()
        for finding in findings:
            await self.session.refresh(finding)
        return findings

    async def get_by_id(self, finding_id: UUID) -> Optional[AuditFinding]:
        """Get finding by ID."""
        result = await self.session.execute(
            select(AuditFinding)
            .where(AuditFinding.id == finding_id)
            .options(
                selectinload(AuditFinding.audit),
                selectinload(AuditFinding.standard),
                selectinload(AuditFinding.verifier)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_audit(
        self,
        audit_id: UUID,
        compliance_status: Optional[ComplianceStatus] = None
    ) -> List[AuditFinding]:
        """Get findings for an audit."""
        query = select(AuditFinding).where(AuditFinding.audit_id == audit_id)

        if compliance_status:
            query = query.where(AuditFinding.compliance_status == compliance_status)

        query = query.options(selectinload(AuditFinding.standard))
        query = query.order_by(AuditFinding.standard_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue_corrective_actions(self) -> List[AuditFinding]:
        """Get findings with overdue corrective actions."""
        today = date.today()

        result = await self.session.execute(
            select(AuditFinding)
            .where(and_(
                AuditFinding.corrective_action_due.isnot(None),
                AuditFinding.corrective_action_due < today,
                AuditFinding.corrective_action_completed.is_(None)
            ))
            .options(
                selectinload(AuditFinding.audit),
                selectinload(AuditFinding.standard)
            )
            .order_by(AuditFinding.corrective_action_due)
        )
        return list(result.scalars().all())

    async def get_open_corrective_actions(self) -> List[AuditFinding]:
        """Get findings with open (incomplete) corrective actions."""
        result = await self.session.execute(
            select(AuditFinding)
            .where(and_(
                AuditFinding.corrective_action.isnot(None),
                AuditFinding.corrective_action_completed.is_(None)
            ))
            .options(
                selectinload(AuditFinding.audit),
                selectinload(AuditFinding.standard)
            )
            .order_by(AuditFinding.corrective_action_due)
        )
        return list(result.scalars().all())

    async def update(self, finding: AuditFinding) -> AuditFinding:
        """Update a finding."""
        await self.session.flush()
        await self.session.refresh(finding)
        return finding

    async def count_by_status(self, audit_id: UUID) -> dict:
        """Get finding counts by status for an audit."""
        result = await self.session.execute(
            select(AuditFinding.compliance_status, func.count(AuditFinding.id))
            .where(AuditFinding.audit_id == audit_id)
            .group_by(AuditFinding.compliance_status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def count_corrective_actions_completed_month(self) -> int:
        """Count corrective actions completed this month."""
        today = date.today()
        month_start = date(today.year, today.month, 1)

        result = await self.session.execute(
            select(func.count(AuditFinding.id))
            .where(and_(
                AuditFinding.corrective_action_completed.isnot(None),
                AuditFinding.corrective_action_completed >= month_start
            ))
        )
        return result.scalar() or 0

    async def count_open_corrective_actions(self) -> int:
        """Count open corrective actions."""
        result = await self.session.execute(
            select(func.count(AuditFinding.id))
            .where(and_(
                AuditFinding.corrective_action.isnot(None),
                AuditFinding.corrective_action_completed.is_(None)
            ))
        )
        return result.scalar() or 0

    async def count_overdue_corrective_actions(self) -> int:
        """Count overdue corrective actions."""
        today = date.today()

        result = await self.session.execute(
            select(func.count(AuditFinding.id))
            .where(and_(
                AuditFinding.corrective_action_due.isnot(None),
                AuditFinding.corrective_action_due < today,
                AuditFinding.corrective_action_completed.is_(None)
            ))
        )
        return result.scalar() or 0
