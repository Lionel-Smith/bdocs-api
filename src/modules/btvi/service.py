"""
BTVI Certification Service - Business logic for vocational certifications.

Implements key operations:
- Certification issuance with auto-generated numbers
- Link to programme enrollments when applicable
- External verification workflow
- Trade-based queries and statistics

BTVI (Bahamas Technical and Vocational Institute) certifications
provide industry-recognized credentials for rehabilitation.
"""
from datetime import date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.enums import BTVICertType, SkillLevel, EnrollmentStatus
from src.modules.btvi.models import BTVICertification
from src.modules.btvi.repository import BTVICertificationRepository
from src.modules.btvi.dtos import (
    BTVICertificationCreate,
    BTVICertificationUpdate,
    BTVICertificationVerify,
    BTVICertificationResponse,
    InmateBTVISummary,
    BTVITradeStatistics,
    BTVIStatistics,
)
from src.modules.programme.repository import ProgrammeEnrollmentRepository


class BTVIService:
    """Service for BTVI certification operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cert_repo = BTVICertificationRepository(session)
        self.enrollment_repo = ProgrammeEnrollmentRepository(session)

    # ========================================================================
    # Certification CRUD
    # ========================================================================

    async def issue_certification(
        self,
        data: BTVICertificationCreate,
        created_by: Optional[UUID] = None
    ) -> BTVICertification:
        """
        Issue a new BTVI certification.

        Auto-generates certification number (BTVI-YYYY-NNNNN).
        Validates programme enrollment if linked.
        """
        # Validate programme enrollment if provided
        if data.programme_enrollment_id:
            enrollment = await self.enrollment_repo.get_by_id(data.programme_enrollment_id)
            if not enrollment:
                raise ValueError(
                    f"Programme enrollment not found: {data.programme_enrollment_id}"
                )
            # Verify enrollment is completed
            if enrollment.status != EnrollmentStatus.COMPLETED.value:
                raise ValueError(
                    f"Cannot link certification to non-completed enrollment "
                    f"(status: {enrollment.status})"
                )
            # Verify inmate matches
            if enrollment.inmate_id != data.inmate_id:
                raise ValueError(
                    "Inmate ID does not match programme enrollment"
                )
            # Check if enrollment already has a certification
            existing_cert = await self.cert_repo.get_by_enrollment(data.programme_enrollment_id)
            if existing_cert:
                raise ValueError(
                    f"Programme enrollment already has certification: "
                    f"{existing_cert.certification_number}"
                )

        # Generate certification number
        certification_number = await self.cert_repo.get_next_certification_number()

        # Create certification
        certification = BTVICertification(
            inmate_id=data.inmate_id,
            programme_enrollment_id=data.programme_enrollment_id,
            certification_number=certification_number,
            certification_type=data.certification_type.value,
            issued_date=data.issued_date,
            expiry_date=data.expiry_date,
            issuing_authority=data.issuing_authority,
            skill_level=data.skill_level.value,
            hours_training=data.hours_training,
            assessment_score=data.assessment_score,
            instructor_name=data.instructor_name,
            verification_url=data.verification_url,
            is_verified=False,  # Starts unverified
            notes=data.notes,
            created_by=created_by
        )

        return await self.cert_repo.create(certification)

    async def get_certification(
        self,
        certification_id: UUID
    ) -> Optional[BTVICertification]:
        """Get certification by ID."""
        return await self.cert_repo.get_by_id(certification_id)

    async def get_certification_by_number(
        self,
        certification_number: str
    ) -> Optional[BTVICertification]:
        """Get certification by certification number."""
        return await self.cert_repo.get_by_certification_number(certification_number)

    async def get_all_certifications(
        self,
        certification_type: Optional[BTVICertType] = None,
        skill_level: Optional[SkillLevel] = None
    ) -> List[BTVICertification]:
        """Get certifications with optional filters."""
        if certification_type:
            return await self.cert_repo.get_by_trade(certification_type)
        elif skill_level:
            return await self.cert_repo.get_by_skill_level(skill_level)
        else:
            return await self.cert_repo.get_all()

    async def update_certification(
        self,
        certification_id: UUID,
        data: BTVICertificationUpdate
    ) -> Optional[BTVICertification]:
        """Update certification fields."""
        certification = await self.cert_repo.get_by_id(certification_id)
        if not certification:
            return None

        # Validate programme enrollment if being updated
        if data.programme_enrollment_id:
            enrollment = await self.enrollment_repo.get_by_id(data.programme_enrollment_id)
            if not enrollment:
                raise ValueError(
                    f"Programme enrollment not found: {data.programme_enrollment_id}"
                )
            if enrollment.status != EnrollmentStatus.COMPLETED.value:
                raise ValueError(
                    f"Cannot link certification to non-completed enrollment"
                )

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(certification, field):
                if field == 'skill_level' and value:
                    setattr(certification, field, value.value)
                else:
                    setattr(certification, field, value)

        return await self.cert_repo.update(certification)

    async def delete_certification(self, certification_id: UUID) -> bool:
        """Soft delete a certification."""
        return await self.cert_repo.delete(certification_id)

    # ========================================================================
    # Verification
    # ========================================================================

    async def verify_certification(
        self,
        certification_id: UUID,
        data: BTVICertificationVerify
    ) -> BTVICertification:
        """
        Verify a BTVI certification.

        This marks the certification as externally verified,
        optionally updating the verification URL and notes.
        """
        certification = await self.cert_repo.get_by_id(certification_id)
        if not certification:
            raise ValueError(f"Certification not found: {certification_id}")

        certification.is_verified = data.is_verified
        if data.verification_url:
            certification.verification_url = data.verification_url
        if data.notes:
            # Append to existing notes
            if certification.notes:
                certification.notes = f"{certification.notes}\n\nVerification: {data.notes}"
            else:
                certification.notes = f"Verification: {data.notes}"

        return await self.cert_repo.update(certification)

    # ========================================================================
    # Query Methods
    # ========================================================================

    async def get_certifications_by_inmate(
        self,
        inmate_id: UUID
    ) -> List[BTVICertification]:
        """Get all certifications for an inmate."""
        return await self.cert_repo.get_by_inmate(inmate_id)

    async def get_certifications_by_trade(
        self,
        certification_type: BTVICertType
    ) -> List[BTVICertification]:
        """Get certifications by trade type."""
        return await self.cert_repo.get_by_trade(certification_type)

    async def get_verified_certifications(self) -> List[BTVICertification]:
        """Get all verified certifications."""
        return await self.cert_repo.get_verified()

    async def get_expired_certifications(self) -> List[BTVICertification]:
        """Get all expired certifications."""
        return await self.cert_repo.get_expired()

    # ========================================================================
    # Summary and Statistics
    # ========================================================================

    async def get_inmate_summary(self, inmate_id: UUID) -> InmateBTVISummary:
        """Get BTVI certification summary for an inmate."""
        certifications = await self.cert_repo.get_by_inmate(inmate_id)
        counts = await self.cert_repo.count_by_inmate_status(inmate_id)

        return InmateBTVISummary(
            inmate_id=inmate_id,
            total_certifications=counts["total"],
            valid_certifications=counts["valid"],
            expired_certifications=counts["expired"],
            verified_certifications=counts["verified"],
            by_trade=counts["by_trade"],
            by_skill_level=counts["by_skill_level"],
            total_training_hours=counts["total_training_hours"],
            certifications=[
                BTVICertificationResponse(
                    id=c.id,
                    inmate_id=c.inmate_id,
                    programme_enrollment_id=c.programme_enrollment_id,
                    certification_number=c.certification_number,
                    certification_type=BTVICertType(c.certification_type),
                    issued_date=c.issued_date,
                    expiry_date=c.expiry_date,
                    issuing_authority=c.issuing_authority,
                    skill_level=SkillLevel(c.skill_level),
                    hours_training=c.hours_training,
                    assessment_score=c.assessment_score,
                    instructor_name=c.instructor_name,
                    verification_url=c.verification_url,
                    is_verified=c.is_verified,
                    is_expired=c.is_expired,
                    is_valid=c.is_valid,
                    notes=c.notes,
                    created_by=c.created_by,
                    inserted_date=c.inserted_date,
                    updated_date=c.updated_date
                )
                for c in certifications
            ]
        )

    async def get_trade_statistics(
        self,
        certification_type: BTVICertType
    ) -> BTVITradeStatistics:
        """Get statistics for a specific trade."""
        stats = await self.cert_repo.get_trade_statistics(certification_type)

        return BTVITradeStatistics(
            certification_type=certification_type,
            total_certifications=stats["total"],
            by_skill_level=stats["by_skill_level"],
            average_training_hours=stats["average_training_hours"],
            average_assessment_score=stats["average_assessment_score"],
            verified_count=stats["verified_count"],
            expired_count=stats["expired_count"]
        )

    async def get_statistics(self) -> BTVIStatistics:
        """Get overall BTVI certification statistics."""
        today = date.today()

        # Count all certifications
        all_certs = await self.cert_repo.get_all()
        total = len(all_certs)

        # Count valid and expired
        valid = sum(1 for c in all_certs if c.is_valid)
        expired = sum(1 for c in all_certs if c.is_expired)
        verified = sum(1 for c in all_certs if c.is_verified)

        # Get breakdowns
        by_trade = await self.cert_repo.count_by_trade()
        by_level = await self.cert_repo.count_by_skill_level()
        issued_this_year = await self.cert_repo.count_issued_this_year()
        avg_hours = await self.cert_repo.get_average_training_hours()
        avg_score = await self.cert_repo.get_average_assessment_score()
        most_popular = await self.cert_repo.get_most_popular_trades()

        return BTVIStatistics(
            total_certifications=total,
            valid_certifications=valid,
            expired_certifications=expired,
            verified_certifications=verified,
            by_trade=by_trade,
            by_skill_level=by_level,
            issued_this_year=issued_this_year,
            average_training_hours=avg_hours,
            average_assessment_score=avg_score,
            most_popular_trades=most_popular
        )
