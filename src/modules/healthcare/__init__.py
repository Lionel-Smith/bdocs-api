"""
BDOCS Healthcare Management Module - Medical records and treatment tracking.

HIPAA NOTE: This module handles Protected Health Information (PHI).
All access must be controlled through role-based access control.
Only authorized medical personnel should access these records.

Three core entities:
- MedicalRecord: Comprehensive health profile (one per inmate)
- MedicalEncounter: Individual medical visits and treatments
- MedicationAdministration: Medication scheduling and tracking

Key features:
- Intake screening on admission (create_intake_screening)
- Suicide watch monitoring (get_suicide_watch_inmates)
- Medication administration with refusal witness requirement
- Follow-up and physical examination scheduling

Encounter types: INTAKE_SCREENING, SICK_CALL, EMERGENCY, SCHEDULED,
                 MENTAL_HEALTH, DENTAL, FOLLOW_UP

Provider types: PHYSICIAN, NURSE, MENTAL_HEALTH, DENTIST, PARAMEDIC

CRITICAL: suicide_watch flag requires immediate safety monitoring.
"""
from src.modules.healthcare.models import (
    MedicalRecord, MedicalEncounter, MedicationAdministration
)
from src.modules.healthcare.controller import healthcare_bp, blueprint

__all__ = [
    'MedicalRecord',
    'MedicalEncounter',
    'MedicationAdministration',
    'healthcare_bp',
    'blueprint'
]
