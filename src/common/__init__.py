"""BDOCS common utilities and enumerations."""
from src.common.enums import (
    InmateStatus,
    SecurityLevel,
    Gender,
    UserRole,
    ClemencyType,
    PetitionType,
    PetitionStatus,
    MovementType,
    MovementStatus,
    SentenceType,
    AdjustmentType,
    HearingType,
    IncidentType,
    AuditAction,
    CourtType,
    CaseStatus,
    AppearanceType,
    AppearanceOutcome,
)
from src.common.base_repository import AsyncBaseRepository

__all__ = [
    # Enums
    'InmateStatus',
    'SecurityLevel',
    'Gender',
    'UserRole',
    'ClemencyType',
    'PetitionType',
    'PetitionStatus',
    'MovementType',
    'MovementStatus',
    'SentenceType',
    'AdjustmentType',
    'HearingType',
    'IncidentType',
    'AuditAction',
    'CourtType',
    'CaseStatus',
    'AppearanceType',
    'AppearanceOutcome',
    # Repository
    'AsyncBaseRepository',
]
