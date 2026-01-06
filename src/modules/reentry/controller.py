"""
Reentry Planning Controller - API endpoints for reentry operations.

PLANS:
- POST   /api/v1/reentry/plans                      Create plan
- GET    /api/v1/reentry/plans                      List plans
- GET    /api/v1/reentry/plans/{id}                 Get plan
- PUT    /api/v1/reentry/plans/{id}                 Update plan
- PUT    /api/v1/reentry/plans/{id}/approve         Approve plan as READY
- DELETE /api/v1/reentry/plans/{id}                 Delete plan
- GET    /api/v1/inmates/{id}/reentry               Get inmate reentry summary

CHECKLIST:
- POST   /api/v1/reentry/plans/{id}/checklist       Add checklist item
- GET    /api/v1/reentry/plans/{id}/checklist       Get plan checklist
- PUT    /api/v1/reentry/checklist/{id}/complete    Complete item
- DELETE /api/v1/reentry/checklist/{id}             Delete item

REFERRALS:
- POST   /api/v1/reentry/referrals                  Create referral
- PUT    /api/v1/reentry/referrals/{id}/status      Update referral status
- GET    /api/v1/reentry/plans/{id}/referrals       Get plan referrals

REPORTS:
- GET    /api/v1/reentry/upcoming                   Upcoming releases
- GET    /api/v1/reentry/not-ready                  Plans not ready
- GET    /api/v1/reentry/statistics                 Statistics
"""
from datetime import date
from typing import Optional
from uuid import UUID

from quart import Blueprint, request, jsonify

from src.database.async_db import get_async_session
from src.common.enums import PlanStatus, HousingPlan, ChecklistType, ServiceType, ReferralStatus
from src.modules.reentry.service import ReentryService
from src.modules.reentry.dtos import (
    ReentryPlanCreate,
    ReentryPlanUpdate,
    ReentryPlanResponse,
    ReentryPlanListResponse,
    ReentryChecklistCreate,
    ReentryChecklistResponse,
    ReentryChecklistListResponse,
    ReentryReferralCreate,
    ReentryReferralStatusUpdate,
    ReentryReferralResponse,
    ReentryReferralListResponse,
)

# Create blueprint
reentry_bp = Blueprint('reentry', __name__, url_prefix='/api/v1')

# Alias for auto-discovery by app.py
blueprint = reentry_bp


# ============================================================================
# Plan Endpoints
# ============================================================================

