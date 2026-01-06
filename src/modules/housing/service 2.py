"""
Housing Service - Business logic for housing and classification.

Key business rules:
- Classification score thresholds: MAXIMUM>=20, MEDIUM>=12, MINIMUM<12
- Only one current assignment/classification per inmate
- Occupancy counts must be maintained on assignments
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import SecurityLevel
from src.modules.housing.models import HousingUnit, Classification, HousingAssignment
from src.modules.housing.repository import (
    HousingUnitRepository,
    ClassificationRepository,
    HousingAssignmentRepository
)
from src.modules.housing.dtos import (
    HousingUnitCreate,
    HousingUnitUpdate,
    HousingUnitResponse,
    ClassificationCreate,
    ClassificationScores,
    ClassificationResponse,
    HousingAssignmentCreate,
    HousingAssignmentResponse,
    HousingAssignmentEnd,
    InmateHousingSummary,
    OvercrowdedUnitReport,
)


class HousingServiceError(Exception):
    """Base exception for housing service errors."""
    pass


class HousingUnitNotFoundError(HousingServiceError):
    """Raised when housing unit is not found."""
    pass


class InmateNotFoundError(HousingServiceError):
    """Raised when inmate is not found."""
    pass


class AssignmentNotFoundError(HousingServiceError):
    """Raised when assignment is not found."""
    pass


class InvalidAssignmentError(HousingServiceError):
    """Raised when assignment is invalid."""
    pass


def calculate_security_level(scores: ClassificationScores) -> SecurityLevel:
    """
    Calculate security level from classification scores.

    Thresholds:
    - MAXIMUM: total score >= 20
    - MEDIUM: total score >= 12
    - MINIMUM: total score < 12
    """
    total = scores.total
    if total >= 20:
        return SecurityLevel.MAXIMUM
    elif total >= 12:
        return SecurityLevel.MEDIUM
    else:
        return SecurityLevel.MINIMUM


class HousingService:
    """Service layer for housing operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.unit_repo = HousingUnitRepository(session)
        self.classification_repo = ClassificationRepository(session)
        self.assignment_repo = HousingAssignmentRepository(session)

    # ========================================================================
    # Housing Unit Operations
    # ========================================================================

    async def get_all_units(self, include_inactive: bool = False) -> List[HousingUnitResponse]:
        """Get all housing units."""
        units = await self.unit_repo.get_all(include_inactive)
        return [HousingUnitResponse.model_validate(u) for u in units]

    async def get_unit_by_id(self, unit_id: UUID) -> HousingUnitResponse:
        """Get housing unit by ID."""
        unit = await self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise HousingUnitNotFoundError(f"Housing unit {unit_id} not found")
        return HousingUnitResponse.model_validate(unit)

    async def get_unit_by_code(self, code: str) -> HousingUnitResponse:
        """Get housing unit by code."""
        unit = await self.unit_repo.get_by_code(code)
        if not unit:
            raise HousingUnitNotFoundError(f"Housing unit {code} not found")
        return HousingUnitResponse.model_validate(unit)

    async def create_unit(
        self,
        data: HousingUnitCreate,
        created_by: Optional[str] = None
    ) -> HousingUnitResponse:
        """Create a new housing unit."""
        unit = HousingUnit(
            code=data.code.upper(),
            name=data.name,
            security_level=data.security_level,
            capacity=data.capacity,
            current_occupancy=0,
            gender_restriction=data.gender_restriction,
            is_active=True,
            is_juvenile=data.is_juvenile,
            description=data.description,
            inserted_by=created_by,
        )
        unit = await self.unit_repo.create(unit)
        return HousingUnitResponse.model_validate(unit)

    async def update_unit(
        self,
        unit_id: UUID,
        data: HousingUnitUpdate,
        updated_by: Optional[str] = None
    ) -> HousingUnitResponse:
        """Update housing unit."""
        unit = await self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise HousingUnitNotFoundError(f"Housing unit {unit_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(unit, field, value)
        unit.updated_by = updated_by

        unit = await self.unit_repo.update(unit)
        return HousingUnitResponse.model_validate(unit)

    async def get_inmates_in_unit(self, code: str) -> List[HousingAssignmentResponse]:
        """Get all inmates currently in a housing unit."""
        unit = await self.unit_repo.get_by_code(code)
        if not unit:
            raise HousingUnitNotFoundError(f"Housing unit {code} not found")

        assignments = await self.assignment_repo.get_inmates_in_unit(unit.id)
        responses = []
        for a in assignments:
            resp = HousingAssignmentResponse.model_validate(a)
            resp.housing_unit_code = unit.code
            resp.housing_unit_name = unit.name
            responses.append(resp)
        return responses

    async def get_overcrowded_units(self) -> OvercrowdedUnitReport:
        """Get report of overcrowded units."""
        overcrowded = await self.unit_repo.get_overcrowded()
        stats = await self.unit_repo.get_facility_stats()

        total_over = sum(
            max(0, u.current_occupancy - u.capacity) for u in overcrowded
        )

        occupancy_rate = 0.0
        if stats['total_capacity'] > 0:
            occupancy_rate = round(
                stats['total_population'] / stats['total_capacity'] * 100, 1
            )

        return OvercrowdedUnitReport(
            overcrowded_units=[HousingUnitResponse.model_validate(u) for u in overcrowded],
            total_over_capacity=total_over,
            facility_capacity=stats['total_capacity'],
            facility_population=stats['total_population'],
            facility_occupancy_rate=occupancy_rate
        )

    # ========================================================================
    # Classification Operations
    # ========================================================================

    async def create_classification(
        self,
        data: ClassificationCreate,
        classified_by: Optional[UUID] = None
    ) -> ClassificationResponse:
        """
        Create a new classification for an inmate.

        Automatically calculates security level from scores.
        """
        # Calculate security level
        security_level = calculate_security_level(data.scores)
        total_score = data.scores.total

        classification = Classification(
            inmate_id=data.inmate_id,
            classification_date=date.today(),
            security_level=security_level,
            scores=data.scores.model_dump(),
            total_score=total_score,
            review_date=data.review_date,
            classified_by=classified_by,
            notes=data.notes,
            is_current=True,
        )

        classification = await self.classification_repo.create(classification)
        return ClassificationResponse.model_validate(classification)

    async def get_inmate_classification(self, inmate_id: UUID) -> Optional[ClassificationResponse]:
        """Get current classification for an inmate."""
        classification = await self.classification_repo.get_current_for_inmate(inmate_id)
        if not classification:
            return None
        return ClassificationResponse.model_validate(classification)

    async def get_classification_history(self, inmate_id: UUID) -> List[ClassificationResponse]:
        """Get classification history for an inmate."""
        history = await self.classification_repo.get_history_for_inmate(inmate_id)
        return [ClassificationResponse.model_validate(c) for c in history]

    # ========================================================================
    # Housing Assignment Operations
    # ========================================================================

    async def create_assignment(
        self,
        data: HousingAssignmentCreate,
        assigned_by: Optional[UUID] = None
    ) -> HousingAssignmentResponse:
        """
        Create a new housing assignment.

        Business rules:
        - Ends any current assignment for the inmate
        - Updates occupancy counts for both units
        """
        # Get the target unit
        unit = await self.unit_repo.get_by_id(data.housing_unit_id)
        if not unit:
            raise HousingUnitNotFoundError(f"Housing unit {data.housing_unit_id} not found")

        if not unit.is_active:
            raise InvalidAssignmentError(f"Housing unit {unit.code} is not active")

        # Get current assignment to decrement old unit's occupancy
        current = await self.assignment_repo.get_current_for_inmate(data.inmate_id)
        if current:
            await self.unit_repo.decrement_occupancy(current.housing_unit_id)

        # Create new assignment
        assignment = HousingAssignment(
            inmate_id=data.inmate_id,
            housing_unit_id=data.housing_unit_id,
            cell_number=data.cell_number,
            bed_number=data.bed_number,
            assigned_date=datetime.utcnow(),
            is_current=True,
            assigned_by=assigned_by,
            reason=data.reason,
        )

        assignment = await self.assignment_repo.create(assignment)

        # Increment new unit's occupancy
        await self.unit_repo.increment_occupancy(data.housing_unit_id)

        response = HousingAssignmentResponse.model_validate(assignment)
        response.housing_unit_code = unit.code
        response.housing_unit_name = unit.name
        return response

    async def get_inmate_housing(self, inmate_id: UUID) -> InmateHousingSummary:
        """Get complete housing summary for an inmate."""
        # Get current assignment
        current_assignment = await self.assignment_repo.get_current_for_inmate(inmate_id)
        current_assignment_resp = None
        if current_assignment:
            unit = await self.unit_repo.get_by_id(current_assignment.housing_unit_id)
            current_assignment_resp = HousingAssignmentResponse.model_validate(current_assignment)
            if unit:
                current_assignment_resp.housing_unit_code = unit.code
                current_assignment_resp.housing_unit_name = unit.name

        # Get current classification
        current_classification = await self.classification_repo.get_current_for_inmate(inmate_id)
        current_classification_resp = None
        if current_classification:
            current_classification_resp = ClassificationResponse.model_validate(current_classification)

        # Get histories
        assignment_history = await self.assignment_repo.get_history_for_inmate(inmate_id)
        classification_history = await self.classification_repo.get_history_for_inmate(inmate_id)

        # Build assignment history with unit info
        assignment_history_resp = []
        for a in assignment_history:
            resp = HousingAssignmentResponse.model_validate(a)
            unit = await self.unit_repo.get_by_id(a.housing_unit_id)
            if unit:
                resp.housing_unit_code = unit.code
                resp.housing_unit_name = unit.name
            assignment_history_resp.append(resp)

        return InmateHousingSummary(
            inmate_id=inmate_id,
            current_assignment=current_assignment_resp,
            current_classification=current_classification_resp,
            assignment_history=assignment_history_resp,
            classification_history=[ClassificationResponse.model_validate(c) for c in classification_history]
        )

    async def end_assignment(
        self,
        assignment_id: UUID,
        data: HousingAssignmentEnd
    ) -> HousingAssignmentResponse:
        """End a housing assignment."""
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise AssignmentNotFoundError(f"Assignment {assignment_id} not found")

        if not assignment.is_current:
            raise InvalidAssignmentError("Assignment is already ended")

        # Decrement unit occupancy
        await self.unit_repo.decrement_occupancy(assignment.housing_unit_id)

        # End the assignment
        assignment = await self.assignment_repo.end_assignment(
            assignment_id,
            reason=data.reason
        )

        unit = await self.unit_repo.get_by_id(assignment.housing_unit_id)
        response = HousingAssignmentResponse.model_validate(assignment)
        if unit:
            response.housing_unit_code = unit.code
            response.housing_unit_name = unit.name
        return response
