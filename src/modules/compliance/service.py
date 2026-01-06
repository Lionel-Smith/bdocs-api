"""
Compliance Service - Business logic for ACA compliance management.

Handles ACA standards tracking, audits, findings, and comprehensive
compliance reporting that aggregates data from all BDOCS modules.

Key features:
- Generate compliance reports aggregating all module data
- Calculate compliance scores
- Track corrective actions and overdue items
- Dashboard for quick compliance overview
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.compliance.models import (
    ACAStandard, ComplianceAudit, AuditFinding
)
from src.modules.compliance.repository import (
    ACAStandardRepository, ComplianceAuditRepository, AuditFindingRepository
)
from src.modules.compliance.dtos import (
    AuditCreateDTO, AuditUpdateDTO, AuditStatusUpdateDTO,
    FindingCreateDTO, FindingUpdateDTO, FindingCompleteDTO,
    OverdueActionDTO, ComplianceReportDTO, ComplianceDashboardDTO,
    InmateStatisticsDTO, IncidentStatisticsDTO, TrainingStatisticsDTO,
    HealthcareStatisticsDTO, ProgrammeStatisticsDTO
)
from src.common.enums import (
    ACACategory, AuditType, AuditStatus, ComplianceStatus
)


class ComplianceService:
    """Service for ACA compliance management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.standard_repo = ACAStandardRepository(session)
        self.audit_repo = ComplianceAuditRepository(session)
        self.finding_repo = AuditFindingRepository(session)

    # =========================================================================
    # ACA Standard Operations (Read-Only - Standards are seeded)
    # =========================================================================

    async def get_standard(self, standard_id: UUID) -> Optional[ACAStandard]:
        """Get standard by ID."""
        return await self.standard_repo.get_by_id(standard_id)

    async def get_standard_by_number(self, standard_number: str) -> Optional[ACAStandard]:
        """Get standard by number (e.g., '4-4001')."""
        return await self.standard_repo.get_by_number(standard_number)

    async def get_all_standards(
        self,
        category: Optional[ACACategory] = None,
        is_mandatory: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ACAStandard]:
        """Get all standards with optional filters."""
        return await self.standard_repo.get_all(
            category=category,
            is_mandatory=is_mandatory,
            skip=skip,
            limit=limit
        )

    async def get_standards_by_category(
        self,
        category: ACACategory
    ) -> List[ACAStandard]:
        """Get all standards in a category."""
        return await self.standard_repo.get_by_category(category)

    async def count_standards(
        self,
        category: Optional[ACACategory] = None,
        is_mandatory: Optional[bool] = None
    ) -> int:
        """Count standards with optional filters."""
        return await self.standard_repo.count(category, is_mandatory)

    # =========================================================================
    # Compliance Audit Operations
    # =========================================================================

    async def create_audit(
        self,
        data: AuditCreateDTO,
        created_by: UUID
    ) -> ComplianceAudit:
        """
        Create a new compliance audit.

        Args:
            data: Audit details
            created_by: ID of staff creating the audit

        Returns:
            Created ComplianceAudit entity
        """
        audit = ComplianceAudit(
            id=uuid4(),
            audit_date=data.audit_date,
            auditor_name=data.auditor_name,
            audit_type=data.audit_type,
            status=AuditStatus.SCHEDULED,
            corrective_actions_required=0,
            next_audit_date=data.next_audit_date,
            created_by=created_by
        )

        return await self.audit_repo.create(audit)

    async def get_audit(self, audit_id: UUID) -> Optional[ComplianceAudit]:
        """Get audit by ID with findings."""
        return await self.audit_repo.get_by_id(audit_id)

    async def get_all_audits(
        self,
        audit_type: Optional[AuditType] = None,
        status: Optional[AuditStatus] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ComplianceAudit]:
        """Get all audits with optional filters."""
        return await self.audit_repo.get_all(
            audit_type=audit_type,
            status=status,
            year=year,
            skip=skip,
            limit=limit
        )

    async def get_latest_audit(
        self,
        audit_type: Optional[AuditType] = None
    ) -> Optional[ComplianceAudit]:
        """Get the most recent audit."""
        return await self.audit_repo.get_latest(audit_type)

    async def get_next_scheduled_audit(self) -> Optional[ComplianceAudit]:
        """Get the next scheduled audit."""
        return await self.audit_repo.get_next_scheduled()

    async def update_audit(
        self,
        audit_id: UUID,
        data: AuditUpdateDTO
    ) -> Optional[ComplianceAudit]:
        """Update audit details."""
        audit = await self.audit_repo.get_by_id(audit_id)
        if not audit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(audit, field, value)

        return await self.audit_repo.update(audit)

    async def update_audit_status(
        self,
        audit_id: UUID,
        data: AuditStatusUpdateDTO
    ) -> Optional[ComplianceAudit]:
        """
        Update audit status.

        When completing an audit, this also calculates the overall score
        and counts corrective actions required.
        """
        audit = await self.audit_repo.get_by_id(audit_id)
        if not audit:
            return None

        audit.status = data.status
        if data.findings_summary:
            audit.findings_summary = data.findings_summary

        # If completing the audit, calculate score
        if data.status == AuditStatus.COMPLETED:
            audit.overall_score = await self.calculate_compliance_score(audit_id)

            # Count corrective actions
            findings = await self.finding_repo.get_by_audit(audit_id)
            corrective_count = sum(
                1 for f in findings
                if f.corrective_action and not f.corrective_action_completed
            )
            audit.corrective_actions_required = corrective_count

        return await self.audit_repo.update(audit)

    async def start_audit(self, audit_id: UUID) -> Optional[ComplianceAudit]:
        """Start a scheduled audit (change status to IN_PROGRESS)."""
        audit = await self.audit_repo.get_by_id(audit_id)
        if not audit:
            return None

        if audit.status != AuditStatus.SCHEDULED:
            raise ValueError(f"Cannot start audit with status {audit.status.value}")

        audit.status = AuditStatus.IN_PROGRESS
        return await self.audit_repo.update(audit)

    # =========================================================================
    # Audit Finding Operations
    # =========================================================================

    async def create_finding(
        self,
        audit_id: UUID,
        data: FindingCreateDTO
    ) -> AuditFinding:
        """
        Create an audit finding for a specific standard.

        Args:
            audit_id: The audit this finding belongs to
            data: Finding details

        Returns:
            Created AuditFinding entity
        """
        finding = AuditFinding(
            id=uuid4(),
            audit_id=audit_id,
            standard_id=data.standard_id,
            compliance_status=data.compliance_status,
            evidence_provided=data.evidence_provided,
            finding_notes=data.finding_notes,
            corrective_action=data.corrective_action,
            corrective_action_due=data.corrective_action_due
        )

        return await self.finding_repo.create(finding)

    async def create_findings_bulk(
        self,
        audit_id: UUID,
        findings_data: List[FindingCreateDTO]
    ) -> List[AuditFinding]:
        """Create multiple findings for an audit at once."""
        findings = [
            AuditFinding(
                id=uuid4(),
                audit_id=audit_id,
                standard_id=data.standard_id,
                compliance_status=data.compliance_status,
                evidence_provided=data.evidence_provided,
                finding_notes=data.finding_notes,
                corrective_action=data.corrective_action,
                corrective_action_due=data.corrective_action_due
            )
            for data in findings_data
        ]

        return await self.finding_repo.create_bulk(findings)

    async def get_finding(self, finding_id: UUID) -> Optional[AuditFinding]:
        """Get finding by ID."""
        return await self.finding_repo.get_by_id(finding_id)

    async def get_audit_findings(
        self,
        audit_id: UUID,
        compliance_status: Optional[ComplianceStatus] = None
    ) -> List[AuditFinding]:
        """Get all findings for an audit."""
        return await self.finding_repo.get_by_audit(audit_id, compliance_status)

    async def update_finding(
        self,
        finding_id: UUID,
        data: FindingUpdateDTO
    ) -> Optional[AuditFinding]:
        """Update a finding."""
        finding = await self.finding_repo.get_by_id(finding_id)
        if not finding:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(finding, field, value)

        return await self.finding_repo.update(finding)

    async def complete_corrective_action(
        self,
        finding_id: UUID,
        data: FindingCompleteDTO,
        verified_by: UUID
    ) -> Optional[AuditFinding]:
        """
        Mark a corrective action as completed.

        Args:
            finding_id: The finding with corrective action
            data: Completion notes
            verified_by: Staff verifying completion

        Returns:
            Updated AuditFinding or None if not found
        """
        finding = await self.finding_repo.get_by_id(finding_id)
        if not finding:
            return None

        if not finding.corrective_action:
            raise ValueError("Finding has no corrective action to complete")

        if finding.corrective_action_completed:
            raise ValueError("Corrective action already completed")

        finding.corrective_action_completed = date.today()
        finding.verified_by = verified_by

        if data.completion_notes:
            existing_notes = finding.finding_notes or ""
            finding.finding_notes = f"{existing_notes}\n\nCompletion Notes: {data.completion_notes}".strip()

        return await self.finding_repo.update(finding)

    # =========================================================================
    # Compliance Score Calculation
    # =========================================================================

    async def calculate_compliance_score(self, audit_id: UUID) -> Decimal:
        """
        Calculate compliance score for an audit.

        Score = (Compliant + 0.5 * Partial) / (Total - Not Applicable) * 100

        Args:
            audit_id: Audit to calculate score for

        Returns:
            Compliance percentage (0-100)
        """
        status_counts = await self.finding_repo.count_by_status(audit_id)

        compliant = status_counts.get(ComplianceStatus.COMPLIANT.value, 0)
        partial = status_counts.get(ComplianceStatus.PARTIAL.value, 0)
        non_compliant = status_counts.get(ComplianceStatus.NON_COMPLIANT.value, 0)
        not_applicable = status_counts.get(ComplianceStatus.NOT_APPLICABLE.value, 0)

        total_applicable = compliant + partial + non_compliant

        if total_applicable == 0:
            return Decimal("0.00")

        # Compliant = full point, Partial = half point
        score_points = compliant + (Decimal("0.5") * partial)
        score = (score_points / total_applicable) * 100

        return round(score, 2)

    # =========================================================================
    # Corrective Actions Tracking
    # =========================================================================

    async def get_overdue_corrective_actions(self) -> List[OverdueActionDTO]:
        """
        Get all overdue corrective actions.

        Returns findings where:
        - corrective_action_due < today
        - corrective_action_completed IS NULL

        Returns:
            List of OverdueActionDTO sorted by due date (oldest first)
        """
        findings = await self.finding_repo.get_overdue_corrective_actions()
        today = date.today()

        result = []
        for finding in findings:
            days_overdue = (today - finding.corrective_action_due).days

            result.append(OverdueActionDTO(
                finding_id=finding.id,
                audit_id=finding.audit_id,
                audit_date=finding.audit.audit_date if finding.audit else date.today(),
                audit_type=finding.audit.audit_type if finding.audit else AuditType.SELF_ASSESSMENT,
                standard_number=finding.standard.standard_number if finding.standard else "",
                standard_title=finding.standard.title if finding.standard else "",
                category=finding.standard.category if finding.standard else ACACategory.SAFETY,
                is_mandatory=finding.standard.is_mandatory if finding.standard else False,
                corrective_action=finding.corrective_action or "",
                corrective_action_due=finding.corrective_action_due,
                days_overdue=days_overdue
            ))

        return result

    async def get_open_corrective_actions(self) -> List[AuditFinding]:
        """Get all findings with open (incomplete) corrective actions."""
        return await self.finding_repo.get_open_corrective_actions()

    async def count_open_corrective_actions(self) -> int:
        """Count open corrective actions."""
        return await self.finding_repo.count_open_corrective_actions()

    async def count_overdue_corrective_actions(self) -> int:
        """Count overdue corrective actions."""
        return await self.finding_repo.count_overdue_corrective_actions()

    # =========================================================================
    # Comprehensive Compliance Report
    # =========================================================================

    async def generate_compliance_report(
        self,
        facility_name: str = "Bahamas Department of Correctional Services"
    ) -> ComplianceReportDTO:
        """
        Generate comprehensive compliance report aggregating all module data.

        This report is used for ACA accreditation documentation and
        internal compliance review. It pulls statistics from:
        - Inmate module (population stats)
        - Incident module (incident trends)
        - Staff module (training compliance)
        - Healthcare module (medical compliance)
        - Programme module (programme participation)

        Args:
            facility_name: Name of facility for report header

        Returns:
            ComplianceReportDTO with aggregated data
        """
        today = date.today()

        # Get latest completed audit for scores
        latest_audit = await self.audit_repo.get_latest(audit_type=None)
        next_scheduled = await self.audit_repo.get_next_scheduled()

        # Calculate standard compliance from latest audit
        mandatory_met = 0
        mandatory_total = 0
        non_mandatory_met = 0
        non_mandatory_total = 0
        by_category: Dict[str, dict] = {}

        if latest_audit and latest_audit.status == AuditStatus.COMPLETED:
            findings = await self.finding_repo.get_by_audit(latest_audit.id)

            for finding in findings:
                if not finding.standard:
                    continue

                cat = finding.standard.category.value
                if cat not in by_category:
                    by_category[cat] = {
                        "compliant": 0,
                        "non_compliant": 0,
                        "partial": 0,
                        "total": 0
                    }

                by_category[cat]["total"] += 1

                if finding.compliance_status == ComplianceStatus.COMPLIANT:
                    by_category[cat]["compliant"] += 1
                    if finding.standard.is_mandatory:
                        mandatory_met += 1
                elif finding.compliance_status == ComplianceStatus.NON_COMPLIANT:
                    by_category[cat]["non_compliant"] += 1
                elif finding.compliance_status == ComplianceStatus.PARTIAL:
                    by_category[cat]["partial"] += 1

                if finding.standard.is_mandatory:
                    mandatory_total += 1
                else:
                    non_mandatory_total += 1
                    if finding.compliance_status == ComplianceStatus.COMPLIANT:
                        non_mandatory_met += 1

        # Calculate overall score
        total_applicable = mandatory_total + non_mandatory_total
        total_met = mandatory_met + non_mandatory_met
        overall_score = (total_met / total_applicable * 100) if total_applicable > 0 else 0.0

        # Get corrective action counts
        open_corrective = await self.finding_repo.count_open_corrective_actions()
        overdue_corrective = await self.finding_repo.count_overdue_corrective_actions()

        # Module statistics - these would integrate with actual module services
        # For now, returning placeholder data structure
        inmate_stats = await self._get_inmate_statistics()
        incident_stats = await self._get_incident_statistics()
        training_stats = await self._get_training_statistics()
        healthcare_stats = await self._get_healthcare_statistics()
        programme_stats = await self._get_programme_statistics()

        return ComplianceReportDTO(
            report_date=today,
            facility_name=facility_name,
            overall_compliance_score=round(overall_score, 2),
            mandatory_standards_met=mandatory_met,
            mandatory_standards_total=mandatory_total,
            non_mandatory_standards_met=non_mandatory_met,
            non_mandatory_standards_total=non_mandatory_total,
            inmate_statistics=inmate_stats,
            incident_statistics=incident_stats,
            training_statistics=training_stats,
            healthcare_statistics=healthcare_stats,
            programme_statistics=programme_stats,
            by_category=by_category,
            open_corrective_actions=open_corrective,
            overdue_corrective_actions=overdue_corrective,
            last_audit_date=latest_audit.audit_date if latest_audit else None,
            last_audit_score=float(latest_audit.overall_score) if latest_audit and latest_audit.overall_score else None,
            next_scheduled_audit=next_scheduled.audit_date if next_scheduled else None
        )

    async def _get_inmate_statistics(self) -> InmateStatisticsDTO:
        """
        Get inmate statistics for compliance report.

        TODO: Integrate with actual inmate module service.
        """
        # Placeholder - would call InmateService.get_statistics()
        return InmateStatisticsDTO(
            total_inmates=0,
            by_status={},
            by_security_level={},
            average_age=0.0
        )

    async def _get_incident_statistics(self) -> IncidentStatisticsDTO:
        """
        Get incident statistics for compliance report.

        TODO: Integrate with actual incident module service.
        """
        # Placeholder - would call IncidentService.get_statistics()
        return IncidentStatisticsDTO(
            total_incidents_year=0,
            by_type={},
            by_severity={},
            average_resolution_days=0.0
        )

    async def _get_training_statistics(self) -> TrainingStatisticsDTO:
        """
        Get training statistics for compliance report.

        TODO: Integrate with actual staff module service.
        """
        # Placeholder - would call StaffService.get_training_statistics()
        return TrainingStatisticsDTO(
            total_staff=0,
            training_completion_rate=0.0,
            certifications_current=0,
            certifications_expired=0,
            certifications_expiring_30_days=0
        )

    async def _get_healthcare_statistics(self) -> HealthcareStatisticsDTO:
        """
        Get healthcare statistics for compliance report.

        TODO: Integrate with actual healthcare module service.
        """
        # Placeholder - would call HealthcareService.get_statistics()
        return HealthcareStatisticsDTO(
            inmates_with_medical_records=0,
            intake_screenings_completed=0,
            mental_health_flagged=0,
            on_suicide_watch=0,
            medication_compliance_rate=0.0
        )

    async def _get_programme_statistics(self) -> ProgrammeStatisticsDTO:
        """
        Get programme statistics for compliance report.

        TODO: Integrate with actual programme module service.
        """
        # Placeholder - would call ProgrammeService.get_statistics()
        return ProgrammeStatisticsDTO(
            total_programmes=0,
            active_enrollments=0,
            completion_rate=0.0,
            btvi_certifications_issued=0
        )

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard(self) -> ComplianceDashboardDTO:
        """
        Get compliance dashboard summary.

        Provides quick overview of compliance status for
        management dashboard.

        Returns:
            ComplianceDashboardDTO with key metrics
        """
        today = date.today()
        current_year = today.year

        # Standard counts
        total_standards = await self.standard_repo.count()
        mandatory_standards = await self.standard_repo.count(is_mandatory=True)

        # Audit info
        audits_this_year = await self.audit_repo.count_by_year(current_year)
        latest_audit = await self.audit_repo.get_latest()
        next_scheduled = await self.audit_repo.get_next_scheduled()

        # Corrective action counts
        open_corrective = await self.finding_repo.count_open_corrective_actions()
        overdue_corrective = await self.finding_repo.count_overdue_corrective_actions()
        completed_month = await self.finding_repo.count_corrective_actions_completed_month()

        # Calculate compliance rates from latest completed audit
        overall_score = 0.0
        mandatory_rate = 0.0
        compliance_by_category: Dict[str, float] = {}

        if latest_audit and latest_audit.status == AuditStatus.COMPLETED:
            overall_score = float(latest_audit.overall_score) if latest_audit.overall_score else 0.0

            findings = await self.finding_repo.get_by_audit(latest_audit.id)

            # Calculate mandatory compliance rate
            mandatory_compliant = 0
            mandatory_total = 0

            # Calculate by category
            category_counts: Dict[str, dict] = {}

            for finding in findings:
                if not finding.standard:
                    continue

                cat = finding.standard.category.value
                if cat not in category_counts:
                    category_counts[cat] = {"compliant": 0, "total": 0}

                category_counts[cat]["total"] += 1
                if finding.compliance_status == ComplianceStatus.COMPLIANT:
                    category_counts[cat]["compliant"] += 1

                if finding.standard.is_mandatory:
                    mandatory_total += 1
                    if finding.compliance_status == ComplianceStatus.COMPLIANT:
                        mandatory_compliant += 1

            mandatory_rate = (mandatory_compliant / mandatory_total * 100) if mandatory_total > 0 else 0.0

            for cat, counts in category_counts.items():
                compliance_by_category[cat] = (
                    counts["compliant"] / counts["total"] * 100
                ) if counts["total"] > 0 else 0.0

        # Generate alerts
        alerts = []

        if overdue_corrective > 0:
            alerts.append(f"{overdue_corrective} corrective action(s) are overdue")

        if mandatory_rate < 100:
            alerts.append(f"Mandatory compliance rate is {mandatory_rate:.1f}% (must be 100%)")

        if next_scheduled and (next_scheduled.audit_date - today).days <= 30:
            days_until = (next_scheduled.audit_date - today).days
            alerts.append(f"Next audit scheduled in {days_until} days")

        if latest_audit:
            days_since = (today - latest_audit.audit_date).days
            if days_since > 365:
                alerts.append(f"Last audit was {days_since} days ago (annual audit recommended)")

        return ComplianceDashboardDTO(
            overall_compliance_score=overall_score,
            mandatory_compliance_rate=mandatory_rate,
            total_standards=total_standards,
            mandatory_standards=mandatory_standards,
            audits_this_year=audits_this_year,
            last_audit_date=latest_audit.audit_date if latest_audit else None,
            last_audit_type=latest_audit.audit_type if latest_audit else None,
            last_audit_score=float(latest_audit.overall_score) if latest_audit and latest_audit.overall_score else None,
            next_scheduled_audit=next_scheduled.audit_date if next_scheduled else None,
            open_corrective_actions=open_corrective,
            overdue_corrective_actions=overdue_corrective,
            corrective_actions_completed_month=completed_month,
            compliance_by_category=compliance_by_category,
            alerts=alerts
        )