@reentry_bp.route('/reentry/plans', methods=['POST'])
async def create_plan():
    """
    Create a new reentry plan.

    Auto-generates standard checklist items.

    Request body: ReentryPlanCreate
    Returns: ReentryPlanResponse (201)
    """
    try:
        data = await request.get_json()
        plan_data = ReentryPlanCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ReentryService(session)
            plan = await service.create_plan(plan_data, created_by)
            await session.commit()

            # Calculate readiness
            score = service.calculate_readiness_score(plan)
            checklist_counts = await service.checklist_repo.count_completion(plan.id)

            response = ReentryPlanResponse(
                id=plan.id,
                inmate_id=plan.inmate_id,
                expected_release_date=plan.expected_release_date,
                status=plan.status,
                housing_plan=plan.housing_plan,
                housing_address=plan.housing_address,
                employment_plan=plan.employment_plan,
                has_id_documents=plan.has_id_documents,
                has_birth_certificate=plan.has_birth_certificate,
                has_nib_card=plan.has_nib_card,
                transportation_arranged=plan.transportation_arranged,
                family_contact_name=plan.family_contact_name,
                family_contact_phone=plan.family_contact_phone,
                support_services=plan.support_services,
                risk_factors=plan.risk_factors,
                notes=plan.notes,
                created_by=plan.created_by,
                approved_by=plan.approved_by,
                approval_date=plan.approval_date,
                days_until_release=plan.days_until_release,
                is_overdue=plan.is_overdue,
                readiness_score=score,
                checklist_total=checklist_counts['total'],
                checklist_completed=checklist_counts['completed'],
                inserted_date=plan.inserted_date,
                updated_date=plan.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create plan: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans', methods=['GET'])
async def list_plans():
    """
    List reentry plans.

    Query params:
    - status: Filter by status (DRAFT, IN_PROGRESS, READY, COMPLETED)
    - include_completed: Include completed plans (default: false)

    Returns: ReentryPlanListResponse
    """
    try:
        status_filter = request.args.get('status')
        include_completed = request.args.get('include_completed', '').lower() == 'true'

        async with get_async_session() as session:
            service = ReentryService(session)

            if status_filter:
                plans = await service.plan_repo.get_by_status(status_filter.upper())
            elif include_completed:
                plans = await service.plan_repo.get_all_active()
                completed = await service.plan_repo.get_by_status(PlanStatus.COMPLETED.value)
                plans = plans + completed
            else:
                plans = await service.plan_repo.get_all_active()

            items = []
            for plan in plans:
                score = service.calculate_readiness_score(plan)
                checklist_counts = await service.checklist_repo.count_completion(plan.id)

                items.append(ReentryPlanResponse(
                    id=plan.id,
                    inmate_id=plan.inmate_id,
                    expected_release_date=plan.expected_release_date,
                    status=plan.status,
                    housing_plan=plan.housing_plan,
                    housing_address=plan.housing_address,
                    employment_plan=plan.employment_plan,
                    has_id_documents=plan.has_id_documents,
                    has_birth_certificate=plan.has_birth_certificate,
                    has_nib_card=plan.has_nib_card,
                    transportation_arranged=plan.transportation_arranged,
                    family_contact_name=plan.family_contact_name,
                    family_contact_phone=plan.family_contact_phone,
                    support_services=plan.support_services,
                    risk_factors=plan.risk_factors,
                    notes=plan.notes,
                    created_by=plan.created_by,
                    approved_by=plan.approved_by,
                    approval_date=plan.approval_date,
                    days_until_release=plan.days_until_release,
                    is_overdue=plan.is_overdue,
                    readiness_score=score,
                    checklist_total=checklist_counts['total'],
                    checklist_completed=checklist_counts['completed'],
                    inserted_date=plan.inserted_date,
                    updated_date=plan.updated_date
                ))

            response = ReentryPlanListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to list plans: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>', methods=['GET'])
async def get_plan(plan_id: UUID):
    """
    Get a specific reentry plan with checklist and referrals.

    Returns: ReentryPlanResponse
    """
    try:
        async with get_async_session() as session:
            service = ReentryService(session)
            plan = await service.get_plan(plan_id, include_referrals=True)

            if not plan:
                return jsonify({"error": "Plan not found"}), 404

            score = service.calculate_readiness_score(plan)
            checklist_counts = await service.checklist_repo.count_completion(plan.id)

            response = ReentryPlanResponse(
                id=plan.id,
                inmate_id=plan.inmate_id,
                expected_release_date=plan.expected_release_date,
                status=plan.status,
                housing_plan=plan.housing_plan,
                housing_address=plan.housing_address,
                employment_plan=plan.employment_plan,
                has_id_documents=plan.has_id_documents,
                has_birth_certificate=plan.has_birth_certificate,
                has_nib_card=plan.has_nib_card,
                transportation_arranged=plan.transportation_arranged,
                family_contact_name=plan.family_contact_name,
                family_contact_phone=plan.family_contact_phone,
                support_services=plan.support_services,
                risk_factors=plan.risk_factors,
                notes=plan.notes,
                created_by=plan.created_by,
                approved_by=plan.approved_by,
                approval_date=plan.approval_date,
                days_until_release=plan.days_until_release,
                is_overdue=plan.is_overdue,
                readiness_score=score,
                checklist_total=checklist_counts['total'],
                checklist_completed=checklist_counts['completed'],
                inserted_date=plan.inserted_date,
                updated_date=plan.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get plan: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>', methods=['PUT'])
async def update_plan(plan_id: UUID):
    """
    Update reentry plan details.

    Request body: ReentryPlanUpdate
    Returns: ReentryPlanResponse
    """
    try:
        data = await request.get_json()
        update_data = ReentryPlanUpdate(**data)

        async with get_async_session() as session:
            service = ReentryService(session)
            plan = await service.update_plan(plan_id, update_data)
            await session.commit()

            if not plan:
                return jsonify({"error": "Plan not found"}), 404

            score = service.calculate_readiness_score(plan)
            checklist_counts = await service.checklist_repo.count_completion(plan.id)

            response = ReentryPlanResponse(
                id=plan.id,
                inmate_id=plan.inmate_id,
                expected_release_date=plan.expected_release_date,
                status=plan.status,
                housing_plan=plan.housing_plan,
                housing_address=plan.housing_address,
                employment_plan=plan.employment_plan,
                has_id_documents=plan.has_id_documents,
                has_birth_certificate=plan.has_birth_certificate,
                has_nib_card=plan.has_nib_card,
                transportation_arranged=plan.transportation_arranged,
                family_contact_name=plan.family_contact_name,
                family_contact_phone=plan.family_contact_phone,
                support_services=plan.support_services,
                risk_factors=plan.risk_factors,
                notes=plan.notes,
                created_by=plan.created_by,
                approved_by=plan.approved_by,
                approval_date=plan.approval_date,
                days_until_release=plan.days_until_release,
                is_overdue=plan.is_overdue,
                readiness_score=score,
                checklist_total=checklist_counts['total'],
                checklist_completed=checklist_counts['completed'],
                inserted_date=plan.inserted_date,
                updated_date=plan.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update plan: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>/approve', methods=['PUT'])
async def approve_plan(plan_id: UUID):
    """
    Approve a plan as READY for release.

    Validates all checklist items are complete.

    Returns: ReentryPlanResponse
    """
    try:
        # Get user ID from auth context (placeholder)
        approved_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ReentryService(session)
            plan = await service.approve_plan(plan_id, approved_by)
            await session.commit()

            score = service.calculate_readiness_score(plan)
            checklist_counts = await service.checklist_repo.count_completion(plan.id)

            response = ReentryPlanResponse(
                id=plan.id,
                inmate_id=plan.inmate_id,
                expected_release_date=plan.expected_release_date,
                status=plan.status,
                housing_plan=plan.housing_plan,
                housing_address=plan.housing_address,
                employment_plan=plan.employment_plan,
                has_id_documents=plan.has_id_documents,
                has_birth_certificate=plan.has_birth_certificate,
                has_nib_card=plan.has_nib_card,
                transportation_arranged=plan.transportation_arranged,
                family_contact_name=plan.family_contact_name,
                family_contact_phone=plan.family_contact_phone,
                support_services=plan.support_services,
                risk_factors=plan.risk_factors,
                notes=plan.notes,
                created_by=plan.created_by,
                approved_by=plan.approved_by,
                approval_date=plan.approval_date,
                days_until_release=plan.days_until_release,
                is_overdue=plan.is_overdue,
                readiness_score=score,
                checklist_total=checklist_counts['total'],
                checklist_completed=checklist_counts['completed'],
                inserted_date=plan.inserted_date,
                updated_date=plan.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to approve plan: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>', methods=['DELETE'])
async def delete_plan(plan_id: UUID):
    """Soft delete a reentry plan."""
    try:
        async with get_async_session() as session:
            service = ReentryService(session)
            success = await service.delete_plan(plan_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Plan not found"}), 404

            return jsonify({"message": "Plan deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete plan: {str(e)}"}), 500


@reentry_bp.route('/inmates/<uuid:inmate_id>/reentry', methods=['GET'])
async def get_inmate_reentry(inmate_id: UUID):
    """
    Get reentry summary for an inmate.

    Returns: ReentryPlanSummary
    """
    try:
        async with get_async_session() as session:
            service = ReentryService(session)
            summary = await service.get_inmate_reentry_summary(inmate_id)
            return jsonify(summary.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get reentry summary: {str(e)}"}), 500


# ============================================================================
# Checklist Endpoints
# ============================================================================

@reentry_bp.route('/reentry/plans/<uuid:plan_id>/checklist', methods=['POST'])
async def add_checklist_item(plan_id: UUID):
    """
    Add a custom checklist item to a plan.

    Request body: ReentryChecklistCreate
    Returns: ReentryChecklistResponse (201)
    """
    try:
        data = await request.get_json()
        item_data = ReentryChecklistCreate(**data)

        async with get_async_session() as session:
            service = ReentryService(session)
            item = await service.add_checklist_item(plan_id, item_data)
            await session.commit()

            response = ReentryChecklistResponse(
                id=item.id,
                reentry_plan_id=item.reentry_plan_id,
                item_type=item.item_type,
                description=item.description,
                is_completed=item.is_completed,
                completed_date=item.completed_date,
                completed_by=item.completed_by,
                due_date=item.due_date,
                is_overdue=item.is_overdue,
                notes=item.notes,
                inserted_date=item.inserted_date,
                updated_date=item.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to add checklist item: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>/checklist', methods=['GET'])
async def get_plan_checklist(plan_id: UUID):
    """
    Get checklist items for a plan.

    Query params:
    - completed: Filter completed only (true/false)
    - incomplete: Filter incomplete only (true/false)

    Returns: ReentryChecklistListResponse
    """
    try:
        completed_only = request.args.get('completed', '').lower() == 'true'
        incomplete_only = request.args.get('incomplete', '').lower() == 'true'

        async with get_async_session() as session:
            service = ReentryService(session)
            items = await service.get_plan_checklist(
                plan_id, completed_only, incomplete_only
            )

            checklist_items = [
                ReentryChecklistResponse(
                    id=item.id,
                    reentry_plan_id=item.reentry_plan_id,
                    item_type=item.item_type,
                    description=item.description,
                    is_completed=item.is_completed,
                    completed_date=item.completed_date,
                    completed_by=item.completed_by,
                    due_date=item.due_date,
                    is_overdue=item.is_overdue,
                    notes=item.notes,
                    inserted_date=item.inserted_date,
                    updated_date=item.updated_date
                )
                for item in items
            ]

            completed = sum(1 for i in items if i.is_completed)
            incomplete = len(items) - completed

            response = ReentryChecklistListResponse(
                items=checklist_items,
                total=len(items),
                completed=completed,
                incomplete=incomplete
            )
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get checklist: {str(e)}"}), 500


@reentry_bp.route('/reentry/checklist/<uuid:item_id>/complete', methods=['PUT'])
async def complete_checklist_item(item_id: UUID):
    """
    Mark a checklist item as complete.

    Request body (optional): {"notes": "..."}
    Returns: ReentryChecklistResponse
    """
    try:
        data = await request.get_json() or {}
        notes = data.get('notes')

        # Get user ID from auth context (placeholder)
        completed_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ReentryService(session)
            item = await service.complete_checklist_item(item_id, completed_by, notes)
            await session.commit()

            response = ReentryChecklistResponse(
                id=item.id,
                reentry_plan_id=item.reentry_plan_id,
                item_type=item.item_type,
                description=item.description,
                is_completed=item.is_completed,
                completed_date=item.completed_date,
                completed_by=item.completed_by,
                due_date=item.due_date,
                is_overdue=item.is_overdue,
                notes=item.notes,
                inserted_date=item.inserted_date,
                updated_date=item.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to complete item: {str(e)}"}), 500


@reentry_bp.route('/reentry/checklist/<uuid:item_id>', methods=['DELETE'])
async def delete_checklist_item(item_id: UUID):
    """Delete a checklist item."""
    try:
        async with get_async_session() as session:
            service = ReentryService(session)
            success = await service.delete_checklist_item(item_id)
            await session.commit()

            if not success:
                return jsonify({"error": "Checklist item not found"}), 404

            return jsonify({"message": "Checklist item deleted successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500


# ============================================================================
# Referral Endpoints
# ============================================================================

@reentry_bp.route('/reentry/referrals', methods=['POST'])
async def create_referral():
    """
    Create a service referral.

    Request body: ReentryReferralCreate
    Returns: ReentryReferralResponse (201)
    """
    try:
        data = await request.get_json()
        referral_data = ReentryReferralCreate(**data)

        # Get user ID from auth context (placeholder)
        created_by = None  # TODO: Get from auth context

        async with get_async_session() as session:
            service = ReentryService(session)
            referral = await service.create_referral(referral_data, created_by)
            await session.commit()

            response = ReentryReferralResponse(
                id=referral.id,
                reentry_plan_id=referral.reentry_plan_id,
                inmate_id=referral.inmate_id,
                service_type=referral.service_type,
                provider_name=referral.provider_name,
                provider_contact=referral.provider_contact,
                referral_date=referral.referral_date,
                status=referral.status,
                appointment_date=referral.appointment_date,
                outcome=referral.outcome,
                notes=referral.notes,
                created_by=referral.created_by,
                inserted_date=referral.inserted_date,
                updated_date=referral.updated_date
            )
            return jsonify(response.model_dump(mode='json')), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create referral: {str(e)}"}), 500


@reentry_bp.route('/reentry/referrals/<uuid:referral_id>/status', methods=['PUT'])
async def update_referral_status(referral_id: UUID):
    """
    Update referral status.

    Request body: ReentryReferralStatusUpdate
    Returns: ReentryReferralResponse
    """
    try:
        data = await request.get_json()
        status_data = ReentryReferralStatusUpdate(**data)

        async with get_async_session() as session:
            service = ReentryService(session)
            referral = await service.update_referral_status(referral_id, status_data)
            await session.commit()

            response = ReentryReferralResponse(
                id=referral.id,
                reentry_plan_id=referral.reentry_plan_id,
                inmate_id=referral.inmate_id,
                service_type=referral.service_type,
                provider_name=referral.provider_name,
                provider_contact=referral.provider_contact,
                referral_date=referral.referral_date,
                status=referral.status,
                appointment_date=referral.appointment_date,
                outcome=referral.outcome,
                notes=referral.notes,
                created_by=referral.created_by,
                inserted_date=referral.inserted_date,
                updated_date=referral.updated_date
            )
            return jsonify(response.model_dump(mode='json'))

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update referral status: {str(e)}"}), 500


@reentry_bp.route('/reentry/plans/<uuid:plan_id>/referrals', methods=['GET'])
async def get_plan_referrals(plan_id: UUID):
    """
    Get referrals for a plan.

    Query params:
    - active: Filter active only (true/false)

    Returns: ReentryReferralListResponse
    """
    try:
        active_only = request.args.get('active', '').lower() == 'true'

        async with get_async_session() as session:
            service = ReentryService(session)
            referrals = await service.get_plan_referrals(plan_id, active_only)

            items = [
                ReentryReferralResponse(
                    id=r.id,
                    reentry_plan_id=r.reentry_plan_id,
                    inmate_id=r.inmate_id,
                    service_type=r.service_type,
                    provider_name=r.provider_name,
                    provider_contact=r.provider_contact,
                    referral_date=r.referral_date,
                    status=r.status,
                    appointment_date=r.appointment_date,
                    outcome=r.outcome,
                    notes=r.notes,
                    created_by=r.created_by,
                    inserted_date=r.inserted_date,
                    updated_date=r.updated_date
                )
                for r in referrals
            ]

            response = ReentryReferralListResponse(items=items, total=len(items))
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get referrals: {str(e)}"}), 500


# ============================================================================
# Report Endpoints
# ============================================================================

@reentry_bp.route('/reentry/upcoming', methods=['GET'])
async def get_upcoming_releases():
    """
    Get plans with releases in the next N days.

    Query params:
    - days: Number of days ahead (default: 90)

    Returns: UpcomingReleasesResponse
    """
    try:
        days = request.args.get('days', 90, type=int)

        async with get_async_session() as session:
            service = ReentryService(session)
            response = await service.get_plans_for_upcoming_releases(days)
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get upcoming releases: {str(e)}"}), 500


@reentry_bp.route('/reentry/not-ready', methods=['GET'])
async def get_not_ready_plans():
    """
    Get plans that are not ready and releasing within threshold days.

    Query params:
    - days: Days threshold (default: 30)

    Returns: NotReadyPlansResponse
    """
    try:
        days = request.args.get('days', 30, type=int)

        async with get_async_session() as session:
            service = ReentryService(session)
            response = await service.get_not_ready_plans(days)
            return jsonify(response.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get not-ready plans: {str(e)}"}), 500


@reentry_bp.route('/reentry/statistics', methods=['GET'])
async def get_statistics():
    """
    Get overall reentry planning statistics.

    Returns: ReentryStatistics
    """
    try:
        async with get_async_session() as session:
            service = ReentryService(session)
            stats = await service.get_statistics()
            return jsonify(stats.model_dump(mode='json'))

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500
