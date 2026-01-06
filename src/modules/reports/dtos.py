"""
Reports Module DTOs - Data transfer objects for report requests and responses.

Organized into sections:
- Report Definition DTOs
- Report Execution DTOs
- Report Generation Request DTOs
- Quick Report Response DTOs
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.common.enums import ReportCategory, OutputFormat, ReportStatus


# =============================================================================
# Report Definition DTOs
# =============================================================================

@dataclass
class ReportDefinitionDTO:
    """Full report definition details."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    category: ReportCategory
    parameters_schema: Optional[Dict[str, Any]]
    output_format: OutputFormat
    is_scheduled: bool
    schedule_cron: Optional[str]
    last_generated: Optional[datetime]
    created_by: UUID
    creator_name: Optional[str] = None


@dataclass
class ReportDefinitionListDTO:
    """Summary for listing report definitions."""
    id: UUID
    code: str
    name: str
    category: ReportCategory
    output_format: OutputFormat
    is_scheduled: bool
    last_generated: Optional[datetime]


@dataclass
class ReportDefinitionCreateDTO:
    """DTO for creating new report definitions (admin only)."""
    code: str
    name: str
    description: Optional[str] = None
    category: ReportCategory = ReportCategory.OPERATIONAL
    parameters_schema: Optional[Dict[str, Any]] = None
    output_format: OutputFormat = OutputFormat.PDF
    is_scheduled: bool = False
    schedule_cron: Optional[str] = None


# =============================================================================
# Report Execution DTOs
# =============================================================================

@dataclass
class ReportExecutionDTO:
    """Full report execution details."""
    id: UUID
    report_definition_id: UUID
    report_code: str
    report_name: str
    parameters: Optional[Dict[str, Any]]
    status: ReportStatus
    started_at: datetime
    completed_at: Optional[datetime]
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    error_message: Optional[str]
    requested_by: UUID
    requester_name: Optional[str] = None
    duration_seconds: Optional[int] = None


@dataclass
class ReportExecutionListDTO:
    """Summary for listing report executions."""
    id: UUID
    report_code: str
    report_name: str
    status: ReportStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    requested_by: UUID
    requester_name: Optional[str] = None


@dataclass
class ReportExecutionCreateDTO:
    """DTO for creating/queuing a new report execution."""
    report_definition_id: UUID
    parameters: Optional[Dict[str, Any]] = None


# =============================================================================
# Report Generation Request DTOs
# =============================================================================

@dataclass
class GenerateReportRequest:
    """Request to generate a report by code."""
    output_format: Optional[OutputFormat] = None  # Override default
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class PopulationReportParams:
    """Parameters for population reports."""
    as_of_date: Optional[date] = None  # Defaults to today
    facility_id: Optional[UUID] = None  # All facilities if not specified
    include_demographics: bool = True
    include_housing_breakdown: bool = True
    include_security_breakdown: bool = True


@dataclass
class IncidentReportParams:
    """Parameters for incident reports."""
    start_date: date
    end_date: date
    facility_id: Optional[UUID] = None
    incident_types: Optional[List[str]] = None  # Filter by types
    severity_levels: Optional[List[str]] = None  # Filter by severity
    include_details: bool = False  # Full incident details vs summary


@dataclass
class ProgrammeReportParams:
    """Parameters for programme reports."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    programme_id: Optional[UUID] = None
    include_btvi_certs: bool = True
    include_completion_rates: bool = True
    include_enrollment_trends: bool = True


@dataclass
class ACAReportParams:
    """Parameters for ACA compliance reports."""
    audit_id: Optional[UUID] = None  # Specific audit or latest
    category: Optional[str] = None  # Filter by standard category
    include_findings: bool = True
    include_corrective_actions: bool = True


# =============================================================================
# Quick Report Response DTOs
# =============================================================================

@dataclass
class QuickPopulationReportDTO:
    """Quick population summary - no file generation."""
    as_of_date: date
    total_population: int
    by_status: Dict[str, int]  # {'ACTIVE': 100, 'RELEASED': 50, ...}
    by_security_level: Dict[str, int]  # {'MAXIMUM': 25, 'MEDIUM': 50, ...}
    by_housing_unit: Dict[str, int]  # {'Unit A': 30, 'Unit B': 45, ...}
    by_gender: Dict[str, int]
    average_age: float
    average_sentence_months: Optional[float]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuickIncidentReportDTO:
    """Quick incident summary - no file generation."""
    start_date: date
    end_date: date
    total_incidents: int
    by_type: Dict[str, int]  # {'ASSAULT': 5, 'CONTRABAND': 10, ...}
    by_severity: Dict[str, int]  # {'HIGH': 3, 'MEDIUM': 7, ...}
    by_status: Dict[str, int]  # {'OPEN': 5, 'CLOSED': 10, ...}
    daily_average: float
    most_common_type: Optional[str]
    highest_severity_count: int
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuickProgrammeReportDTO:
    """Quick programme summary - no file generation."""
    total_programmes: int
    total_enrolled: int
    total_completed_ytd: int
    completion_rate: float  # Percentage
    btvi_certifications_ytd: int
    by_programme_type: Dict[str, int]  # {'EDUCATION': 50, 'VOCATIONAL': 30, ...}
    top_programmes: List[Dict[str, Any]]  # Top 5 by enrollment
    generated_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Report Generation Result DTOs
# =============================================================================

@dataclass
class ReportGenerationResultDTO:
    """Result of report generation."""
    execution_id: UUID
    status: ReportStatus
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None


@dataclass
class ReportQueuedDTO:
    """Response when report is queued for async generation."""
    execution_id: UUID
    report_code: str
    status: ReportStatus
    message: str
    estimated_completion: Optional[datetime] = None
