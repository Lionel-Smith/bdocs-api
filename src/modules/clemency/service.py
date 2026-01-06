"""
Clemency Service - Business logic for clemency petitions.

Implements the constitutional workflow for Prerogative of Mercy:
SUBMITTED → UNDER_REVIEW → COMMITTEE_SCHEDULED →
AWAITING_MINISTER → GOVERNOR_GENERAL → GRANTED/DENIED

Key features:
- Status transition validation with workflow enforcement
- Auto-create SentenceAdjustment when clemency is GRANTED
- Status history tracking for legal documentation
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import PetitionType, PetitionStatus, AdjustmentType
from src.modules.clemency.models import ClemencyPetition, ClemencyStatusHistory
from src.modules.clemency.repository import (
    ClemencyPetitionRepository,
    ClemencyStatusHistoryRepository
)
from src.modules.clemency.dtos import (
    ClemencyPetitionCreate,
    ClemencyPetitionUpdate,
    ClemencyStatusUpdate,
    ClemencyPetitionResponse,
    ClemencyStatusHistoryResponse,
    InmateClemencySummary,
    ClemencyStatistics,
    VALID_STATUS_TRANSITIONS
)
from src.modules.sentence.models import SentenceAdjustment
from src.modules.sentence.repository import SentenceAdjustmentRepository


class ClemencyService:
    """Service for clemency petition operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.petition_repo = ClemencyPetitionRepository(session)
        self.history_repo = ClemencyStatusHistoryRepository(session)
        self.adjustment_repo = SentenceAdjustmentRepository(session)

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def create_petition(
        self,
        data: ClemencyPetitionCreate,
        created_by: Optional[UUID] = None
    ) -> ClemencyPetition:
        """
        Create a new clemency petition.

        Auto-generates petition number (CP-YYYY-NNNNN) and creates
        initial status history entry.
        """
        # Generate petition number
        petition_number = await self.petition_repo.get_next_petition_number()

        # Create petition
        petition = ClemencyPetition(
            inmate_id=data.inmate_id,
            sentence_id=data.sentence_id,
            petition_number=petition_number,
            petition_type=data.petition_type.value,
            status=PetitionStatus.SUBMITTED.value,
            filed_date=data.filed_date,
            petitioner_name=data.petitioner_name,
            petitioner_relationship=data.petitioner_relationship,
            grounds_for_clemency=data.grounds_for_clemency,
            supporting_documents=[doc.model_dump() for doc in data.supporting_documents] if data.supporting_documents else [],
            victim_notification_date=data.victim_notification_date,
            victim_response=data.victim_response,
            created_by=created_by
        )

        petition = await self.petition_repo.create(petition)

        # Create initial status history entry
        await self._record_status_change(
            petition_id=petition.id,
            from_status=None,
            to_status=PetitionStatus.SUBMITTED,
            changed_by=created_by,
            notes="Petition submitted"
        )

        return petition

    async def get_petition(self, petition_id: UUID) -> Optional[ClemencyPetition]:
        """Get petition by ID."""
        return await self.petition_repo.get(petition_id)

    async def get_petition_by_number(self, petition_number: str) -> Optional[ClemencyPetition]:
        """Get petition by petition number."""
        return await self.petition_repo.get_by_petition_number(petition_number)

    async def update_petition(
        self,
        petition_id: UUID,
        data: ClemencyPetitionUpdate
    ) -> Optional[ClemencyPetition]:
        """
        Update petition fields (non-status).

        Status changes must go through advance_status() for validation.
        """
        petition = await self.petition_repo.get(petition_id)
        if not petition:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(petition, field):
                setattr(petition, field, value)

        return await self.petition_repo.update(petition)

    async def delete_petition(self, petition_id: UUID) -> bool:
        """Soft delete a petition."""
        petition = await self.petition_repo.get(petition_id)
        if not petition:
            return False

        # Only allow deletion of non-terminal petitions
        terminal_states = [
            PetitionStatus.GRANTED.value,
            PetitionStatus.DENIED.value
        ]
        if petition.status in terminal_states:
            raise ValueError(
                f"Cannot delete petition in terminal state: {petition.status}"
            )

        return await self.petition_repo.delete(petition_id)

    # ========================================================================
    # Status Workflow
    # ========================================================================

    async def advance_status(
        self,
        petition_id: UUID,
        status_update: ClemencyStatusUpdate,
        changed_by: Optional[UUID] = None
    ) -> ClemencyPetition:
        """
        Advance petition to a new status with workflow validation.

        Validates that the transition is allowed per VALID_STATUS_TRANSITIONS.
        On GRANTED status, auto-creates a SentenceAdjustment with
        CLEMENCY_REDUCTION type.

        Args:
            petition_id: The petition to update
            status_update: New status and optional transition data
            changed_by: User making the change

        Returns:
            Updated petition

        Raises:
            ValueError: If petition not found or invalid transition
        """
        petition = await self.petition_repo.get(petition_id)
        if not petition:
            raise ValueError(f"Petition not found: {petition_id}")

        current_status = PetitionStatus(petition.status)
        new_status = status_update.status

        # Validate transition
        self._validate_transition(current_status, new_status)

        # Update status
        old_status = petition.status
        petition.status = new_status.value

        # Update transition-specific fields
        if status_update.committee_review_date:
            petition.committee_review_date = status_update.committee_review_date
        if status_update.committee_recommendation:
            petition.committee_recommendation = status_update.committee_recommendation
        if status_update.minister_review_date:
            petition.minister_review_date = status_update.minister_review_date
        if status_update.minister_recommendation:
            petition.minister_recommendation = status_update.minister_recommendation
        if status_update.governor_general_date:
            petition.governor_general_date = status_update.governor_general_date
        if status_update.decision_date:
            petition.decision_date = status_update.decision_date
        if status_update.decision_notes:
            petition.decision_notes = status_update.decision_notes
        if status_update.granted_reduction_days:
            petition.granted_reduction_days = status_update.granted_reduction_days

        # Save petition
        petition = await self.petition_repo.update(petition)

        # Record status change in history
        await self._record_status_change(
            petition_id=petition.id,
            from_status=PetitionStatus(old_status),
            to_status=new_status,
            changed_by=changed_by,
            notes=status_update.notes
        )

        # Handle GRANTED status - create sentence adjustment
        if new_status == PetitionStatus.GRANTED:
            await self._create_clemency_adjustment(petition, changed_by)

        return petition

    def _validate_transition(
        self,
        current_status: PetitionStatus,
        new_status: PetitionStatus
    ) -> None:
        """
        Validate that a status transition is allowed.

        Raises:
            ValueError: If transition is not valid
        """
        allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in allowed_transitions:
            allowed_str = ", ".join([s.value for s in allowed_transitions]) or "none"
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}. "
                f"Allowed transitions: {allowed_str}"
            )

    async def _record_status_change(
        self,
        petition_id: UUID,
        from_status: Optional[PetitionStatus],
        to_status: PetitionStatus,
        changed_by: Optional[UUID],
        notes: Optional[str]
    ) -> ClemencyStatusHistory:
        """Record a status change in the history table."""
        history = ClemencyStatusHistory(
            petition_id=petition_id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            changed_date=datetime.utcnow(),
            changed_by=changed_by,
            notes=notes
        )
        return await self.history_repo.create(history)

    async def _create_clemency_adjustment(
        self,
        petition: ClemencyPetition,
        approved_by: Optional[UUID]
    ) -> SentenceAdjustment:
        """
        Create a sentence adjustment when clemency is granted.

        This is the Prerogative of Mercy in action - reducing the
        sentence per the Governor-General's decision.
        """
        if not petition.granted_reduction_days:
            raise ValueError(
                "granted_reduction_days must be set when granting clemency"
            )

        adjustment = SentenceAdjustment(
            sentence_id=petition.sentence_id,
            adjustment_type=AdjustmentType.CLEMENCY_REDUCTION.value,
            days=petition.granted_reduction_days,
            effective_date=petition.decision_date or date.today(),
            reason=f"Clemency granted via petition {petition.petition_number}. "
                   f"Type: {petition.petition_type}. "
                   f"{petition.decision_notes or ''}".strip(),
            document_reference=petition.petition_number,
            approved_by=approved_by
        )

        return await self.adjustment_repo.create(adjustment)

    # ========================================================================
    # Query Methods
    # ========================================================================

    async def get_by_inmate(self, inmate_id: UUID) -> List[ClemencyPetition]:
        """Get all petitions for an inmate."""
        return await self.petition_repo.get_by_inmate(inmate_id)

    async def get_by_sentence(self, sentence_id: UUID) -> List[ClemencyPetition]:
        """Get all petitions for a sentence."""
        return await self.petition_repo.get_by_sentence(sentence_id)

    async def get_by_status(self, status: PetitionStatus) -> List[ClemencyPetition]:
        """Get petitions by status."""
        return await self.petition_repo.get_by_status(status)

    async def get_by_type(self, petition_type: PetitionType) -> List[ClemencyPetition]:
        """Get petitions by type."""
        return await self.petition_repo.get_by_type(petition_type)

    async def get_pending_committee(self) -> List[ClemencyPetition]:
        """Get petitions awaiting committee review."""
        return await self.petition_repo.get_pending_committee()

    async def get_pending_minister(self) -> List[ClemencyPetition]:
        """Get petitions awaiting minister review."""
        return await self.petition_repo.get_pending_minister()

    async def get_pending_governor_general(self) -> List[ClemencyPetition]:
        """Get petitions awaiting Governor-General decision."""
        return await self.petition_repo.get_pending_governor_general()

    async def get_petition_history(
        self,
        petition_id: UUID
    ) -> List[ClemencyStatusHistory]:
        """Get status history for a petition."""
        return await self.history_repo.get_by_petition(petition_id)

    # ========================================================================
    # Summary and Statistics
    # ========================================================================

    async def get_inmate_summary(self, inmate_id: UUID) -> InmateClemencySummary:
        """Get clemency summary for an inmate."""
        petitions = await self.petition_repo.get_by_inmate(inmate_id)
        counts = await self.petition_repo.count_by_inmate_status(inmate_id)

        return InmateClemencySummary(
            inmate_id=inmate_id,
            total_petitions=counts["total"],
            pending_petitions=counts["pending"],
            granted_petitions=counts["granted"],
            denied_petitions=counts["denied"],
            petitions=[
                ClemencyPetitionResponse.model_validate(p) for p in petitions
            ]
        )

    async def get_statistics(self) -> ClemencyStatistics:
        """Get overall clemency statistics."""
        by_status = await self.petition_repo.count_by_status()
        by_type = await self.petition_repo.count_by_type()
        decisions = await self.petition_repo.count_decisions_last_year()

        pending_committee = await self.petition_repo.get_pending_committee()
        pending_minister = await self.petition_repo.get_pending_minister()
        pending_gg = await self.petition_repo.get_pending_governor_general()

        total = sum(by_status.values())

        return ClemencyStatistics(
            total_petitions=total,
            by_status=by_status,
            by_type=by_type,
            pending_committee=len(pending_committee),
            pending_minister=len(pending_minister),
            pending_governor_general=len(pending_gg),
            granted_last_year=decisions["granted"],
            denied_last_year=decisions["denied"],
            average_processing_days=None  # TODO: Calculate from history
        )
