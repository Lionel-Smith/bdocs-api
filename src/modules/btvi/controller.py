"""
BTVI Certification Controller - API endpoints for vocational certifications.

Endpoints:
- POST   /api/v1/btvi/certifications                Issue certification
- GET    /api/v1/btvi/certifications                List certifications (with filters)
- GET    /api/v1/btvi/certifications/statistics     Get statistics
- GET    /api/v1/btvi/certifications/{id}           Get certification by ID
- PUT    /api/v1/btvi/certifications/{id}           Update certification
- DELETE /api/v1/btvi/certifications/{id}           Delete certification
- GET    /api/v1/btvi/certifications/number/{num}   Get by certification number
- PUT    /api/v1/btvi/certifications/{id}/verify    Verify certification
- GET    /api/v1/btvi/certifications/by-trade/{type} Get by trade type
- GET    /api/v1/inmates/{id}/btvi                  Inmate BTVI summary
"""
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import BTVICertType, SkillLevel
from src.modules.btvi.service import BTVIService
from src.modules.btvi.dtos import (
    BTVICertificationCreate,
    BTVICertificationUpdate,
    BTVICertificationVerify,
    BTVICertificationResponse,
    BTVICertificationListResponse,
)

# Create blueprint
btvi_bp = Blueprint('btvi', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = btvi_bp


# ============================================================================
# Certification CRUD Endpoints
# ============================================================================

@btvi_bp.route('/btvi/certifications', methods=['POST'])
async def issue_certification():
    """
    Issue a new BTVI certification.

    Can optionally link to a completed programme enrollment.

    Request body: BTVICertificationCreate
    Returns: BTVICertificationResponse
    """
    try:
        data = await request.get_json()
        cert_data = BTVICertificationCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = BTVIService(session)
            certification = await service.issue_certification(cert_data, created_by)
            await session.commit()

            response = BTVICertificationResponse(
                id=certification.id,
                inmate_id=certification.inmate_id,
                programme_enrollment_id=certification.programme_enrollment_id,
                certification_number=certification.certification_number,
                certification_type=BTVICertType(certification.certification_type),
                issued_date=certification.issued_date,
                expiry_date=certification.expiry_date,
                issuing_authority=certification.issuing_authority,
                skill_level=SkillLevel(certification.skill_level),
                hours_training=certification.hours_training,
                assessment_score=certification.assessment_score,
                instructor_name=certification.instructor_name,
                verification_url=certification.verification_url,
                is_verified=certification.is_verified,
                is_expired=certification.is_expired,
                is_valid=certification.is_valid,
                notes=certification.notes,
                created_by=certification.created_by,
                inserted_date=certification.inserted_date,
                updated_date=certification.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to issue certification: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications', methods=['GET'])
async def list_certifications():
    """
    List BTVI certifications with optional filters.

    Query params:
    - type: Filter by BTVICertType
    - level: Filter by SkillLevel

    Returns: BTVICertificationListResponse
    """
    try:
        type_filter = request.args.get('type')
        level_filter = request.args.get('level')

        cert_type = BTVICertType(type_filter) if type_filter else None
        skill_level = SkillLevel(level_filter) if level_filter else None

        async with get_async_session() as session:
            service = BTVIService(session)
            certifications = await service.get_all_certifications(
                certification_type=cert_type,
                skill_level=skill_level
            )

            items = [
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

            response = BTVICertificationListResponse(
                items=items,
                total=len(items)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to list certifications: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications/<uuid:certification_id>', methods=['GET'])
async def get_certification(certification_id: UUID):
    """
    Get a BTVI certification by ID.

    Returns: BTVICertificationResponse
    """
    try:
        async with get_async_session() as session:
            service = BTVIService(session)
            certification = await service.get_certification(certification_id)

            if not certification:
                return jsonify({"error": "Certification not found"}), 404

            response = BTVICertificationResponse(
                id=certification.id,
                inmate_id=certification.inmate_id,
                programme_enrollment_id=certification.programme_enrollment_id,
                certification_number=certification.certification_number,
                certification_type=BTVICertType(certification.certification_type),
                issued_date=certification.issued_date,
                expiry_date=certification.expiry_date,
                issuing_authority=certification.issuing_authority,
                skill_level=SkillLevel(certification.skill_level),
                hours_training=certification.hours_training,
                assessment_score=certification.assessment_score,
                instructor_name=certification.instructor_name,
                verification_url=certification.verification_url,
                is_verified=certification.is_verified,
                is_expired=certification.is_expired,
                is_valid=certification.is_valid,
                notes=certification.notes,
                created_by=certification.created_by,
                inserted_date=certification.inserted_date,
                updated_date=certification.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get certification: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications/<uuid:certification_id>', methods=['PUT'])
async def update_certification(certification_id: UUID):
    """
    Update a BTVI certification.

    Request body: BTVICertificationUpdate
    Returns: BTVICertificationResponse
    """
    try:
        data = await request.get_json()
        update_data = BTVICertificationUpdate(**data)

        async with get_async_session() as session:
            service = BTVIService(session)
            certification = await service.update_certification(
                certification_id, update_data
            )
            await session.commit()

            if not certification:
                return jsonify({"error": "Certification not found"}), 404

            response = BTVICertificationResponse(
                id=certification.id,
                inmate_id=certification.inmate_id,
                programme_enrollment_id=certification.programme_enrollment_id,
                certification_number=certification.certification_number,
                certification_type=BTVICertType(certification.certification_type),
                issued_date=certification.issued_date,
                expiry_date=certification.expiry_date,
                issuing_authority=certification.issuing_authority,
                skill_level=SkillLevel(certification.skill_level),
                hours_training=certification.hours_training,
                assessment_score=certification.assessment_score,
                instructor_name=certification.instructor_name,
                verification_url=certification.verification_url,
                is_verified=certification.is_verified,
                is_expired=certification.is_expired,
                is_valid=certification.is_valid,
                notes=certification.notes,
                created_by=certification.created_by,
                inserted_date=certification.inserted_date,
                updated_date=certification.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update certification: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications/<uuid:certification_id>', methods=['DELETE'])
async def delete_certification(certification_id: UUID):
    """Soft delete a BTVI certification."""
    try:
        async with get_async_session() as session:
            service = BTVIService(session)
            success = await service.delete_certification(certification_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Certification not found"}), 404

            return jsonify({"message": "Certification deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete certification: {str(e)}"}), 500


# ============================================================================
# Lookup Endpoints
# ============================================================================

@btvi_bp.route('/btvi/certifications/number/<cert_number>', methods=['GET'])
async def get_certification_by_number(cert_number: str):
    """
    Get a BTVI certification by certification number.

    Returns: BTVICertificationResponse
    """
    try:
        async with get_async_session() as session:
            service = BTVIService(session)
            certification = await service.get_certification_by_number(cert_number)

            if not certification:
                return jsonify({"error": "Certification not found"}), 404

            response = BTVICertificationResponse(
                id=certification.id,
                inmate_id=certification.inmate_id,
                programme_enrollment_id=certification.programme_enrollment_id,
                certification_number=certification.certification_number,
                certification_type=BTVICertType(certification.certification_type),
                issued_date=certification.issued_date,
                expiry_date=certification.expiry_date,
                issuing_authority=certification.issuing_authority,
                skill_level=SkillLevel(certification.skill_level),
                hours_training=certification.hours_training,
                assessment_score=certification.assessment_score,
                instructor_name=certification.instructor_name,
                verification_url=certification.verification_url,
                is_verified=certification.is_verified,
                is_expired=certification.is_expired,
                is_valid=certification.is_valid,
                notes=certification.notes,
                created_by=certification.created_by,
                inserted_date=certification.inserted_date,
                updated_date=certification.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get certification: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications/by-trade/<trade_type>', methods=['GET'])
async def get_certifications_by_trade(trade_type: str):
    """
    Get BTVI certifications by trade type.

    Path params:
    - trade_type: BTVICertType value (AUTOMOTIVE, ELECTRICAL, etc.)

    Returns: BTVICertificationListResponse
    """
    try:
        cert_type = BTVICertType(trade_type.upper())

        async with get_async_session() as session:
            service = BTVIService(session)
            certifications = await service.get_certifications_by_trade(cert_type)

            items = [
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

            response = BTVICertificationListResponse(
                items=items,
                total=len(items)
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": f"Invalid trade type: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get certifications: {str(e)}"}), 500


# ============================================================================
# Verification Endpoint
# ============================================================================

@btvi_bp.route('/btvi/certifications/<uuid:certification_id>/verify', methods=['PUT'])
async def verify_certification(certification_id: UUID):
    """
    Verify a BTVI certification.

    Request body: BTVICertificationVerify
    Returns: BTVICertificationResponse
    """
    try:
        data = await request.get_json()
        verify_data = BTVICertificationVerify(**data)

        async with get_async_session() as session:
            service = BTVIService(session)
            certification = await service.verify_certification(
                certification_id, verify_data
            )
            await session.commit()

            response = BTVICertificationResponse(
                id=certification.id,
                inmate_id=certification.inmate_id,
                programme_enrollment_id=certification.programme_enrollment_id,
                certification_number=certification.certification_number,
                certification_type=BTVICertType(certification.certification_type),
                issued_date=certification.issued_date,
                expiry_date=certification.expiry_date,
                issuing_authority=certification.issuing_authority,
                skill_level=SkillLevel(certification.skill_level),
                hours_training=certification.hours_training,
                assessment_score=certification.assessment_score,
                instructor_name=certification.instructor_name,
                verification_url=certification.verification_url,
                is_verified=certification.is_verified,
                is_expired=certification.is_expired,
                is_valid=certification.is_valid,
                notes=certification.notes,
                created_by=certification.created_by,
                inserted_date=certification.inserted_date,
                updated_date=certification.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to verify certification: {str(e)}"}), 500


# ============================================================================
# Inmate BTVI Endpoint
# ============================================================================

@btvi_bp.route('/inmates/<uuid:inmate_id>/btvi', methods=['GET'])
async def get_inmate_btvi(inmate_id: UUID):
    """
    Get BTVI certification summary for an inmate.

    Returns: InmateBTVISummary
    """
    try:
        async with get_async_session() as session:
            service = BTVIService(session)
            summary = await service.get_inmate_summary(inmate_id)

            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get inmate BTVI: {str(e)}"}), 500


# ============================================================================
# Statistics Endpoints
# ============================================================================

@btvi_bp.route('/btvi/certifications/statistics', methods=['GET'])
async def get_statistics():
    """
    Get overall BTVI certification statistics.

    Returns: BTVIStatistics
    """
    try:
        async with get_async_session() as session:
            service = BTVIService(session)
            stats = await service.get_statistics()

            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


@btvi_bp.route('/btvi/certifications/statistics/<trade_type>', methods=['GET'])
async def get_trade_statistics(trade_type: str):
    """
    Get statistics for a specific trade type.

    Path params:
    - trade_type: BTVICertType value (AUTOMOTIVE, ELECTRICAL, etc.)

    Returns: BTVITradeStatistics
    """
    try:
        cert_type = BTVICertType(trade_type.upper())

        async with get_async_session() as session:
            service = BTVIService(session)
            stats = await service.get_trade_statistics(cert_type)

            return jsonify(stats.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": f"Invalid trade type: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get trade statistics: {str(e)}"}), 500
