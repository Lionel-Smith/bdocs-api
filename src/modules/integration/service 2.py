"""
Integration Service - Business logic for external system integrations.

Wraps RBPF client with:
- Request/response logging to ExternalSystemLog
- Retry logic with exponential backoff
- Error handling and status tracking
- Health monitoring

All integration requests are logged for audit compliance and debugging.
"""
import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.integration.models import ExternalSystemLog
from src.modules.integration.repository import ExternalSystemLogRepository
from src.modules.integration.rbpf_client import (
    RBPFClient, get_rbpf_client, RBPFClientError, RBPFTimeoutError
)
from src.modules.integration.dtos import (
    PersonLookupRequest, PersonLookupResponse,
    WarrantCheckRequest, WarrantCheckResponse,
    BookingNotificationRequest, ReleaseNotificationRequest, NotificationResponse,
    IntegrationHealthDTO, SystemHealthDTO
)
from src.common.enums import RequestType, IntegrationStatus


# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds
RETRY_DELAY_MAX = 10.0  # Maximum delay in seconds


class IntegrationService:
    """Service for external system integration operations."""

    SYSTEM_RBPF = "RBPF"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.log_repo = ExternalSystemLogRepository(session)
        self.rbpf_client = get_rbpf_client()

    # =========================================================================
    # Logging Helpers
    # =========================================================================

    async def _create_log(
        self,
        system_name: str,
        request_type: RequestType,
        request_payload: dict,
        initiated_by: UUID,
        correlation_id: Optional[UUID] = None
    ) -> ExternalSystemLog:
        """Create a new log entry for an integration request."""
        log = ExternalSystemLog(
            id=uuid4(),
            system_name=system_name,
            request_type=request_type,
            request_payload=request_payload,
            status=IntegrationStatus.PENDING,
            request_time=datetime.utcnow(),
            correlation_id=correlation_id or uuid4(),
            initiated_by=initiated_by
        )
        return await self.log_repo.create(log)

    async def _update_log_success(
        self,
        log: ExternalSystemLog,
        response_payload: dict
    ) -> ExternalSystemLog:
        """Update log entry with successful response."""
        log.status = IntegrationStatus.SUCCESS
        log.response_time = datetime.utcnow()
        log.response_payload = response_payload
        return await self.log_repo.update(log)

    async def _update_log_failure(
        self,
        log: ExternalSystemLog,
        error_message: str,
        is_timeout: bool = False
    ) -> ExternalSystemLog:
        """Update log entry with failure details."""
        log.status = IntegrationStatus.TIMEOUT if is_timeout else IntegrationStatus.FAILED
        log.response_time = datetime.utcnow()
        log.error_message = error_message
        return await self.log_repo.update(log)

    # =========================================================================
    # Retry Logic
    # =========================================================================

    async def _execute_with_retry(
        self,
        operation,
        log: ExternalSystemLog,
        max_retries: int = MAX_RETRIES
    ):
        """
        Execute an operation with exponential backoff retry.

        Args:
            operation: Async callable to execute
            log: Log entry to update on success/failure
            max_retries: Maximum retry attempts

        Returns:
            Result of operation if successful

        Raises:
            RBPFClientError: If all retries exhausted
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await operation()
                return result

            except RBPFTimeoutError as e:
                last_error = e
                await self._update_log_failure(log, str(e), is_timeout=True)
                # Don't retry timeouts immediately
                break

            except RBPFClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = min(
                        RETRY_DELAY_BASE * (2 ** attempt),
                        RETRY_DELAY_MAX
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    await self._update_log_failure(log, str(e))
                    break

            except Exception as e:
                last_error = e
                await self._update_log_failure(log, f"Unexpected error: {str(e)}")
                break

        raise last_error if last_error else RBPFClientError("Operation failed")

    # =========================================================================
    # RBPF Person Lookup
    # =========================================================================

    async def lookup_person(
        self,
        request: PersonLookupRequest,
        initiated_by: UUID,
        correlation_id: Optional[UUID] = None
    ) -> PersonLookupResponse:
        """
        Look up a person in RBPF system by NIB number.

        Creates audit log, calls RBPF with retry, and updates log with result.

        Args:
            request: PersonLookupRequest with NIB number
            initiated_by: UUID of staff member initiating request
            correlation_id: Optional correlation ID for tracking

        Returns:
            PersonLookupResponse with criminal history if found
        """
        # Sanitize payload for logging (don't log full NIB in some cases)
        sanitized_payload = {
            'nib_number': request.nib_number[:5] + '****',
            'request_type': 'INMATE_LOOKUP'
        }

        log = await self._create_log(
            system_name=self.SYSTEM_RBPF,
            request_type=RequestType.INMATE_LOOKUP,
            request_payload=sanitized_payload,
            initiated_by=initiated_by,
            correlation_id=correlation_id
        )

        async def operation():
            return await self.rbpf_client.lookup_person(request)

        result = await self._execute_with_retry(operation, log)

        # Update log with response
        response_payload = result.model_dump(mode='json')
        await self._update_log_success(log, response_payload)

        return result

    # =========================================================================
    # RBPF Warrant Check
    # =========================================================================

    async def check_warrants(
        self,
        request: WarrantCheckRequest,
        initiated_by: UUID,
        correlation_id: Optional[UUID] = None
    ) -> WarrantCheckResponse:
        """
        Check for active warrants in RBPF system.

        Args:
            request: WarrantCheckRequest with name and DOB
            initiated_by: UUID of staff member initiating request
            correlation_id: Optional correlation ID for tracking

        Returns:
            WarrantCheckResponse with active warrants if any
        """
        sanitized_payload = {
            'first_name': request.first_name,
            'last_name': request.last_name,
            'date_of_birth': request.date_of_birth.isoformat(),
            'request_type': 'WARRANT_CHECK'
        }

        log = await self._create_log(
            system_name=self.SYSTEM_RBPF,
            request_type=RequestType.WARRANT_CHECK,
            request_payload=sanitized_payload,
            initiated_by=initiated_by,
            correlation_id=correlation_id
        )

        async def operation():
            return await self.rbpf_client.check_warrants(request)

        result = await self._execute_with_retry(operation, log)

        response_payload = result.model_dump(mode='json')
        await self._update_log_success(log, response_payload)

        return result

    # =========================================================================
    # RBPF Booking Notification
    # =========================================================================

    async def notify_booking(
        self,
        request: BookingNotificationRequest,
        initiated_by: UUID,
        correlation_id: Optional[UUID] = None
    ) -> NotificationResponse:
        """
        Notify RBPF of a new inmate booking.

        Args:
            request: BookingNotificationRequest with inmate/booking details
            initiated_by: UUID of staff member initiating request
            correlation_id: Optional correlation ID for tracking

        Returns:
            NotificationResponse with acknowledgment
        """
        sanitized_payload = {
            'booking_number': request.booking_number,
            'first_name': request.first_name,
            'last_name': request.last_name,
            'booking_date': request.booking_date.isoformat(),
            'offense': request.offense,
            'request_type': 'BOOKING_NOTIFICATION'
        }

        log = await self._create_log(
            system_name=self.SYSTEM_RBPF,
            request_type=RequestType.BOOKING_NOTIFICATION,
            request_payload=sanitized_payload,
            initiated_by=initiated_by,
            correlation_id=correlation_id
        )

        async def operation():
            return await self.rbpf_client.notify_booking(request)

        result = await self._execute_with_retry(operation, log)

        response_payload = result.model_dump(mode='json')
        await self._update_log_success(log, response_payload)

        return result

    # =========================================================================
    # RBPF Release Notification
    # =========================================================================

    async def notify_release(
        self,
        request: ReleaseNotificationRequest,
        initiated_by: UUID,
        correlation_id: Optional[UUID] = None
    ) -> NotificationResponse:
        """
        Notify RBPF of an inmate release.

        Args:
            request: ReleaseNotificationRequest with release details
            initiated_by: UUID of staff member initiating request
            correlation_id: Optional correlation ID for tracking

        Returns:
            NotificationResponse with acknowledgment
        """
        sanitized_payload = {
            'booking_number': request.booking_number,
            'first_name': request.first_name,
            'last_name': request.last_name,
            'release_date': request.release_date.isoformat(),
            'release_type': request.release_type,
            'request_type': 'RELEASE_NOTIFICATION'
        }

        log = await self._create_log(
            system_name=self.SYSTEM_RBPF,
            request_type=RequestType.RELEASE_NOTIFICATION,
            request_payload=sanitized_payload,
            initiated_by=initiated_by,
            correlation_id=correlation_id
        )

        async def operation():
            return await self.rbpf_client.notify_release(request)

        result = await self._execute_with_retry(operation, log)

        response_payload = result.model_dump(mode='json')
        await self._update_log_success(log, response_payload)

        return result

    # =========================================================================
    # Log Access
    # =========================================================================

    async def get_log(self, log_id: UUID) -> Optional[ExternalSystemLog]:
        """Get a log entry by ID."""
        return await self.log_repo.get_by_id(log_id)

    async def get_logs_by_correlation(
        self,
        correlation_id: UUID
    ) -> List[ExternalSystemLog]:
        """Get all logs with a correlation ID."""
        return await self.log_repo.get_by_correlation_id(correlation_id)

    async def get_all_logs(
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
        return await self.log_repo.get_all(
            system_name=system_name,
            request_type=request_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )

    async def count_logs(
        self,
        system_name: Optional[str] = None,
        request_type: Optional[RequestType] = None,
        status: Optional[IntegrationStatus] = None
    ) -> int:
        """Count logs with optional filters."""
        return await self.log_repo.count(system_name, request_type, status)

    # =========================================================================
    # Health Check
    # =========================================================================

    async def get_health(self) -> IntegrationHealthDTO:
        """
        Get health status of all integrated systems.

        Returns:
            IntegrationHealthDTO with status of all systems
        """
        systems = []

        # RBPF Health
        rbpf_healthy = await self.rbpf_client.health_check()
        last_success = await self.log_repo.get_last_successful(self.SYSTEM_RBPF)
        last_failure = await self.log_repo.get_last_failed(self.SYSTEM_RBPF)
        success_rate = await self.log_repo.get_success_rate(self.SYSTEM_RBPF, hours=24)
        avg_response = await self.log_repo.get_average_response_time(self.SYSTEM_RBPF, hours=24)

        # Determine status
        if not rbpf_healthy:
            rbpf_status = "UNAVAILABLE"
        elif success_rate < 95:
            rbpf_status = "DEGRADED"
        else:
            rbpf_status = "HEALTHY"

        systems.append(SystemHealthDTO(
            system_name=self.SYSTEM_RBPF,
            status=rbpf_status,
            last_successful_request=last_success.request_time if last_success else None,
            last_failed_request=last_failure.request_time if last_failure else None,
            success_rate_24h=success_rate,
            average_response_time_ms=avg_response
        ))

        # TODO: Add other systems (COURTS, etc.) here

        # Determine overall status
        if all(s.status == "HEALTHY" for s in systems):
            overall = "HEALTHY"
        elif any(s.status == "UNAVAILABLE" for s in systems):
            overall = "UNAVAILABLE"
        else:
            overall = "DEGRADED"

        return IntegrationHealthDTO(
            overall_status=overall,
            systems=systems,
            checked_at=datetime.utcnow()
        )
