"""
BDOCS Admin Dashboard Module.

Aggregates statistics from all modules:
- Inmate population and status
- Housing capacity and utilization
- Movements (today and scheduled)
- Court appearances (upcoming)
- Sentence releases (upcoming)
- Clemency petitions (pending)
- System alerts

All endpoints use Redis caching with 5-minute TTL.
"""
from src.modules.dashboard.controller import dashboard_bp

__all__ = ['dashboard_bp']
