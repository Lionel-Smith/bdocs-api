"""
BDOCS Programme Module - Rehabilitation programmes.

Supports inmate rehabilitation through:
- Educational programmes (GED, literacy)
- Vocational training (carpentry, plumbing, etc.)
- Therapeutic programmes (substance abuse, anger management)
- Religious programmes (faith-based initiatives)
- Life skills (financial literacy, parenting)

Key features:
- Programme definition with eligibility criteria
- Session scheduling and attendance tracking
- Enrollment management with capacity checks
- Completion tracking with grades and certification
"""
from src.modules.programme.models import Programme, ProgrammeSession, ProgrammeEnrollment
from src.modules.programme.controller import programme_bp, blueprint

__all__ = [
    'Programme',
    'ProgrammeSession',
    'ProgrammeEnrollment',
    'programme_bp',
    'blueprint'
]
