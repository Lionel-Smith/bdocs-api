"""
BDOCS Staff Management Module - Personnel and scheduling management.

This module handles correctional staff records, shift scheduling,
and training/certification tracking for BDOCS facilities.

Three core entities:
- Staff: Personnel records linked to auth users (EMP-NNNNN format)
- StaffShift: Duty schedules with post assignments
- StaffTraining: Certifications with expiry tracking

Key features:
- Auto-generated employee numbers
- Shift scheduling with housing unit assignments
- On-duty staff tracking
- Certification expiry monitoring (get_expiring_certifications)
- Staff statistics dashboard

Departments: ADMINISTRATION, SECURITY, PROGRAMMES, MEDICAL, RECORDS, MAINTENANCE, KITCHEN
Ranks: SUPERINTENDENT → DEPUTY → ASSISTANT → CHIEF_OFFICER → SENIOR_OFFICER → OFFICER → RECRUIT
"""
from src.modules.staff.models import Staff, StaffShift, StaffTraining
from src.modules.staff.controller import staff_bp, blueprint

__all__ = [
    'Staff',
    'StaffShift',
    'StaffTraining',
    'staff_bp',
    'blueprint'
]
