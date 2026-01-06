"""
BDOCS Seed Data - Related Agencies Reference

External agencies that interact with the BDOCS system.
Used for integration directory, contact management, and reporting.

Agency Types:
- GOVERNMENT: Bahamas government ministries/departments
- LAW_ENFORCEMENT: Police and security agencies
- JUDICIARY: Court system offices
- EDUCATION: Training and education providers
- INTERNATIONAL: International organizations
- PROGRAMME: Special programmes and initiatives

Note: This is reference data for contact directory and integration points.
"""

AGENCY_TYPES = [
    "GOVERNMENT",
    "LAW_ENFORCEMENT",
    "JUDICIARY",
    "EDUCATION",
    "INTERNATIONAL",
    "PROGRAMME",
    "HEALTHCARE",
    "COMMUNITY",
]

# Fixed UUIDs for referential integrity
AGENCY_IDS = {
    "MNS": "e1000001-0001-4000-8000-000000000001",
    "CSJP": "e1000001-0001-4000-8000-000000000002",
    "RBPF": "e1000001-0001-4000-8000-000000000003",
    "BTVI": "e1000001-0001-4000-8000-000000000004",
    "SC-REG": "e1000001-0001-4000-8000-000000000005",
    "DRS": "e1000001-0001-4000-8000-000000000006",
    "PMO": "e1000001-0001-4000-8000-000000000007",
    "IDB": "e1000001-0001-4000-8000-000000000008",
    "PMH": "e1000001-0001-4000-8000-000000000009",
    "MOH": "e1000001-0001-4000-8000-000000000010",
    "BDOCS": "e1000001-0001-4000-8000-000000000011",
}

