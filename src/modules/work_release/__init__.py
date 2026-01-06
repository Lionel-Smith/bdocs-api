"""
BDOCS Work Release Module - Structured reintegration through employment.

Work release allows MINIMUM security inmates to work for approved
employers while serving their sentence. This supports:
- Gradual reintegration into society
- Job skill development
- Financial responsibility (savings, restitution)
- Reduced recidivism

Three core entities:
- WorkReleaseEmployer: Approved employers with MOU agreements
- WorkReleaseAssignment: Inmate work assignments with status workflow
- WorkReleaseLog: Daily departure/return tracking

CRITICAL: Only MINIMUM security inmates are eligible for work release.
This is enforced in approve_assignment() service method.

Key features:
- Employer MOU tracking with expiry validation
- Multi-step approval workflow for assignments
- Automatic late return detection
- No-show auto-suspension of assignments
- Daily activity reports and statistics
"""
from src.modules.work_release.models import (
    WorkReleaseEmployer,
    WorkReleaseAssignment,
    WorkReleaseLog
)
from src.modules.work_release.controller import work_release_bp, blueprint

__all__ = [
    'WorkReleaseEmployer',
    'WorkReleaseAssignment',
    'WorkReleaseLog',
    'work_release_bp',
    'blueprint'
]
