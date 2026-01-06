"""
ACA Compliance Reporting DTOs - Data Transfer Objects for compliance management.

Provides structured data validation for standards, audits, findings,
and comprehensive compliance reports.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.common.enums import (
    ACACategory, AuditType, AuditStatus, ComplianceStatus
)


# =============================================================================
# Evidence DTO
# =============================================================================

class EvidenceRequirementDTO(BaseModel):
    """Evidence requirement entry."""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="Type of evidence (policy, log, record, etc.)")
    description: str = Field(..., max_length=500)


# =============================================================================
# ACA Standard DTOs
# =============================================================================

class ACAStandardDTO(BaseModel):
    """ACA Standard response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    standard_number: str
    category: ACACategory
    title: str
    description: str
    is_mandatory: bool
    evidence_required: Optional[List[dict]] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class ACAStandardListDTO(BaseModel):
    """Minimal standard info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    standard_number: str
    category: ACACategory
    title: str
    is_mandatory: bool


# =============================================================================
# Compliance Audit DTOs
# =============================================================================

class AuditCreateDTO(BaseModel):
    """Create a new compliance audit."""
    model_config = ConfigDict(from_attributes=True)

    audit_date: date = Field(..., description="Date of audit")
    auditor_name: str = Field(..., min_length=1, max_length=200)
    audit_type: AuditType = Field(...)
    next_audit_date: Optional[date] = None


class AuditUpdateDTO(BaseModel):
    """Update audit details."""
    model_config = ConfigDict(from_attributes=True)

    auditor_name: Optional[str] = Field(None, max_length=200)
    findings_summary: Optional[str] = Field(None, max_length=5000)
    next_audit_date: Optional[date] = None


class AuditStatusUpdateDTO(BaseModel):
    """Update audit status."""
    model_config = ConfigDict(from_attributes=True)

    status: AuditStatus = Field(...)
    findings_summary: Optional[str] = Field(None, max_length=5000)


class AuditDTO(BaseModel):
    """Compliance audit response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_date: date
    auditor_name: str
    audit_type: AuditType
    status: AuditStatus
    overall_score: Optional[float] = None
    findings_summary: Optional[str] = None
    corrective_actions_required: int
    next_audit_date: Optional[date] = None
    created_by: UUID
    creator_name: Optional[str] = None

    # Counts
    total_findings: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    partial_count: int = 0

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class AuditListDTO(BaseModel):
    """Minimal audit info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_date: date
    auditor_name: str
    audit_type: AuditType
    status: AuditStatus
    overall_score: Optional[float] = None
    corrective_actions_required: int


# =============================================================================
# Audit Finding DTOs
# =============================================================================

class FindingCreateDTO(BaseModel):
    """Create an audit finding."""
    model_config = ConfigDict(from_attributes=True)

    standard_id: UUID = Field(..., description="Standard being evaluated")
    compliance_status: ComplianceStatus = Field(...)
    evidence_provided: Optional[str] = Field(None, max_length=2000)
    finding_notes: Optional[str] = Field(None, max_length=2000)
    corrective_action: Optional[str] = Field(None, max_length=2000)
    corrective_action_due: Optional[date] = None


class FindingUpdateDTO(BaseModel):
    """Update a finding."""
    model_config = ConfigDict(from_attributes=True)

    compliance_status: Optional[ComplianceStatus] = None
    evidence_provided: Optional[str] = Field(None, max_length=2000)
    finding_notes: Optional[str] = Field(None, max_length=2000)
    corrective_action: Optional[str] = Field(None, max_length=2000)
    corrective_action_due: Optional[date] = None


class FindingCompleteDTO(BaseModel):
    """Complete a corrective action."""
    model_config = ConfigDict(from_attributes=True)

    completion_notes: Optional[str] = Field(None, max_length=1000)


class FindingDTO(BaseModel):
    """Audit finding response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_id: UUID
    standard_id: UUID
    standard_number: Optional[str] = None
    standard_title: Optional[str] = None
    standard_category: Optional[ACACategory] = None
    is_mandatory: Optional[bool] = None
    compliance_status: ComplianceStatus
    evidence_provided: Optional[str] = None
    finding_notes: Optional[str] = None
    corrective_action: Optional[str] = None
    corrective_action_due: Optional[date] = None
    corrective_action_completed: Optional[date] = None
    is_overdue: bool = False
    verified_by: Optional[UUID] = None
    verifier_name: Optional[str] = None

    # Timestamps
    inserted_date: datetime
    updated_date: Optional[datetime] = None