RELATED_AGENCIES = [
    {
        "id": AGENCY_IDS["MNS"],
        "code": "MNS",
        "name": "Ministry of National Security",
        "full_name": "Ministry of National Security, The Bahamas",
        "type": "GOVERNMENT",
        "address": "Churchill Building, Rawson Square, Nassau",
        "phone": "(242) 502-3300",
        "fax": "(242) 356-3312",
        "email": "mnsinfo@bahamas.gov.bs",
        "website": "https://www.bahamas.gov.bs/nationalsecurity",
        "contact_person": "Minister of National Security",
        "contact_title": "The Honourable Minister",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "Parent ministry for BDOCS. Policy oversight and budget allocation.",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["CSJP"],
        "code": "CSJP",
        "name": "Citizen Security and Justice Programme",
        "full_name": "Citizen Security and Justice Programme (CSJP)",
        "type": "PROGRAMME",
        "address": "Ministry of Finance, Cecil Wallace Whitfield Centre, Cable Beach",
        "phone": "(242) 604-1016",
        "fax": None,
        "email": "csjp@bahamas.gov.bs",
        "website": "https://www.csjpbahamas.gov.bs",
        "contact_person": "Programme Manager",
        "contact_title": "Project Coordinator",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "IDB-funded programme BH-L1033. Funding for BDOCS modernization.",
        "funding_info": {
            "idb_loan": "BH-L1033",
            "total_amount": 20000000,
            "currency": "USD",
            "start_date": "2020-01-01",
            "end_date": "2025-12-31",
        },
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["RBPF"],
        "code": "RBPF",
        "name": "Royal Bahamas Police Force",
        "full_name": "Royal Bahamas Police Force",
        "type": "LAW_ENFORCEMENT",
        "address": "Police Headquarters, East Street, Nassau",
        "phone": "(242) 322-4444",
        "fax": "(242) 356-6347",
        "email": "rbpf@royalbahamaspolice.org",
        "website": "https://www.royalbahamaspolice.org",
        "contact_person": "Criminal Records Office",
        "contact_title": "Inspector",
        "operating_hours": "24/7",
        "integration_type": "API",
        "api_endpoint": "https://api.rbpf.gov.bs/v1",
        "notes": "Arrest records, intake coordination, warrant checks. Key integration partner.",
        "emergency_phone": "919 or (242) 322-4444",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["BTVI"],
        "code": "BTVI",
        "name": "Bahamas Technical and Vocational Institute",
        "full_name": "Bahamas Technical and Vocational Institute (BTVI)",
        "type": "EDUCATION",
        "address": "Old Trail Road, Nassau",
        "phone": "(242) 502-6300",
        "fax": "(242) 323-5728",
        "email": "info@btvi.edu.bs",
        "website": "https://www.btvi.edu.bs",
        "contact_person": "Registrar",
        "contact_title": "Director of Registrar's Office",
        "operating_hours": "8:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": "MANUAL",
        "api_endpoint": None,
        "notes": "Vocational training partner. Certification verification for inmates.",
        "programmes_offered": [
            "Auto Mechanics",
            "Barbering",
            "Basic Carpentry",
            "Basic Masonry",
            "Basic Electrical Installation",
            "Basic Plumbing",
            "Garment Manufacturing",
            "Information Technology",
            "Hair Dressing",
        ],
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["SC-REG"],
        "code": "SC-REG",
        "name": "Supreme Court Registry",
        "full_name": "Registry of the Supreme Court of The Bahamas",
        "type": "JUDICIARY",
        "address": "Bank Lane, Nassau",
        "phone": "(242) 322-3315",
        "fax": "(242) 323-6895",
        "email": "supremecourt@bahamas.gov.bs",
        "website": "https://www.bahamasjudiciary.com",
        "contact_person": "Registrar",
        "contact_title": "Registrar of the Supreme Court",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": "FOLIO",
        "api_endpoint": "https://folio.bahamasjudiciary.com/api/v1",
        "notes": "Court filings and records. Folio e-filing system integration.",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["DRS"],
        "code": "DRS",
        "name": "Department of Rehabilitative Services",
        "full_name": "Department of Rehabilitative Services",
        "type": "GOVERNMENT",
        "address": "Ministry of Social Services, Frederick Street, Nassau",
        "phone": "(242) 502-2800",
        "fax": None,
        "email": "socialservices@bahamas.gov.bs",
        "website": None,
        "contact_person": "Director",
        "contact_title": "Director of Rehabilitative Services",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "Post-release supervision, Second Chance programme, community reintegration.",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["PMO"],
        "code": "PMO",
        "name": "Prerogative of Mercy Unit",
        "full_name": "Prerogative of Mercy Unit, Ministry of National Security",
        "type": "GOVERNMENT",
        "address": "Ministry of National Security, Churchill Building, Rawson Square",
        "phone": "(242) 502-3300",
        "fax": "(242) 356-3312",
        "email": "pom@bahamas.gov.bs",
        "website": None,
        "contact_person": "Secretary to Advisory Committee",
        "contact_title": "Permanent Secretary Designate",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "Clemency petition processing. Advisory Committee on Prerogative of Mercy.",
        "constitutional_reference": "Articles 90-92, Constitution of The Bahamas",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["IDB"],
        "code": "IDB",
        "name": "Inter-American Development Bank - Nassau",
        "full_name": "Inter-American Development Bank, Country Office Bahamas",
        "type": "INTERNATIONAL",
        "address": "IDB Country Office, Nassau",
        "phone": "(242) 328-0088",
        "fax": None,
        "email": "idb-nassau@iadb.org",
        "website": "https://www.iadb.org/en/countries/bahamas",
        "contact_person": "Country Representative",
        "contact_title": "IDB Representative",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "CSJP funding oversight. Technical assistance and project monitoring.",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["PMH"],
        "code": "PMH",
        "name": "Princess Margaret Hospital",
        "full_name": "Princess Margaret Hospital",
        "type": "HEALTHCARE",
        "address": "Shirley Street, Nassau",
        "phone": "(242) 322-2861",
        "fax": "(242) 326-4654",
        "email": "pmh@bahamas.gov.bs",
        "website": None,
        "contact_person": "Medical Records Department",
        "contact_title": "Medical Records Supervisor",
        "operating_hours": "24/7 (Emergency)",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "Primary hospital for inmate medical emergencies and specialized care.",
        "emergency_phone": "(242) 322-2861",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["MOH"],
        "code": "MOH",
        "name": "Ministry of Health",
        "full_name": "Ministry of Health, The Bahamas",
        "type": "GOVERNMENT",
        "address": "Meeting Street, Nassau",
        "phone": "(242) 502-4700",
        "fax": "(242) 325-8487",
        "email": "moh@bahamas.gov.bs",
        "website": "https://www.bahamas.gov.bs/health",
        "contact_person": "Chief Medical Officer",
        "contact_title": "Chief Medical Officer",
        "operating_hours": "9:00 AM - 5:00 PM, Mon-Fri",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "Public health oversight for prison medical services.",
        "is_active": True,
    },
    {
        "id": AGENCY_IDS["BDOCS"],
        "code": "BDOCS",
        "name": "Bahamas Department of Correctional Services",
        "full_name": "Bahamas Department of Correctional Services (BDOCS)",
        "type": "GOVERNMENT",
        "address": "Fox Hill Road, Nassau",
        "phone": "(242) 364-9800",
        "fax": "(242) 364-9850",
        "email": "info@bdcs.gov.bs",
        "website": "https://www.bdcs.gov.bs",
        "contact_person": "Commissioner",
        "contact_title": "Commissioner of Correctional Services",
        "operating_hours": "24/7 (Operations)",
        "integration_type": None,
        "api_endpoint": None,
        "notes": "This system operator. Fox Hill Correctional Facility.",
        "latitude": 25.0478,
        "longitude": -77.2922,
        "is_active": True,
    },
]

# Summary statistics
AGENCY_STATS = {
    "total_agencies": len(RELATED_AGENCIES),
    "by_type": {
        agency_type: len([a for a in RELATED_AGENCIES if a["type"] == agency_type])
        for agency_type in AGENCY_TYPES
    },
    "with_api": len([a for a in RELATED_AGENCIES if a.get("api_endpoint")]),
    "active": len([a for a in RELATED_AGENCIES if a["is_active"]]),
}


def get_agency_by_code(code: str) -> dict | None:
    """Get agency by code for lookups."""
    return next((a for a in RELATED_AGENCIES if a["code"] == code), None)


def get_agencies_by_type(agency_type: str) -> list:
    """Get all agencies of a specific type."""
    return [a for a in RELATED_AGENCIES if a["type"] == agency_type]


def get_agencies_with_integration() -> list:
    """Get all agencies with API integration."""
    return [a for a in RELATED_AGENCIES if a.get("api_endpoint")]
