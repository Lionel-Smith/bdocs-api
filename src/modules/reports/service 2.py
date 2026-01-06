"""
Reports Service - Business logic for report generation and management.

Orchestrates report generation by:
1. Looking up report definitions
2. Dispatching to appropriate generators
3. Tracking execution status
4. Providing quick report summaries

Key methods:
- generate_report(): Synchronous generation (returns when complete)
- queue_report(): Async generation (returns immediately with execution ID)
- get_report_history(): Get past executions with filters
- get_quick_*(): Real-time dashboard summaries
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reports.models import ReportDefinition, ReportExecution
from src.modules.reports.repository import ReportDefinitionRepository, ReportExecutionRepository
from src.modules.reports.dtos import (
    ReportDefinitionDTO, ReportDefinitionListDTO,
    ReportExecutionDTO, ReportExecutionListDTO,
    ReportGenerationResultDTO, ReportQueuedDTO,
    QuickPopulationReportDTO, QuickIncidentReportDTO, QuickProgrammeReportDTO
)
from src.modules.reports.generators import (
    PopulationReportGenerator,
    IncidentReportGenerator,
    ProgrammeReportGenerator,
    ACAReportGenerator,
    ReportOutput
)
from src.common.enums import ReportCategory, ReportStatus, OutputFormat


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass


class ReportService:
    """Service for report management and generation."""

    # Map categories to generator classes
    GENERATORS = {
        ReportCategory.POPULATION: PopulationReportGenerator,
        ReportCategory.INCIDENT: IncidentReportGenerator,
        ReportCategory.PROGRAMME: ProgrammeReportGenerator,
        ReportCategory.COMPLIANCE: ACAReportGenerator,
        # Healthcare, Financial, Operational would use generic or specialized generators
        # TODO: Add generators for remaining categories
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.definition_repo = ReportDefinitionRepository(session)
        self.execution_repo = ReportExecutionRepository(session)

    # =========================================================================
    # Report Definition Methods
    # =========================================================================

    async def get_definition(self, definition_id: UUID) -> Optional[ReportDefinitionDTO]:
        """Get report definition by ID."""
        definition = await self.definition_repo.get_by_id(definition_id)
        if not definition:
            return None
        return self._to_definition_dto(definition)

    async def get_definition_by_code(self, code: str) -> Optional[ReportDefinitionDTO]:
        """Get report definition by code."""
        definition = await self.definition_repo.get_by_code(code)
        if not definition:
            return None
        return self._to_definition_dto(definition)

    async def get_all_definitions(
        self,
        category: Optional[ReportCategory] = None,
        is_scheduled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportDefinitionListDTO]:
        """Get all report definitions with optional filters."""
        definitions = await self.definition_repo.get_all(
            category=category,
            is_scheduled=is_scheduled,
            skip=skip,
            limit=limit
        )
        return [self._to_definition_list_dto(d) for d in definitions]

    async def count_definitions(
        self,
        category: Optional[ReportCategory] = None
    ) -> int:
        """Count report definitions."""
        return await self.definition_repo.count(category)

    # =========================================================================
    # Report Generation Methods
    # =========================================================================

    async def generate_report(
        self,
        code: str,
        parameters: Optional[Dict[str, Any]] = None,
        output_format: Optional[OutputFormat] = None,
        requested_by: UUID = None
    ) -> ReportGenerationResultDTO:
        """
        Generate a report synchronously.

        Looks up the definition, creates an execution record, runs the
        appropriate generator, and returns the result.

        Args:
            code: Report definition code (e.g., 'RPT-POP-001')
            parameters: Optional parameters for the report
            output_format: Override default output format
            requested_by: User ID requesting the report

        Returns:
            ReportGenerationResultDTO with file path and status
        """
        # Get definition
        definition = await self.definition_repo.get_by_code(code)
        if not definition:
            raise ReportGenerationError(f"Report definition not found: {code}")

        # Use default format if not specified
        if not output_format:
            output_format = definition.output_format

        # Create execution record
        execution = ReportExecution(
            report_definition_id=definition.id,
            parameters=parameters,
            status=ReportStatus.GENERATING,
            started_at=datetime.utcnow(),
            requested_by=requested_by or UUID('00000000-0000-0000-0000-000000000000')
        )
        execution = await self.execution_repo.create(execution)

        try:
            # Get appropriate generator
            generator_class = self.GENERATORS.get(definition.category)
            if not generator_class:
                raise ReportGenerationError(
                    f"No generator available for category: {definition.category.value}"
                )

            # Generate report
            generator = generator_class()
            params = parameters or {}
            params['report_code'] = code

            output: ReportOutput = await generator.generate(params, output_format)

            # Update execution with success
            execution.status = ReportStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.file_path = output.file_path
            execution.file_size_bytes = output.file_size_bytes
            await self.execution_repo.update(execution)

            # Update definition last_generated
            await self.definition_repo.update_last_generated(
                definition.id,
                datetime.utcnow()
            )

            return ReportGenerationResultDTO(
                execution_id=execution.id,
                status=ReportStatus.COMPLETED,
                file_path=output.file_path,
                file_size_bytes=output.file_size_bytes,
                duration_seconds=execution.duration_seconds
            )

        except Exception as e:
            # Update execution with failure
            execution.status = ReportStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)
            await self.execution_repo.update(execution)

            return ReportGenerationResultDTO(
                execution_id=execution.id,
                status=ReportStatus.FAILED,
                error_message=str(e)
            )

    async def queue_report(
        self,
        code: str,
        parameters: Optional[Dict[str, Any]] = None,
        output_format: Optional[OutputFormat] = None,
        requested_by: UUID = None
    ) -> ReportQueuedDTO:
        """
        Queue a report for async generation.

        Creates an execution record with QUEUED status. A background worker
        would pick this up and run generate_report().

        NOTE: Background processing is not implemented in this stub.
        TODO: Integrate with Celery/Redis for actual async processing.
        """
        definition = await self.definition_repo.get_by_code(code)
        if not definition:
            raise ReportGenerationError(f"Report definition not found: {code}")

        # Create queued execution
        execution = ReportExecution(
            report_definition_id=definition.id,
            parameters=parameters,
            status=ReportStatus.QUEUED,
            started_at=datetime.utcnow(),
            requested_by=requested_by or UUID('00000000-0000-0000-0000-000000000000')
        )
        execution = await self.execution_repo.create(execution)

        # TODO: Push to task queue (Celery, Redis, etc.)
        # For now, this is just a stub that creates the queued record

        return ReportQueuedDTO(
            execution_id=execution.id,
            report_code=code,
            status=ReportStatus.QUEUED,
            message="Report queued for generation. Check execution status for updates.",
            estimated_completion=datetime.utcnow() + timedelta(minutes=5)
        )

    # =========================================================================
    # Report Execution/History Methods
    # =========================================================================

    async def get_execution(self, execution_id: UUID) -> Optional[ReportExecutionDTO]:
        """Get report execution by ID."""
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            return None
        return self._to_execution_dto(execution)

    async def get_report_history(
        self,
        report_definition_id: Optional[UUID] = None,
        status: Optional[ReportStatus] = None,
        requested_by: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportExecutionListDTO]:
        """Get report execution history with filters."""
        executions = await self.execution_repo.get_all(
            report_definition_id=report_definition_id,
            status=status,
            requested_by=requested_by,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return [self._to_execution_list_dto(e) for e in executions]

    async def get_user_history(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[ReportExecutionListDTO]:
        """Get report history for a specific user."""
        executions = await self.execution_repo.get_user_history(
            user_id, skip=skip, limit=limit
        )
        return [self._to_execution_list_dto(e) for e in executions]

    async def count_executions(
        self,
        report_definition_id: Optional[UUID] = None,
        status: Optional[ReportStatus] = None,
        requested_by: Optional[UUID] = None
    ) -> int:
        """Count report executions."""
        return await self.execution_repo.count(
            report_definition_id=report_definition_id,
            status=status,
            requested_by=requested_by
        )

    async def get_execution_stats(
        self,
        definition_id: UUID
    ) -> Dict[str, Any]:
        """Get execution statistics for a report definition."""
        return await self.execution_repo.get_stats_by_definition(definition_id)

    # =========================================================================
    # Quick Report Methods (no file generation)
    # =========================================================================

    async def get_quick_population(
        self,
        as_of_date: Optional[date] = None
    ) -> QuickPopulationReportDTO:
        """Get quick population summary without file generation."""
        from src.modules.reports.generators.population_report import get_quick_population_summary

        data = await get_quick_population_summary(as_of_date)

        return QuickPopulationReportDTO(
            as_of_date=date.fromisoformat(data['as_of_date']),
            total_population=data['total_population'],
            by_status=data['by_status'],
            by_security_level=data['by_security_level'],
            by_housing_unit=data['by_housing_unit'],
            by_gender=data['by_gender'],
            average_age=data['average_age'],
            average_sentence_months=data.get('average_sentence_months')
        )

    async def get_quick_incidents(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> QuickIncidentReportDTO:
        """Get quick incident summary without file generation."""
        from src.modules.reports.generators.incident_report import get_quick_incident_summary

        data = await get_quick_incident_summary(start_date, end_date)

        return QuickIncidentReportDTO(
            start_date=date.fromisoformat(data['start_date']),
            end_date=date.fromisoformat(data['end_date']),
            total_incidents=data['total_incidents'],
            by_type=data['by_type'],
            by_severity=data['by_severity'],
            by_status=data['by_status'],
            daily_average=data['daily_average'],
            most_common_type=data['most_common_type'],
            highest_severity_count=data['highest_severity_count']
        )

    async def get_quick_programmes(self) -> QuickProgrammeReportDTO:
        """Get quick programme summary without file generation."""
        from src.modules.reports.generators.programme_report import get_quick_programme_summary

        data = await get_quick_programme_summary()

        return QuickProgrammeReportDTO(
            total_programmes=data['total_programmes'],
            total_enrolled=data['total_enrolled'],
            total_completed_ytd=data['total_completed_ytd'],
            completion_rate=data['completion_rate'],
            btvi_certifications_ytd=data['btvi_certifications_ytd'],
            by_programme_type=data['by_programme_type'],
            top_programmes=data['top_programmes']
        )

    # =========================================================================
    # DTO Conversion Helpers
    # =========================================================================

    def _to_definition_dto(self, definition: ReportDefinition) -> ReportDefinitionDTO:
        """Convert ReportDefinition model to DTO."""
        return ReportDefinitionDTO(
            id=definition.id,
            code=definition.code,
            name=definition.name,
            description=definition.description,
            category=definition.category,
            parameters_schema=definition.parameters_schema,
            output_format=definition.output_format,
            is_scheduled=definition.is_scheduled,
            schedule_cron=definition.schedule_cron,
            last_generated=definition.last_generated,
            created_by=definition.created_by,
            creator_name=definition.creator.full_name if definition.creator else None
        )

    def _to_definition_list_dto(self, definition: ReportDefinition) -> ReportDefinitionListDTO:
        """Convert ReportDefinition model to list DTO."""
        return ReportDefinitionListDTO(
            id=definition.id,
            code=definition.code,
            name=definition.name,
            category=definition.category,
            output_format=definition.output_format,
            is_scheduled=definition.is_scheduled,
            last_generated=definition.last_generated
        )

    def _to_execution_dto(self, execution: ReportExecution) -> ReportExecutionDTO:
        """Convert ReportExecution model to DTO."""
        return ReportExecutionDTO(
            id=execution.id,
            report_definition_id=execution.report_definition_id,
            report_code=execution.definition.code if execution.definition else 'unknown',
            report_name=execution.definition.name if execution.definition else 'Unknown Report',
            parameters=execution.parameters,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            file_path=execution.file_path,
            file_size_bytes=execution.file_size_bytes,
            error_message=execution.error_message,
            requested_by=execution.requested_by,
            requester_name=execution.requester.full_name if execution.requester else None,
            duration_seconds=execution.duration_seconds
        )

    def _to_execution_list_dto(self, execution: ReportExecution) -> ReportExecutionListDTO:
        """Convert ReportExecution model to list DTO."""
        return ReportExecutionListDTO(
            id=execution.id,
            report_code=execution.definition.code if execution.definition else 'unknown',
            report_name=execution.definition.name if execution.definition else 'Unknown Report',
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_seconds=execution.duration_seconds,
            requested_by=execution.requested_by,
            requester_name=execution.requester.full_name if execution.requester else None
        )
