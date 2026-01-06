"""
BDOCS Seed Data - Bahamian Courts Reference

Official court locations in The Bahamas for case management
and court appearance scheduling.

Source: Bahamas Judiciary official information
Reference: Courts Act (Chapter 54), The Bahamas

Court Types (from CourtType enum):
- MAGISTRATES: Minor offenses, preliminary inquiries
- SUPREME: Serious criminal cases
- COURT_OF_APPEAL: Appeals from Supreme Court
- PRIVY_COUNCIL: Final appellate (London)
- CORONERS: Death investigations

Note: This is reference data, not stored in a separate database table.
Court cases reference court_type enum values, this data provides
location/contact details for UI and reporting.
"""

# Fixed UUIDs for referential integrity
COURT_IDS = {
    "SC": "f1000001-0001-4000-8000-000000000001",
    "MC-NP": "f1000001-0001-4000-8000-000000000002",
    "MC-GB": "f1000001-0001-4000-8000-000000000003",
    "COA": "f1000001-0001-4000-8000-000000000004",
    "MC-AB": "f1000001-0001-4000-8000-000000000005",
    "MC-EL": "f1000001-0001-4000-8000-000000000006",
}

BAHAMAS_COURTS = [
    {
        "id": COURT_IDS["SC"],
        "code": "SC",
        "name": "Supreme Court of The Bahamas",
        "full_name": "The Supreme Court of the Commonwealth of The Bahamas",
        "court_type": "SUPREME",
        "location": "Nassau",
        "island": "New Providence",
        "address": "Bank Lane & Parliament Street, Nassau, Bahamas",
        "phone": "(242) 322-3315",
        "fax": "(242) 323-6895",
        "email": "supremecourt@bahamas.gov.bs",
        "handles": [
            "Murder",
            "Rape",
            "Armed Robbery",
            "Major felonies",
            "Appeals from Magistrates Court",
            "Constitutional matters",
        ],
        "case_number_prefix": "SC",
        "case_number_format": "SC-YYYY-CRI-NNNNN",
        "has_folio_integration": True,
        "folio_court_id": "SC-NP-001",
        "latitude": 25.0782,
        "longitude": -77.3431,
        "is_active": True,
        "notes": "Principal court for serious criminal matters. Handles all capital cases.",
    },
    {
        "id": COURT_IDS["MC-NP"],
        "code": "MC-NP",
        "name": "Magistrate's Court - New Providence",
        "full_name": "Magistrate's Court - District of New Providence",
        "court_type": "MAGISTRATES",
        "location": "Nassau",
        "island": "New Providence",
        "address": "Nassau Street, Nassau, Bahamas",
        "phone": "(242) 322-3512",
        "fax": "(242) 326-1455",
        "email": "magistratecourt.np@bahamas.gov.bs",
        "handles": [
            "Minor offenses",
            "Preliminary inquiries",
            "Bail hearings",
            "Summary offenses",
            "Traffic violations",
            "Minor assault",
            "Petty theft",
        ],
        "case_number_prefix": "MC",
        "case_number_format": "MC-YYYY-NNNNN",
        "has_folio_integration": False,
        "folio_court_id": None,
        "latitude": 25.0778,
        "longitude": -77.3418,
        "is_active": True,
        "notes": "Handles majority of remand hearings for Fox Hill inmates.",
    },
    {
        "id": COURT_IDS["MC-GB"],
        "code": "MC-GB",
        "name": "Magistrate's Court - Grand Bahama",
        "full_name": "Magistrate's Court - District of Grand Bahama",
        "court_type": "MAGISTRATES",
        "location": "Freeport",
        "island": "Grand Bahama",
        "address": "Mall Drive, Freeport, Grand Bahama, Bahamas",
        "phone": "(242) 352-2025",
        "fax": "(242) 352-3092",
        "email": "magistratecourt.gb@bahamas.gov.bs",
        "handles": [
            "Minor offenses",
            "Preliminary inquiries",
            "Bail hearings",
            "Summary offenses",
        ],
        "case_number_prefix": "MC-GB",
        "case_number_format": "MC-GB-YYYY-NNNNN",
        "has_folio_integration": False,
        "folio_court_id": None,
        "latitude": 26.5271,
        "longitude": -78.6519,
        "is_active": True,
        "notes": "Grand Bahama district court. Inmates transferred to Fox Hill for serious matters.",
    },
    {
        "id": COURT_IDS["COA"],
        "code": "COA",
        "name": "Court of Appeal",
        "full_name": "The Court of Appeal of the Commonwealth of The Bahamas",
        "court_type": "COURT_OF_APPEAL",
        "location": "Nassau",
        "island": "New Providence",
        "address": "British Colonial Hilton, Bay Street, Nassau",
        "phone": "(242) 322-3324",
        "fax": "(242) 322-3335",
        "email": "courtofappeal@bahamas.gov.bs",
        "handles": [
            "Appeals from Supreme Court",
            "Constitutional matters",
            "Sentence appeals",
            "Death penalty appeals",
        ],
        "case_number_prefix": "COA",
        "case_number_format": "COA-YYYY-NNNNN",
        "has_folio_integration": True,
        "folio_court_id": "COA-001",
        "latitude": 25.0790,
        "longitude": -77.3450,
        "is_active": True,
        "notes": "Handles appeals from Supreme Court. Death sentence appeals mandatory.",
    },
    {
        "id": COURT_IDS["MC-AB"],
        "code": "MC-AB",
        "name": "Magistrate's Court - Abaco",
        "full_name": "Magistrate's Court - District of Abaco",
        "court_type": "MAGISTRATES",
        "location": "Marsh Harbour",
        "island": "Abaco",
        "address": "Marsh Harbour, Abaco, Bahamas",
        "phone": "(242) 367-2662",
        "fax": "(242) 367-2025",
        "email": "magistratecourt.ab@bahamas.gov.bs",
        "handles": [
            "Minor offenses",
            "Preliminary inquiries",
            "Bail hearings",
        ],
        "case_number_prefix": "MC-AB",
        "case_number_format": "MC-AB-YYYY-NNNNN",
        "has_folio_integration": False,
        "folio_court_id": None,
        "latitude": 26.5417,
        "longitude": -77.0636,
        "is_active": True,
        "notes": "Family Island court. Circuit visits for major matters.",
    },
    {
        "id": COURT_IDS["MC-EL"],
        "code": "MC-EL",
        "name": "Magistrate's Court - Eleuthera",
        "full_name": "Magistrate's Court - District of Eleuthera",
        "court_type": "MAGISTRATES",
        "location": "Governor's Harbour",
        "island": "Eleuthera",
        "address": "Governor's Harbour, Eleuthera, Bahamas",
        "phone": "(242) 332-2774",
        "fax": "(242) 332-2093",
        "email": "magistratecourt.el@bahamas.gov.bs",
        "handles": [
            "Minor offenses",
            "Preliminary inquiries",
            "Bail hearings",
        ],
        "case_number_prefix": "MC-EL",
        "case_number_format": "MC-EL-YYYY-NNNNN",
        "has_folio_integration": False,
        "folio_court_id": None,
        "latitude": 25.1967,
        "longitude": -76.2389,
        "is_active": True,
        "notes": "Family Island court. Serves Eleuthera, Harbour Island, Spanish Wells.",
    },
]

