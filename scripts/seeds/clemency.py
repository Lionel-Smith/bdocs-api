"""
BDOCS Seed Data - Prerogative of Mercy Reference

Advisory Committee on Prerogative of Mercy (2021-2026 appointments)
and clemency types from Constitution Articles 90-92.

Reference: Constitution of The Bahamas, Articles 90-92
- Article 90: Governor-General may pardon, grant respite, or commute
- Article 91: Advisory Committee composition and role
- Article 92: Exceptions for death sentences

CRITICAL: The Bahamas has NO parole system.
Early release is only possible through:
1. Prerogative of Mercy (clemency via Governor-General)
2. Statutory remission (up to 1/3 for good behavior - Prison Act)

Note: This is reference data for UI dropdowns and reporting.
The ClemencyPetition model uses PetitionType and PetitionStatus enums.
"""
from datetime import date

# Fixed UUIDs for referential integrity
COMMITTEE_MEMBER_IDS = {
    "MUNROE": "c1000001-0001-4000-8000-000000000001",
    "PINDER": "c1000001-0001-4000-8000-000000000002",
    "SMITH": "c1000001-0001-4000-8000-000000000003",
    "MCPHEE": "c1000001-0001-4000-8000-000000000004",
    "WELLS": "c1000001-0001-4000-8000-000000000005",
    "TINKER": "c1000001-0001-4000-8000-000000000006",
    "SEIDE": "c1000001-0001-4000-8000-000000000007",
}

# ============================================================================
# Advisory Committee on Prerogative of Mercy (2021-2026)
# ============================================================================
# Per Article 91 of the Constitution:
# - Chaired by the Minister of National Security (ex-officio)
# - Includes the Attorney General (ex-officio)
# - Not less than 3 and not more than 5 other members appointed by G-G
# ============================================================================

ADVISORY_COMMITTEE_MEMBERS = [
    {
        "id": COMMITTEE_MEMBER_IDS["MUNROE"],
        "name": "Hon. Wayne Munroe QC",
        "title": "MP",
        "position": "Chairman",
        "role": "Minister of National Security",
        "appointed_date": "2021-10-01",
        "term_end_date": "2026-09-30",
        "is_active": True,
        "is_ex_officio": True,
        "contact_email": "minister@mns.gov.bs",
        "contact_phone": "(242) 502-3300",
        "notes": "Ex-officio Chairman per Article 91(2)(a). Senior Counsel.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["PINDER"],
        "name": "Sen. Hon. Ryan Pinder",
        "title": "QC, MP",
        "position": "Deputy Chairman",
        "role": "Attorney General",
        "appointed_date": "2021-10-01",
        "term_end_date": "2026-09-30",
        "is_active": True,
        "is_ex_officio": True,
        "contact_email": "attorney.general@bahamas.gov.bs",
        "contact_phone": "(242) 502-0400",
        "notes": "Ex-officio member per Article 91(2)(b). Senator and Queen's Counsel.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["SMITH"],
        "name": "Bishop Lloyd Smith",
        "title": None,
        "position": "Member",
        "role": "Appointed Member",
        "appointed_date": "2021-11-15",
        "term_end_date": "2026-11-14",
        "is_active": True,
        "is_ex_officio": False,
        "organization": "Bahamas Christian Council",
        "contact_email": None,
        "contact_phone": None,
        "notes": "Religious community representative. BCC liaison.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["MCPHEE"],
        "name": "Bishop Helen McPhee",
        "title": None,
        "position": "Member",
        "role": "Appointed Member",
        "appointed_date": "2021-11-15",
        "term_end_date": "2026-11-14",
        "is_active": True,
        "is_ex_officio": False,
        "organization": None,
        "contact_email": None,
        "contact_phone": None,
        "notes": "Community advocate. Female perspective on rehabilitation.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["WELLS"],
        "name": "Apostle Raymond Wells",
        "title": None,
        "position": "Member",
        "role": "Appointed Member",
        "appointed_date": "2021-11-15",
        "term_end_date": "2026-11-14",
        "is_active": True,
        "is_ex_officio": False,
        "organization": None,
        "contact_email": None,
        "contact_phone": None,
        "notes": "Faith community leader. Prison ministry experience.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["TINKER"],
        "name": "Rudolph Tinker",
        "title": None,
        "position": "Member",
        "role": "Appointed Member",
        "appointed_date": "2021-11-15",
        "term_end_date": "2026-11-14",
        "is_active": True,
        "is_ex_officio": False,
        "organization": None,
        "contact_email": None,
        "contact_phone": None,
        "notes": "Community representative with justice system experience.",
    },
    {
        "id": COMMITTEE_MEMBER_IDS["SEIDE"],
        "name": "Dudley Seide",
        "title": None,
        "position": "Member",
        "role": "Appointed Member",
        "appointed_date": "2021-11-15",
        "term_end_date": "2026-11-14",
        "is_active": True,
        "is_ex_officio": False,
        "organization": None,
        "contact_email": None,
        "contact_phone": None,
        "notes": "Community representative with rehabilitation advocacy.",
    },
]