class FindingListDTO(BaseModel):
    """Minimal finding info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    standard_number: str
    standard_title: str
    compliance_status: ComplianceStatus
    corrective_action_due: Optional[date] = None
    is_overdue: bool = False


# =============================================================================
# Overdue Corrective Action DTO
# =============================================================================

class OverdueActionDTO(BaseModel):
    """Overdue corrective action."""
    model_config = ConfigDict(from_attributes=True)

    finding_id: UUID
    audit_id: UUID
    audit_date: date
    audit_type: AuditType
    standard_number: str
    standard_title: str
    category: ACACategory
    is_mandatory: bool
    corrective_action: str
    corrective_action_due: date
    days_overdue: int


# =============================================================================
# Compliance Report DTOs (Aggregated Data)
# =============================================================================

class InmateStatisticsDTO(BaseModel):
    """Inmate statistics for compliance report."""
    model_config = ConfigDict(from_attributes=True)

    total_inmates: int
    by_status: dict  # Status -> count
    by_security_level: dict  # Level -> count
    average_age: float


class IncidentStatisticsDTO(BaseModel):
    """Incident statistics for compliance report."""
    model_config = ConfigDict(from_attributes=True)

    total_incidents_year: int
    by_type: dict  # Type -> count
    by_severity: dict  # Severity -> count
    average_resolution_days: float


class TrainingStatisticsDTO(BaseModel):
    """Training compliance statistics."""
    model_config = ConfigDict(from_attributes=True)

    total_staff: int
    training_completion_rate: float
    certifications_current: int
    certifications_expired: int
    certifications_expiring_30_days: int


class HealthcareStatisticsDTO(BaseModel):
    """Healthcare statistics for compliance report."""
    model_config = ConfigDict(from_attributes=True)

    inmates_with_medical_records: int
    intake_screenings_completed: int
    mental_health_flagged: int
    on_suicide_watch: int
    medication_compliance_rate: float


class ProgrammeStatisticsDTO(BaseModel):
    """Programme participation statistics."""
    model_config = ConfigDict(from_attributes=True)

    total_programmes: int
    active_enrollments: int
    completion_rate: float
    btvi_certifications_issued: int


class ComplianceReportDTO(BaseModel):
    """Comprehensive compliance report aggregating all modules."""
    model_config = ConfigDict(from_attributes=True)

    report_date: date
    facility_name: str

    # Overall compliance
    overall_compliance_score: float
    mandatory_standards_met: int
    mandatory_standards_total: int
    non_mandatory_standards_met: int
    non_mandatory_standards_total: int

    # Statistics from each module
    inmate_statistics: InmateStatisticsDTO
    incident_statistics: IncidentStatisticsDTO
    training_statistics: TrainingStatisticsDTO
    healthcare_statistics: HealthcareStatisticsDTO
    programme_statistics: ProgrammeStatisticsDTO

    # Compliance by category
    by_category: dict  # Category -> {compliant, non_compliant, partial, total}

    # Corrective actions
    open_corrective_actions: int
    overdue_corrective_actions: int

    # Recent audits
    last_audit_date: Optional[date] = None
    last_audit_score: Optional[float] = None
    next_scheduled_audit: Optional[date] = None


# =============================================================================
# Dashboard DTO
# =============================================================================

class ComplianceDashboardDTO(BaseModel):
    """Compliance dashboard summary."""
    model_config = ConfigDict(from_attributes=True)

    # Overall status
    overall_compliance_score: float
    mandatory_compliance_rate: float

    # Standards summary
    total_standards: int
    mandatory_standards: int

    # Audit status
    audits_this_year: int
    last_audit_date: Optional[date] = None
    last_audit_type: Optional[AuditType] = None
    last_audit_score: Optional[float] = None
    next_scheduled_audit: Optional[date] = None

    # Corrective actions
    open_corrective_actions: int
    overdue_corrective_actions: int
    corrective_actions_completed_month: int

    # Category breakdown
    compliance_by_category: dict  # Category -> compliance percentage

    # Alerts
    alerts: List[str]
