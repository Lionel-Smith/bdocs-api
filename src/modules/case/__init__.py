"""
BDOCS Case Management Module - Case officer assignments and rehabilitation tracking.

Case management is central to rehabilitation success. Each inmate
is assigned a case officer who provides structured support through:
- Regular assessments and progress monitoring
- Documented interactions via case notes
- SMART rehabilitation goals for reintegration

Three core entities:
- CaseAssignment: One active case officer per inmate
- CaseNote: Documented interactions and assessments
- RehabilitationGoal: Trackable goals for successful reintegration

Key features:
- Automatic transition when reassigning case officers
- Confidential note support for sensitive information
- Progress tracking with auto-completion
- Overdue goal alerts
"""
from src.modules.case.models import CaseAssignment, CaseNote, RehabilitationGoal
from src.modules.case.controller import case_bp, blueprint

__all__ = [
    'CaseAssignment',
    'CaseNote',
    'RehabilitationGoal',
    'case_bp',
    'blueprint'
]
