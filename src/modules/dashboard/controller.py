"""
Dashboard Controller - API endpoints for admin dashboard.

All endpoints use Redis caching with 5-minute TTL.
Responses include generated_at timestamp for cache freshness.

Endpoints:
- GET /api/v1/dashboard/summary          Overall stats
- GET /api/v1/dashboard/population       Capacity & remand metrics
- GET /api/v1/dashboard/movements/today  Today's movements
- GET /api/v1/dashboard/court/upcoming   Upcoming court appearances
- GET /api/v1/dashboard/releases/upcoming Upcoming releases
- GET /api/v1/dashboard/clemency/pending  Pending clemency petitions
- GET /api/v1/dashboard/alerts           System alerts
"""
from quart import Blueprint, jsonify

from src.database.async_db import get_async_session
from src.modules.dashboard.service import DashboardService
from src.cache.redis_client import redis_client

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')

# Alias for auto-discovery by app.py
blueprint = dashboard_bp


# ============================================================================
# Cache Helper
# ============================================================================

async def get_cached_or_compute(cache_key: str, compute_func):
    """
    Get data from cache or compute and cache it.

    Args:
        cache_key: Redis cache key
        compute_func: Async function to compute data if not cached

    Returns:
        Computed or cached data as dict
    """
    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached is not None:
        return cached

    # Compute and cache
    result = await compute_func()
    result_dict = result.model_dump(mode='json')

    await redis_client.set(cache_key, result_dict, ttl=CACHE_TTL)
    return result_dict


# ============================================================================
# Summary Endpoint
# ============================================================================

@dashboard_bp.route('/summary', methods=['GET'])
async def get_summary():
    """
    Get overall dashboard summary.

    Returns:
    - total_inmates: Total inmates across all statuses
    - by_status: Breakdown by custody status (REMAND, SENTENCED, etc.)
    - by_security_level: Breakdown by security classification
    - by_gender: Breakdown by gender
    - capacity_utilization: Percentage of facility capacity used
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:summary",
                compute_func=service.get_summary
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get summary: {str(e)}"}), 500


# ============================================================================
# Population Endpoint
# ============================================================================

@dashboard_bp.route('/population', methods=['GET'])
async def get_population():
    """
    Get population metrics including capacity and remand ratio.

    The Bahamas targets <40% remand population per international standards.

    Returns:
    - current_population: Total inmates currently housed
    - total_capacity: Total bed capacity
    - available_beds: Remaining capacity
    - utilization_percent: Current utilization percentage
    - overcrowded_units: List of units over capacity
    - remand_count: Number of inmates on remand
    - remand_percentage: Remand as percentage of population
    - remand_target_met: Whether <40% target is met
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:population",
                compute_func=service.get_population
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get population: {str(e)}"}), 500


# ============================================================================
# Movements Today Endpoint
# ============================================================================

@dashboard_bp.route('/movements/today', methods=['GET'])
async def get_movements_today():
    """
    Get today's movement summary.

    Returns:
    - date: Current date
    - total_movements: Total movements scheduled for today
    - scheduled: Movements not yet started
    - in_progress: Movements currently underway
    - completed: Movements finished
    - cancelled: Movements cancelled
    - by_type: Breakdown by movement type
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:movements:today",
                compute_func=service.get_movements_today
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get movements: {str(e)}"}), 500


# ============================================================================
# Court Upcoming Endpoint
# ============================================================================

@dashboard_bp.route('/court/upcoming', methods=['GET'])
async def get_court_upcoming():
    """
    Get upcoming court appearances for next 7 days.

    Returns:
    - period_days: Number of days covered (7)
    - total_appearances: Total upcoming appearances
    - by_court_type: Breakdown by court (Magistrates, Supreme, etc.)
    - by_appearance_type: Breakdown by type (Arraignment, Trial, etc.)
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:court:upcoming",
                compute_func=service.get_court_upcoming
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get court appearances: {str(e)}"}), 500


# ============================================================================
# Releases Upcoming Endpoint
# ============================================================================

@dashboard_bp.route('/releases/upcoming', methods=['GET'])
async def get_releases_upcoming():
    """
    Get upcoming releases for next 30/60/90 days.

    Returns:
    - by_timeframe: Counts for 30/60/90 day periods
    - by_type: Breakdown by sentence type releasing
    - total_upcoming: Total releases in next 90 days
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:releases:upcoming",
                compute_func=service.get_releases_upcoming
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get releases: {str(e)}"}), 500


# ============================================================================
# Clemency Pending Endpoint
# ============================================================================

@dashboard_bp.route('/clemency/pending', methods=['GET'])
async def get_clemency_pending():
    """
    Get pending clemency petition summary.

    Returns:
    - total_pending: Total petitions in non-terminal states
    - by_status: Breakdown by workflow status
    - avg_days_in_status: Average days petitions spend in each status
    - oldest_pending: Details of the oldest pending petition
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:clemency:pending",
                compute_func=service.get_clemency_pending
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get clemency status: {str(e)}"}), 500


# ============================================================================
# Alerts Endpoint
# ============================================================================

@dashboard_bp.route('/alerts', methods=['GET'])
async def get_alerts():
    """
    Get system alerts requiring attention.

    Alert categories:
    - overcrowded_units: Housing units over capacity
    - overdue_classifications: Classifications past review date
    - missed_court_dates: Appearances without outcomes after date
    - expiring_sentences_no_plan: Releases within 7 days without movement

    Returns:
    - total_alerts: Total alert count
    - high/medium/low_severity: Counts by severity
    - Individual alert lists by category
    """
    try:
        async with get_async_session() as session:
            service = DashboardService(session)

            result = await get_cached_or_compute(
                cache_key="dashboard:alerts",
                compute_func=service.get_alerts
            )
            return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to get alerts: {str(e)}"}), 500


# ============================================================================
# Cache Invalidation Endpoint (Admin only)
# ============================================================================

@dashboard_bp.route('/cache/clear', methods=['POST'])
async def clear_cache():
    """
    Clear all dashboard cache entries.

    Admin endpoint to force fresh data retrieval.
    """
    try:
        cache_keys = [
            "dashboard:summary",
            "dashboard:population",
            "dashboard:movements:today",
            "dashboard:court:upcoming",
            "dashboard:releases:upcoming",
            "dashboard:clemency:pending",
            "dashboard:alerts"
        ]

        for key in cache_keys:
            await redis_client.delete(key)

        return jsonify({
            "message": "Dashboard cache cleared",
            "keys_cleared": cache_keys
        })

    except Exception as e:
        return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500
