"""
BDOCS Reports Module - Report definitions, generation, and execution tracking.

This module provides a comprehensive reporting framework for generating
various reports across all BDOCS modules.

Core entities:
- ReportDefinition: Template/configuration for report types
- ReportExecution: Individual report generation records

Report categories:
- POPULATION: Daily counts, demographics, housing distribution
- INCIDENT: Date range analysis, by type, by severity
- PROGRAMME: Enrollment stats, completion rates, BTVI certifications
- COMPLIANCE: ACA compliance summaries and audit reports
- HEALTHCARE: Medical statistics (TODO)
- FINANCIAL: Budget and accounting reports (TODO)
- OPERATIONAL: General operational metrics (TODO)

Key features:
- Seeded report definitions for common report types
- Synchronous and asynchronous (queued) generation
- Quick report endpoints for real-time dashboard data
- Multiple output formats: PDF, Excel, CSV, JSON
- Execution tracking with file management
- Scheduled report support (cron expressions)

NOTE: Report generators use STUB implementations with mock data.
TODO: Connect generators to actual module repositories for real data.

Quick Reports:
- /api/v1/reports/quick/population - Real-time population snapshot
- /api/v1/reports/quick/incidents - 30-day incident summary
- /api/v1/reports/quick/programmes - YTD programme statistics

Full Reports:
- /api/v1/reports/generate/{code} - Sync generation with file output
- /api/v1/reports/queue/{code} - Async generation (background)
"""
from src.modules.reports.models import ReportDefinition, ReportExecution
from src.modules.reports.service import ReportService, ReportGenerationError
from src.modules.reports.controller import reports_bp, blueprint
from src.modules.reports.generators import (
    BaseReportGenerator,
    ReportOutput,
    PopulationReportGenerator,
    IncidentReportGenerator,
    ProgrammeReportGenerator,
    ACAReportGenerator
)

__all__ = [
    # Models
    'ReportDefinition',
    'ReportExecution',
    # Service
    'ReportService',
    'ReportGenerationError',
    # Blueprint
    'reports_bp',
    'blueprint',
    # Generators
    'BaseReportGenerator',
    'ReportOutput',
    'PopulationReportGenerator',
    'IncidentReportGenerator',
    'ProgrammeReportGenerator',
    'ACAReportGenerator',
]
