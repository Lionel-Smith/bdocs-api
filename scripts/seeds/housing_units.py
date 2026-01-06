"""
BDOCS Seed Data - Housing Units

Fox Hill Correctional Facility housing unit configuration.
Source: BDOCS_QUICK_REFERENCE.md

Housing Unit Model Fields:
- code: Unit code (e.g., MAX-A)
- name: Full unit name
- security_level: MAXIMUM | MEDIUM | MINIMUM
- capacity: Max inmates
- current_occupancy: Current count
- gender_restriction: MALE | FEMALE | NULL (any)
- is_active: Whether accepting inmates
- is_juvenile: Juvenile-only unit
- description: Unit notes and facility information

Note: The model only supports MAXIMUM, MEDIUM, MINIMUM security levels.
Special unit types (REMAND, MEDICAL, SEGREGATION) are mapped appropriately.
"""
from uuid import uuid4

# Fixed UUIDs for referential integrity across seeds
HOUSING_UNIT_IDS = {
    "MAX-A": "a1000001-0001-4000-8000-000000000001",
    "MAX-B": "a1000001-0001-4000-8000-000000000002",
    "MED-1": "a1000001-0001-4000-8000-000000000003",
    "MED-2": "a1000001-0001-4000-8000-000000000004",
    "MIN-1": "a1000001-0001-4000-8000-000000000005",
    "REM-1": "a1000001-0001-4000-8000-000000000006",
    "FEM-1": "a1000001-0001-4000-8000-000000000007",
    "MED-H": "a1000001-0001-4000-8000-000000000008",
    "JUV-1": "a1000001-0001-4000-8000-000000000009",
    "SEG-1": "a1000001-0001-4000-8000-000000000010",
    "DEATH-ROW": "a1000001-0001-4000-8000-000000000011",
}

HOUSING_UNITS = [
    {
        "id": HOUSING_UNIT_IDS["MAX-A"],
        "code": "MAX-A",
        "name": "Maximum Security Block A",
        "security_level": "MAXIMUM",
        "capacity": 100,
        "current_occupancy": 145,  # Overcrowded - 145% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Highest risk inmates. Facilities: dayroom, outdoor recreation area, "
            "shower facilities. Double-bunking due to overcrowding. "
            "Housing violent offenders and escape risks."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["MAX-B"],
        "code": "MAX-B",
        "name": "Maximum Security Block B",
        "security_level": "MAXIMUM",
        "capacity": 100,
        "current_occupancy": 138,  # 138% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Highest risk inmates. Facilities: dayroom, outdoor recreation area, "
            "shower facilities. Houses inmates with disciplinary issues and "
            "those requiring enhanced supervision."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["MED-1"],
        "code": "MED-1",
        "name": "Medium Security Unit 1",
        "security_level": "MEDIUM",
        "capacity": 200,
        "current_occupancy": 287,  # 143.5% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "General population. Facilities: dayroom, outdoor recreation area, "
            "shower facilities. Primary medium security housing unit."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["MED-2"],
        "code": "MED-2",
        "name": "Medium Security Unit 2",
        "security_level": "MEDIUM",
        "capacity": 200,
        "current_occupancy": 265,  # 132.5% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "General population. Facilities: dayroom, outdoor recreation area, "
            "shower facilities. Planned BTVI classroom conversion. "
            "Houses inmates eligible for vocational training programs."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["MIN-1"],
        "code": "MIN-1",
        "name": "Minimum Security Unit",
        "security_level": "MINIMUM",
        "capacity": 150,
        "current_occupancy": 112,  # 74.7% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Pre-release and low-risk inmates. Facilities: dayroom, "
            "outdoor recreation area, shower facilities. "
            "Work release eligible. Preparing for community reintegration."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["REM-1"],
        "code": "REM-1",
        "name": "Remand Centre",
        "security_level": "MEDIUM",  # Remand mapped to MEDIUM
        "capacity": 250,
        "current_occupancy": 312,  # 124.8% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Pre-trial detainees awaiting court. Facilities: dayroom, "
            "outdoor recreation area, shower facilities. "
            "Remand prisoners (~37% of total population). "
            "Separate from sentenced inmates per legal requirements."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["FEM-1"],
        "code": "FEM-1",
        "name": "Female Correctional Facility",
        "security_level": "MEDIUM",  # Female unit, mixed security levels
        "capacity": 50,
        "current_occupancy": 48,  # 96% occupancy
        "gender_restriction": "FEMALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "All female inmates (sentenced and remand). Facilities: dayroom, "
            "outdoor recreation area, shower facilities. "
            "Separate facility from male population. "
            "Includes specialized programs for women."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["MED-H"],
        "code": "MED-H",
        "name": "Medical Block",
        "security_level": "MEDIUM",  # Medical mapped to MEDIUM
        "capacity": 30,
        "current_occupancy": 22,  # 73.3% occupancy
        "gender_restriction": None,  # Both genders for medical
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Medical needs housing. Facilities: shower facilities. "
            "No dayroom or outdoor recreation - patients in recovery. "
            "Adjacent to prison infirmary. 24-hour nursing staff. "
            "Handles chronic conditions and post-operative care."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["JUV-1"],
        "code": "JUV-1",
        "name": "Juvenile Detention Facility",
        "security_level": "MEDIUM",  # Juvenile mapped to MEDIUM
        "capacity": 20,
        "current_occupancy": 8,  # 40% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": True,  # Juvenile-only flag
        "description": (
            "Male youth offenders (under 18). Facilities: dayroom, "
            "outdoor recreation area, shower facilities. "
            "On-staff psychologist. Separate from adult population. "
            "Education-focused with mandatory schooling."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["SEG-1"],
        "code": "SEG-1",
        "name": "Segregation Unit",
        "security_level": "MAXIMUM",  # Segregation mapped to MAXIMUM
        "capacity": 30,
        "current_occupancy": 18,  # 60% occupancy
        "gender_restriction": None,  # Both genders possible
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Disciplinary and protective custody. Facilities: "
            "limited outdoor recreation (1 hour/day), shower facilities. "
            "No dayroom access. Single-cell housing. "
            "Used for administrative segregation, protective custody, "
            "and disciplinary isolation. Regular psychological monitoring."
        ),
    },
    {
        "id": HOUSING_UNIT_IDS["DEATH-ROW"],
        "code": "DEATH-ROW",
        "name": "Death Row",
        "security_level": "MAXIMUM",
        "capacity": 10,
        "current_occupancy": 2,  # 20% occupancy
        "gender_restriction": "MALE",
        "is_active": True,
        "is_juvenile": False,
        "description": (
            "Capital punishment inmates. Facilities: "
            "limited outdoor recreation (supervised), shower facilities. "
            "No dayroom access. Maximum security single cells. "
            "Separate from general population. "
            "Awaiting execution or appeal outcomes."
        ),
    },
]

# Summary statistics for verification
HOUSING_STATS = {
    "total_units": len(HOUSING_UNITS),
    "total_capacity": sum(u["capacity"] for u in HOUSING_UNITS),
    "total_population": sum(u["current_occupancy"] for u in HOUSING_UNITS),
    "occupancy_rate": round(
        sum(u["current_occupancy"] for u in HOUSING_UNITS)
        / sum(u["capacity"] for u in HOUSING_UNITS)
        * 100,
        1,
    ),
}

# Calculated: Capacity 1,140 | Population 1,357 | Occupancy 119% (overcrowded)
