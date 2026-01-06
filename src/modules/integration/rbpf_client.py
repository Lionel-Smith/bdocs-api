"""
RBPF Client - Stub/Mock client for Royal Bahamas Police Force integration.

This is a STUB IMPLEMENTATION that returns mock data for development and testing.
TODO comments mark where real RBPF API integration would connect.

Environment Variables (stubbed):
- RBPF_API_URL: Base URL for RBPF API
- RBPF_API_KEY: Authentication key for RBPF API
- RBPF_TIMEOUT: Request timeout in seconds (default: 30)

When the real RBPF API becomes available:
1. Replace mock methods with actual HTTP calls
2. Implement proper authentication handling
3. Add response validation against actual API schema
4. Configure retry logic for production reliability
"""
import os
import random
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import asyncio

from src.modules.integration.dtos import (
    PersonLookupRequest, PersonLookupResponse, CriminalRecordEntry,
    WarrantCheckRequest, WarrantCheckResponse, WarrantEntry,
    BookingNotificationRequest, ReleaseNotificationRequest, NotificationResponse
)

# =============================================================================
# Configuration (stubbed - would come from environment)
# =============================================================================

# TODO: Load from environment variables when real API available
RBPF_API_URL = os.getenv('RBPF_API_URL', 'https://api.rbpf.gov.bs/v1')
RBPF_API_KEY = os.getenv('RBPF_API_KEY', 'stub-api-key-not-real')
RBPF_TIMEOUT = int(os.getenv('RBPF_TIMEOUT', '30'))

# Simulation settings for stub
SIMULATE_LATENCY = True
MIN_LATENCY_MS = 100
MAX_LATENCY_MS = 500


class RBPFClientError(Exception):
    """Exception for RBPF client errors."""
    pass


class RBPFTimeoutError(RBPFClientError):
    """Exception for RBPF timeout errors."""
    pass