# ============================================================================
# Clemency Types
# ============================================================================
# These extend the PetitionType enum with detailed descriptions for UI/reports.
# The enum values are: PARDON, COMMUTATION, REMISSION, REPRIEVE
# ClemencyType enum also includes: RESPITE, EARLY_RELEASE
# ============================================================================

CLEMENCY_TYPES = [
    {
        "code": "PARDON",
        "name": "Full Pardon",
        "short_name": "Pardon",
        "description": "Complete forgiveness - conviction expunged from record. "
                       "Removes all legal consequences and restores full civil rights.",
        "constitutional_basis": "Article 90(1)(a)",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Exceptional rehabilitation demonstrated",
            "Significant time served",
            "Community support and reintegration plan",
            "No risk to public safety",
            "Circumstances of original offense",
        ],
        "notes": "Rarely granted. Reserved for exceptional cases where complete "
                 "exoneration is warranted. May require victim notification.",
    },
    {
        "code": "COMMUTATION",
        "name": "Commutation of Sentence",
        "short_name": "Commutation",
        "description": "Reduction of sentence to a lesser term. "
                       "Conviction remains but punishment is lessened.",
        "constitutional_basis": "Article 90(1)(c)",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Good behavior while incarcerated",
            "Participation in rehabilitation programmes",
            "Time already served",
            "Nature and severity of offense",
            "Age and health of petitioner",
        ],
        "notes": "Most common form of clemency. Reduces sentence length "
                 "without expunging conviction. Death sentences may be "
                 "commuted to life imprisonment (Article 92).",
    },
    {
        "code": "REMISSION",
        "name": "Remission of Sentence",
        "short_name": "Remission",
        "description": "Remainder of sentence remitted (forgiven). "
                       "Immediate release with time served credited.",
        "constitutional_basis": "Article 90(1)(d)",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Significant portion of sentence already served",
            "Exemplary conduct in custody",
            "Strong family and community support",
            "Approved reintegration plan",
            "Low recidivism risk assessment",
        ],
        "notes": "Different from statutory remission (automatic 1/3 off). "
                 "This is discretionary remission granted by G-G. "
                 "May include conditions similar to probation.",
    },
    {
        "code": "RESPITE",
        "name": "Respite",
        "short_name": "Respite",
        "description": "Temporary delay of sentence execution. "
                       "Postpones punishment for a defined period.",
        "constitutional_basis": "Article 90(1)(b)",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Medical condition requiring outside treatment",
            "Family emergency requiring presence",
            "Pending appeal or legal proceedings",
            "Humanitarian circumstances",
        ],
        "notes": "Temporary measure only. Does not reduce or eliminate "
                 "sentence - only delays execution. Used for death "
                 "penalty cases pending appeals (Article 92).",
    },
    {
        "code": "REPRIEVE",
        "name": "Reprieve",
        "short_name": "Reprieve",
        "description": "Postponement of sentence execution, especially "
                       "applicable to capital cases.",
        "constitutional_basis": "Article 90(1)(b), Article 92",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Pending appeal to Court of Appeal or Privy Council",
            "New evidence under consideration",
            "Constitutional challenge pending",
            "International legal proceedings",
        ],
        "notes": "Particularly relevant for death penalty cases. "
                 "Article 92 provides special provisions for capital cases "
                 "where appeal rights exist.",
    },
    {
        "code": "EARLY_RELEASE",
        "name": "Early Release on License",
        "short_name": "Early Release",
        "description": "Release before sentence completion with supervision "
                       "conditions. Subject to recall if conditions violated.",
        "constitutional_basis": "Article 90(1)(d) - implied authority",
        "requires_committee_review": True,
        "requires_minister_approval": True,
        "requires_governor_general": True,
        "typical_considerations": [
            "Minimum portion of sentence served",
            "Excellent institutional record",
            "Completed rehabilitation programmes",
            "Verified employment or education plan",
            "Stable housing arrangement",
            "Community supervision available",
        ],
        "notes": "Released inmate remains under sentence and can be "
                 "recalled to prison if license conditions violated. "
                 "This is NOT parole (no parole system in The Bahamas).",
    },
]

