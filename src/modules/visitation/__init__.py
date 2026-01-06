"""
BDOCS Visitation Management Module - Visitor registration and visit scheduling.

This module handles visitor approval, visit scheduling, and check-in/out
processes for BDOCS facilities.

Three core entities:
- ApprovedVisitor: Visitor registry with background check requirement
- VisitSchedule: Visit scheduling with conflict detection
- VisitLog: Visit records including security checks

Key features:
- Background check required for visitor approval
- Visit conflict detection at scheduling time
- Check-in/out workflow with security logging
- Contraband discovery tracking linked to incidents
- Video visit support

Visit types: GENERAL, LEGAL (privileged), CLERGY, FAMILY_SPECIAL, VIDEO
ID types accepted: PASSPORT, DRIVERS_LICENSE, NIB_CARD, VOTER_CARD
"""
from src.modules.visitation.models import ApprovedVisitor, VisitSchedule, VisitLog
from src.modules.visitation.controller import visitation_bp, blueprint

__all__ = [
    'ApprovedVisitor',
    'VisitSchedule',
    'VisitLog',
    'visitation_bp',
    'blueprint'
]