# Summary statistics
COURT_STATS = {
    "total_courts": len(BAHAMAS_COURTS),
    "by_type": {
        "MAGISTRATES": len([c for c in BAHAMAS_COURTS if c["court_type"] == "MAGISTRATES"]),
        "SUPREME": len([c for c in BAHAMAS_COURTS if c["court_type"] == "SUPREME"]),
        "COURT_OF_APPEAL": len([c for c in BAHAMAS_COURTS if c["court_type"] == "COURT_OF_APPEAL"]),
    },
    "folio_integrated": len([c for c in BAHAMAS_COURTS if c["has_folio_integration"]]),
    "nassau_courts": len([c for c in BAHAMAS_COURTS if c["location"] == "Nassau"]),
    "family_island_courts": len([c for c in BAHAMAS_COURTS if c["island"] not in ["New Providence", "Grand Bahama"]]),
}


def get_court_by_code(code: str) -> dict | None:
    """Get court by code for lookups."""
    return next((c for c in BAHAMAS_COURTS if c["code"] == code), None)


def get_courts_by_type(court_type: str) -> list:
    """Get all courts of a specific type."""
    return [c for c in BAHAMAS_COURTS if c["court_type"] == court_type]


def get_courts_by_island(island: str) -> list:
    """Get all courts on a specific island."""
    return [c for c in BAHAMAS_COURTS if c["island"] == island]