# ============================================================================
# Standard License Conditions for Early Release
# ============================================================================
# When clemency (especially early release) is granted, the G-G may impose
# conditions. These are standard conditions that may be applied.
# ============================================================================

LICENSE_CONDITIONS = [
    {
        "code": "REPORT",
        "name": "Regular Reporting",
        "description": "Report to supervising officer weekly at designated location",
        "category": "SUPERVISION",
        "is_standard": True,
        "can_be_modified": True,
        "typical_frequency": "Weekly",
        "notes": "Core condition for all early releases. Reporting frequency "
                 "may be adjusted based on risk level and compliance.",
    },
    {
        "code": "RESIDENCE",
        "name": "Approved Residence",
        "description": "Reside at approved address and notify of any change",
        "category": "HOUSING",
        "is_standard": True,
        "can_be_modified": False,
        "typical_frequency": None,
        "notes": "Address must be approved before release. Any change requires "
                 "advance approval from supervising authority.",
    },
    {
        "code": "EMPLOYMENT",
        "name": "Employment Requirement",
        "description": "Maintain lawful employment or approved education/training",
        "category": "STABILITY",
        "is_standard": True,
        "can_be_modified": True,
        "typical_frequency": None,
        "notes": "Unemployed licensees must actively seek work. BTVI programme "
                 "enrollment counts as approved activity.",
    },
    {
        "code": "NO_TRAVEL",
        "name": "Travel Restriction",
        "description": "Remain within The Bahamas and surrender passport",
        "category": "MOVEMENT",
        "is_standard": True,
        "can_be_modified": True,
        "typical_frequency": None,
        "notes": "Inter-island travel may require prior approval. International "
                 "travel prohibited unless specifically authorized.",
    },
    {
        "code": "NO_CONTACT",
        "name": "No Contact Order",
        "description": "No contact with victims, witnesses, or co-defendants",
        "category": "RESTRICTION",
        "is_standard": False,
        "can_be_modified": False,
        "typical_frequency": None,
        "notes": "Applied for violent offenses or cases with identified victims. "
                 "Violation is serious and may result in immediate recall.",
    },
    {
        "code": "NO_WEAPONS",
        "name": "Weapons Prohibition",
        "description": "No possession of firearms, ammunition, or offensive weapons",
        "category": "RESTRICTION",
        "is_standard": True,
        "can_be_modified": False,
        "typical_frequency": None,
        "notes": "Standard condition for all releases. Includes replica weapons "
                 "and items capable of causing injury.",
    },
    {
        "code": "NO_DRUGS",
        "name": "Substance Prohibition",
        "description": "Abstain from illegal drugs; alcohol restriction may apply",
        "category": "RESTRICTION",
        "is_standard": True,
        "can_be_modified": True,
        "typical_frequency": None,
        "notes": "Drug offenders may have complete substance prohibition. "
                 "Others may be restricted from excess alcohol consumption.",
    },
    {
        "code": "CURFEW",
        "name": "Curfew Requirement",
        "description": "Observe curfew hours (typically 10PM-6AM)",
        "category": "MOVEMENT",
        "is_standard": False,
        "can_be_modified": True,
        "typical_frequency": "Daily",
        "notes": "Applied based on risk assessment. Hours may be adjusted for "
                 "work requirements with documentation.",
    },
    {
        "code": "COUNSELING",
        "name": "Counseling Requirement",
        "description": "Attend mandated counseling or treatment sessions",
        "category": "REHABILITATION",
        "is_standard": False,
        "can_be_modified": True,
        "typical_frequency": "Weekly or as prescribed",
        "notes": "May include anger management, substance abuse treatment, "
                 "mental health counseling, or family therapy.",
    },
    {
        "code": "DRUG_TEST",
        "name": "Drug Testing",
        "description": "Submit to random drug and alcohol testing",
        "category": "MONITORING",
        "is_standard": False,
        "can_be_modified": True,
        "typical_frequency": "Random (typically monthly)",
        "notes": "Standard for drug-related offenses. Positive test or refusal "
                 "is treated as license violation.",
    },
]

