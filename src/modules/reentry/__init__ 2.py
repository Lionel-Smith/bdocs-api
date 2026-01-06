"""
BDOCS Reentry Planning Module - Preparing inmates for successful release.

Reentry planning is critical for reducing recidivism. This module tracks
comprehensive release preparation including:
- Housing arrangements
- Employment planning
- Documentation (ID, birth certificate, NIB card)
- External service referrals
- Family reunification

Three core entities:
- ReentryPlan: Master plan with housing, employment, documentation status
- ReentryChecklist: Specific items to complete before release
- ReentryReferral: Referrals to external support services

Key features:
- Auto-generated standard checklist items on plan creation
- Readiness score calculation (0-100%) based on completion
- Critical items tracking (ID, NIB card, housing)
- Upcoming release alerts and not-ready plan identification
- Support for multiple referral types to community services

Bahamas-specific elements:
- NIB (National Insurance Board) card requirement for employment
- Family-centric reintegration approach
- Local housing programme references
"""
from src.modules.reentry.models import ReentryPlan, ReentryChecklist, ReentryReferral
from src.modules.reentry.controller import reentry_bp, blueprint

__all__ = [
    'ReentryPlan',
    'ReentryChecklist',
    'ReentryReferral',
    'reentry_bp',
    'blueprint'
]