class RBPFClient:
    """
    Stub client for RBPF (Royal Bahamas Police Force) API integration.

    This client provides mock implementations that return realistic
    test data. All methods simulate network latency and occasional
    failures to test error handling.

    TODO: Replace stub implementations with real HTTP client when
    RBPF API specifications and access are provided.
    """

    def __init__(self):
        self.base_url = RBPF_API_URL
        self.api_key = RBPF_API_KEY
        self.timeout = RBPF_TIMEOUT

        # TODO: Initialize HTTP client (e.g., aiohttp.ClientSession)
        # self.session = aiohttp.ClientSession(
        #     base_url=self.base_url,
        #     headers={'Authorization': f'Bearer {self.api_key}'},
        #     timeout=aiohttp.ClientTimeout(total=self.timeout)
        # )

    async def _simulate_latency(self) -> None:
        """Simulate network latency for realistic testing."""
        if SIMULATE_LATENCY:
            latency = random.randint(MIN_LATENCY_MS, MAX_LATENCY_MS) / 1000
            await asyncio.sleep(latency)

    async def _simulate_occasional_failure(self, failure_rate: float = 0.05) -> None:
        """Simulate occasional failures for error handling testing."""
        if random.random() < failure_rate:
            raise RBPFClientError("Simulated RBPF API error for testing")

    # =========================================================================
    # Person Lookup
    # =========================================================================

    async def lookup_person(
        self,
        request: PersonLookupRequest
    ) -> PersonLookupResponse:
        """
        Look up a person by NIB number in RBPF system.

        TODO: Replace with actual HTTP call:
        ```
        async with self.session.get(
            '/persons/lookup',
            params={'nib': request.nib_number}
        ) as response:
            data = await response.json()
            return PersonLookupResponse(**data)
        ```

        Args:
            request: PersonLookupRequest with NIB number

        Returns:
            PersonLookupResponse with criminal history if found
        """
        await self._simulate_latency()
        await self._simulate_occasional_failure()

        # STUB: Generate mock data based on NIB
        # In reality, this would query RBPF database

        # Use NIB hash to deterministically generate mock data
        nib_hash = hash(request.nib_number) % 100

        # 70% chance person is found
        if nib_hash < 70:
            # Generate mock criminal history (30% have records)
            criminal_history = None
            if nib_hash < 30:
                criminal_history = self._generate_mock_criminal_history(nib_hash)

            return PersonLookupResponse(
                found=True,
                nib_number=request.nib_number,
                first_name=self._generate_mock_name(nib_hash, 'first'),
                last_name=self._generate_mock_name(nib_hash, 'last'),
                date_of_birth=date(1980 + (nib_hash % 30), (nib_hash % 12) + 1, (nib_hash % 28) + 1),
                aliases=None if nib_hash > 20 else [f"AKA_{nib_hash}"],
                criminal_history=criminal_history,
                last_known_address=f"{nib_hash * 10} Mock Street, Nassau, Bahamas",
                rbpf_id=f"RBPF-{nib_hash:06d}"
            )
        else:
            return PersonLookupResponse(
                found=False,
                nib_number=request.nib_number
            )

    def _generate_mock_name(self, seed: int, name_type: str) -> str:
        """Generate deterministic mock name."""
        first_names = [
            "John", "Mary", "James", "Patricia", "Robert", "Jennifer",
            "Michael", "Linda", "William", "Elizabeth", "David", "Barbara"
        ]
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Davis",
            "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas"
        ]

        if name_type == 'first':
            return first_names[seed % len(first_names)]
        return last_names[seed % len(last_names)]

    def _generate_mock_criminal_history(self, seed: int) -> list:
        """Generate mock criminal history records."""
        offenses = [
            "Theft", "Assault", "Drug Possession", "Burglary",
            "DUI", "Fraud", "Disorderly Conduct"
        ]
        courts = ["Magistrates Court", "Supreme Court"]
        dispositions = ["Convicted", "Probation", "Fine", "Dismissed"]

        num_records = (seed % 3) + 1
        records = []

        for i in range(num_records):
            records.append(CriminalRecordEntry(
                offense=offenses[(seed + i) % len(offenses)],
                offense_date=date.today() - timedelta(days=365 * (i + 1) + seed),
                court=courts[(seed + i) % len(courts)],
                case_number=f"CR-{2020 - i}-{seed:04d}",
                disposition=dispositions[(seed + i) % len(dispositions)],
                sentence="6 months imprisonment" if (seed + i) % 4 == 0 else None
            ))

        return records

    # =========================================================================
    # Warrant Check
    # =========================================================================

    async def check_warrants(
        self,
        request: WarrantCheckRequest
    ) -> WarrantCheckResponse:
        """
        Check for active warrants against a person.

        TODO: Replace with actual HTTP call:
        ```
        async with self.session.post(
            '/warrants/check',
            json=request.model_dump()
        ) as response:
            data = await response.json()
            return WarrantCheckResponse(**data)
        ```

        Args:
            request: WarrantCheckRequest with name and DOB

        Returns:
            WarrantCheckResponse with active warrants if any
        """
        await self._simulate_latency()
        await self._simulate_occasional_failure()

        # STUB: Generate mock warrant data
        # Use name hash to deterministically generate mock data
        name_hash = hash(f"{request.first_name}{request.last_name}") % 100

        # 15% chance of having warrants
        if name_hash < 15:
            warrant_count = (name_hash % 2) + 1
            warrants = []

            for i in range(warrant_count):
                warrant_types = ["ARREST", "BENCH"]
                offenses = ["Failure to Appear", "Probation Violation", "Outstanding Fines"]

                warrants.append(WarrantEntry(
                    warrant_number=f"W-{2024}-{name_hash:04d}-{i}",
                    warrant_type=warrant_types[i % len(warrant_types)],
                    issue_date=date.today() - timedelta(days=30 * (i + 1)),
                    issuing_court="Magistrates Court, Nassau",
                    offense=offenses[i % len(offenses)],
                    status="ACTIVE"
                ))

            return WarrantCheckResponse(
                has_warrants=True,
                warrant_count=warrant_count,
                warrants=warrants,
                last_checked=datetime.utcnow()
            )
        else:
            return WarrantCheckResponse(
                has_warrants=False,
                warrant_count=0,
                warrants=None,
                last_checked=datetime.utcnow()
            )

    # =========================================================================
    # Booking Notification
    # =========================================================================

    async def notify_booking(
        self,
        request: BookingNotificationRequest
    ) -> NotificationResponse:
        """
        Notify RBPF of a new inmate booking.

        TODO: Replace with actual HTTP call:
        ```
        async with self.session.post(
            '/notifications/booking',
            json=request.model_dump(mode='json')
        ) as response:
            data = await response.json()
            return NotificationResponse(**data)
        ```

        Args:
            request: BookingNotificationRequest with inmate details

        Returns:
            NotificationResponse with acknowledgment
        """
        await self._simulate_latency()
        await self._simulate_occasional_failure(failure_rate=0.02)  # Lower failure rate

        # STUB: Simulate successful notification
        return NotificationResponse(
            acknowledged=True,
            reference_number=f"RBPF-BK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
            timestamp=datetime.utcnow(),
            message=f"Booking notification received for {request.booking_number}"
        )

    # =========================================================================
    # Release Notification
    # =========================================================================

    async def notify_release(
        self,
        request: ReleaseNotificationRequest
    ) -> NotificationResponse:
        """
        Notify RBPF of an inmate release.

        TODO: Replace with actual HTTP call:
        ```
        async with self.session.post(
            '/notifications/release',
            json=request.model_dump(mode='json')
        ) as response:
            data = await response.json()
            return NotificationResponse(**data)
        ```

        Args:
            request: ReleaseNotificationRequest with release details

        Returns:
            NotificationResponse with acknowledgment
        """
        await self._simulate_latency()
        await self._simulate_occasional_failure(failure_rate=0.02)

        # STUB: Simulate successful notification
        return NotificationResponse(
            acknowledged=True,
            reference_number=f"RBPF-RL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
            timestamp=datetime.utcnow(),
            message=f"Release notification received for {request.booking_number}"
        )

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> bool:
        """
        Check if RBPF API is reachable.

        TODO: Replace with actual health endpoint call:
        ```
        try:
            async with self.session.get('/health') as response:
                return response.status == 200
        except Exception:
            return False
        ```

        Returns:
            True if API is healthy, False otherwise
        """
        await self._simulate_latency()

        # STUB: 95% chance of being healthy
        return random.random() < 0.95

    async def close(self) -> None:
        """
        Close the HTTP client session.

        TODO: Implement proper cleanup:
        ```
        await self.session.close()
        ```
        """
        pass  # STUB: No cleanup needed for mock


# Singleton instance for reuse
_client: Optional[RBPFClient] = None


def get_rbpf_client() -> RBPFClient:
    """Get or create RBPF client instance."""
    global _client
    if _client is None:
        _client = RBPFClient()
    return _client
