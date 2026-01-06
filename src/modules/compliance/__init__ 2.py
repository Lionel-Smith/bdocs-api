"""
BDOCS ACA Compliance Reporting Module - Standards tracking and audit management.

This module handles American Correctional Association (ACA) compliance standards,
audits, and findings for BDOCS facilities. Essential for maintaining accreditation.

Reference: ACA Performance-Based Standards for Adult Correctional Institutions

Three core entities:
- ACAStandard: Reference library of compliance standards (seeded data)
- ComplianceAudit: Audit records (self-assessment, mock, official)
- AuditFinding: Individual standard findings within an audit

Key features:
- Standards organized by ACA category (SAFETY, SECURITY, CARE, etc.)
- Mandatory standards tracking (required for accreditation)
- Compliance scoring (Compliant=1pt, Partial=0.5pt, Non-Compliant=0pt)
- Corrective action tracking with due dates and completion verification
- Comprehensive reports aggregating data from all BDOCS modules

Audit types: SELF_ASSESSMENT, MOCK, OFFICIAL

Compliance statuses: COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE

CRITICAL: Mandatory standards MUST be met for ACA accreditation.
Track overdue corrective actions via get_overdue_corrective_actions().
"""
from src.modules.compliance.models import (
    ACAStandard, ComplianceAudit, AuditFinding
)
from src.modules.compliance.controller import compliance_bp, blueprint

__all__ = [
    'ACAStandard',
    'ComplianceAudit',
    'AuditFinding',
    'compliance_bp',
    'blueprint'
]
