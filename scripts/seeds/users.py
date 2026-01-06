"""
BDOCS Seed Data - System Users

Authentic Bahamian names with proper BDOCS role assignments.
Email domain: @bdcs.gov.bs (Bahamas Department of Correctional Services)
Phone prefix: (242) 364-XXXX (Fox Hill area)

Source: Common Bahamian surnames (Rolle, Ferguson, Johnson, Butler, etc.)

User Model Fields:
- username: Unique login (lowercase, letters/numbers/dots/underscores)
- email: Official email address
- password_hash: bcrypt hashed password
- first_name, last_name: Personal name
- role: ADMIN | SUPERVISOR | OFFICER | INTAKE | PROGRAMMES | MEDICAL | RECORDS | READONLY
- badge_number: Unique badge ID
- phone: (242) XXX-XXXX format
- position: Job title
- assigned_unit: Housing unit code (for officers/supervisors)
- shift: DAY | EVENING | NIGHT
- is_active, is_system_account, is_external: Account flags
- must_change_password: Force password change on first login
"""
from uuid import uuid4

# Fixed UUIDs for referential integrity
USER_IDS = {
    "admin": "d1000001-0001-4000-8000-000000000001",
    "d.cleare": "d1000001-0001-4000-8000-000000000002",
    "t.rolle": "d1000001-0001-4000-8000-000000000003",
    "s.ferguson": "d1000001-0001-4000-8000-000000000004",
    "k.johnson": "d1000001-0001-4000-8000-000000000005",
    "m.butler": "d1000001-0001-4000-8000-000000000006",
    "a.dean": "d1000001-0001-4000-8000-000000000007",
    "j.smith": "d1000001-0001-4000-8000-000000000008",
    "r.williams": "d1000001-0001-4000-8000-000000000009",
    "c.bain": "d1000001-0001-4000-8000-000000000010",
    "d.thompson": "d1000001-0001-4000-8000-000000000011",
    "n.mcphee": "d1000001-0001-4000-8000-000000000012",
    "dr.moss": "d1000001-0001-4000-8000-000000000013",
    "n.clarke": "d1000001-0001-4000-8000-000000000014",
    "p.seymour": "d1000001-0001-4000-8000-000000000015",
    "aca.auditor": "d1000001-0001-4000-8000-000000000016",
}

# Default password for demo accounts (MUST be changed in production)
# Password: BDOCS2026Demo!
DEFAULT_PASSWORD = "BDOCS2026Demo!"