# ============================================================================
# Summary Statistics
# ============================================================================

COMMITTEE_STATS = {
    "total_members": len(ADVISORY_COMMITTEE_MEMBERS),
    "ex_officio_members": len([m for m in ADVISORY_COMMITTEE_MEMBERS if m["is_ex_officio"]]),
    "appointed_members": len([m for m in ADVISORY_COMMITTEE_MEMBERS if not m["is_ex_officio"]]),
    "active_members": len([m for m in ADVISORY_COMMITTEE_MEMBERS if m["is_active"]]),
}

CLEMENCY_TYPE_STATS = {
    "total_types": len(CLEMENCY_TYPES),
    "requires_committee": len([c for c in CLEMENCY_TYPES if c["requires_committee_review"]]),
    "requires_gg": len([c for c in CLEMENCY_TYPES if c["requires_governor_general"]]),
}

LICENSE_CONDITION_STATS = {
    "total_conditions": len(LICENSE_CONDITIONS),
    "standard_conditions": len([c for c in LICENSE_CONDITIONS if c["is_standard"]]),
    "by_category": {
        category: len([c for c in LICENSE_CONDITIONS if c["category"] == category])
        for category in set(c["category"] for c in LICENSE_CONDITIONS)
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_committee_member_by_role(role: str) -> dict | None:
    """Get committee member by their role."""
    return next(
        (m for m in ADVISORY_COMMITTEE_MEMBERS if m["role"] == role),
        None
    )


def get_ex_officio_members() -> list:
    """Get all ex-officio (automatic) members."""
    return [m for m in ADVISORY_COMMITTEE_MEMBERS if m["is_ex_officio"]]


def get_appointed_members() -> list:
    """Get all appointed (non-ex-officio) members."""
    return [m for m in ADVISORY_COMMITTEE_MEMBERS if not m["is_ex_officio"]]


def get_clemency_type_by_code(code: str) -> dict | None:
    """Get clemency type details by code."""
    return next(
        (c for c in CLEMENCY_TYPES if c["code"] == code),
        None
    )


def get_license_condition_by_code(code: str) -> dict | None:
    """Get license condition by code."""
    return next(
        (c for c in LICENSE_CONDITIONS if c["code"] == code),
        None
    )


def get_standard_license_conditions() -> list:
    """Get all standard (default) license conditions."""
    return [c for c in LICENSE_CONDITIONS if c["is_standard"]]


def get_license_conditions_by_category(category: str) -> list:
    """Get all conditions in a category."""
    return [c for c in LICENSE_CONDITIONS if c["category"] == category]