SYSTEM_USERS = [
    # ========================================================================
    # ADMIN Role - Full system access
    # ========================================================================
    {
        "id": USER_IDS["admin"],
        "username": "admin",
        "email": "admin@bdcs.gov.bs",
        "first_name": "System",
        "last_name": "Administrator",
        "role": "ADMIN",
        "badge_number": "ADMIN-001",
        "phone": "(242) 364-9800",
        "position": "System Administrator",
        "assigned_unit": None,
        "shift": None,
        "is_active": True,
        "is_system_account": True,
        "is_external": False,
        "must_change_password": False,  # System account
    },
    {
        "id": USER_IDS["d.cleare"],
        "username": "d.cleare",
        "email": "commissioner@bdcs.gov.bs",
        "first_name": "Doan",
        "last_name": "Cleare",
        "role": "ADMIN",
        "badge_number": "COM-001",
        "phone": "(242) 364-9802",
        "position": "Commissioner",
        "assigned_unit": None,
        "shift": None,
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # SUPERVISOR Role - Department supervisors
    # ========================================================================
    {
        "id": USER_IDS["t.rolle"],
        "username": "t.rolle",
        "email": "t.rolle@bdcs.gov.bs",
        "first_name": "Terrance",
        "last_name": "Rolle",
        "role": "SUPERVISOR",
        "badge_number": "SUP-101",
        "phone": "(242) 364-9811",
        "position": "Chief Correctional Officer",
        "assigned_unit": "MAX-A",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["s.ferguson"],
        "username": "s.ferguson",
        "email": "s.ferguson@bdcs.gov.bs",
        "first_name": "Shantell",
        "last_name": "Ferguson",
        "role": "SUPERVISOR",
        "badge_number": "SUP-102",
        "phone": "(242) 364-9812",
        "position": "Chief Correctional Officer - Female Facility",
        "assigned_unit": "FEM-1",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["k.johnson"],
        "username": "k.johnson",
        "email": "k.johnson@bdcs.gov.bs",
        "first_name": "Kevin",
        "last_name": "Johnson",
        "role": "SUPERVISOR",
        "badge_number": "SUP-103",
        "phone": "(242) 364-9813",
        "position": "Remand Centre Supervisor",
        "assigned_unit": "REM-1",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # OFFICER Role - Correctional officers
    # ========================================================================
    {
        "id": USER_IDS["m.butler"],
        "username": "m.butler",
        "email": "m.butler@bdcs.gov.bs",
        "first_name": "Michael",
        "last_name": "Butler",
        "role": "OFFICER",
        "badge_number": "OFF-201",
        "phone": "(242) 364-9820",
        "position": "Correctional Officer",
        "assigned_unit": "MAX-A",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["a.dean"],
        "username": "a.dean",
        "email": "a.dean@bdcs.gov.bs",
        "first_name": "Antoinette",
        "last_name": "Dean",
        "role": "OFFICER",
        "badge_number": "OFF-202",
        "phone": "(242) 364-9821",
        "position": "Correctional Officer",
        "assigned_unit": "FEM-1",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["j.smith"],
        "username": "j.smith",
        "email": "j.smith@bdcs.gov.bs",
        "first_name": "Jamaal",
        "last_name": "Smith",
        "role": "OFFICER",
        "badge_number": "OFF-203",
        "phone": "(242) 364-9822",
        "position": "Correctional Officer",
        "assigned_unit": "MED-1",
        "shift": "NIGHT",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # INTAKE Role - Intake processing
    # ========================================================================
    {
        "id": USER_IDS["r.williams"],
        "username": "r.williams",
        "email": "r.williams@bdcs.gov.bs",
        "first_name": "Rashad",
        "last_name": "Williams",
        "role": "INTAKE",
        "badge_number": "INT-301",
        "phone": "(242) 364-9830",
        "position": "Intake Officer",
        "assigned_unit": None,
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["c.bain"],
        "username": "c.bain",
        "email": "c.bain@bdcs.gov.bs",
        "first_name": "Crystal",
        "last_name": "Bain",
        "role": "INTAKE",
        "badge_number": "INT-302",
        "phone": "(242) 364-9831",
        "position": "Intake Officer",
        "assigned_unit": None,
        "shift": "EVENING",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # PROGRAMMES Role - Programme management
    # ========================================================================
    {
        "id": USER_IDS["d.thompson"],
        "username": "d.thompson",
        "email": "d.thompson@bdcs.gov.bs",
        "first_name": "Derek",
        "last_name": "Thompson",
        "role": "PROGRAMMES",
        "badge_number": "PRG-401",
        "phone": "(242) 364-9840",
        "position": "Programme Coordinator",
        "assigned_unit": None,
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["n.mcphee"],
        "username": "n.mcphee",
        "email": "n.mcphee@bdcs.gov.bs",
        "first_name": "Natasha",
        "last_name": "McPhee",
        "role": "PROGRAMMES",
        "badge_number": "PRG-402",
        "phone": "(242) 364-9841",
        "position": "BTVI Liaison",
        "assigned_unit": None,
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # MEDICAL Role - Healthcare access
    # ========================================================================
    {
        "id": USER_IDS["dr.moss"],
        "username": "dr.moss",
        "email": "dr.moss@bdcs.gov.bs",
        "first_name": "Patricia",
        "last_name": "Moss",
        "role": "MEDICAL",
        "badge_number": "MED-501",
        "phone": "(242) 364-9850",
        "position": "Chief Medical Officer",
        "assigned_unit": "MED-H",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },
    {
        "id": USER_IDS["n.clarke"],
        "username": "n.clarke",
        "email": "n.clarke@bdcs.gov.bs",
        "first_name": "Nicole",
        "last_name": "Clarke",
        "role": "MEDICAL",
        "badge_number": "MED-502",
        "phone": "(242) 364-9851",
        "position": "Staff Nurse",
        "assigned_unit": "MED-H",
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # RECORDS Role - Records department
    # ========================================================================
    {
        "id": USER_IDS["p.seymour"],
        "username": "p.seymour",
        "email": "p.seymour@bdcs.gov.bs",
        "first_name": "Patrice",
        "last_name": "Seymour",
        "role": "RECORDS",
        "badge_number": "REC-601",
        "phone": "(242) 364-9860",
        "position": "Records Clerk",
        "assigned_unit": None,
        "shift": "DAY",
        "is_active": True,
        "is_system_account": False,
        "is_external": False,
        "must_change_password": True,
    },

    # ========================================================================
    # READONLY Role - View-only access (auditors, etc.)
    # ========================================================================
    {
        "id": USER_IDS["aca.auditor"],
        "username": "aca.auditor",
        "email": "auditor@aca.org",
        "first_name": "ACA",
        "last_name": "Auditor",
        "role": "READONLY",
        "badge_number": "AUD-001",
        "phone": None,
        "position": "External Auditor",
        "assigned_unit": None,
        "shift": None,
        "is_active": True,
        "is_system_account": False,
        "is_external": True,
        "must_change_password": True,
    },
]

# Summary statistics
USER_STATS = {
    "total_users": len(SYSTEM_USERS),
    "by_role": {
        "ADMIN": len([u for u in SYSTEM_USERS if u["role"] == "ADMIN"]),
        "SUPERVISOR": len([u for u in SYSTEM_USERS if u["role"] == "SUPERVISOR"]),
        "OFFICER": len([u for u in SYSTEM_USERS if u["role"] == "OFFICER"]),
        "INTAKE": len([u for u in SYSTEM_USERS if u["role"] == "INTAKE"]),
        "PROGRAMMES": len([u for u in SYSTEM_USERS if u["role"] == "PROGRAMMES"]),
        "MEDICAL": len([u for u in SYSTEM_USERS if u["role"] == "MEDICAL"]),
        "RECORDS": len([u for u in SYSTEM_USERS if u["role"] == "RECORDS"]),
        "READONLY": len([u for u in SYSTEM_USERS if u["role"] == "READONLY"]),
    },
    "internal_users": len([u for u in SYSTEM_USERS if not u["is_external"]]),
    "external_users": len([u for u in SYSTEM_USERS if u["is_external"]]),
}
