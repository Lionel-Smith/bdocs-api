"""
BDOCS Seed Data - Staff Records

Staff records linked to system users with training records.
Creates staff profiles for correctional officers, supervisors, and other personnel.

Staff Model Fields:
- user_id: Link to auth users table (required, one-to-one)
- employee_number: Format EMP-NNNNN (unique)
- first_name, last_name: Personal name
- rank: SUPERINTENDENT | DEPUTY_SUPERINTENDENT | CHIEF_OFFICER | SENIOR_OFFICER | OFFICER | TRAINEE
- department: ADMINISTRATION | SECURITY | PROGRAMMES | MEDICAL | RECORDS | MAINTENANCE
- hire_date: Employment start date
- status: ACTIVE | ON_LEAVE | SUSPENDED | TERMINATED
- phone: (242) XXX-XXXX format
- emergency_contact_name, emergency_contact_phone: Emergency contact info
- certifications: JSONB array of certifications
- is_active: Boolean flag
"""
from datetime import date, timedelta
from uuid import uuid4

# Import user IDs for linking
from scripts.seeds.users import USER_IDS

# Fixed UUIDs for staff referential integrity
STAFF_IDS = {
    "d.cleare": "e2000001-0001-4000-8000-000000000001",
    "t.rolle": "e2000001-0001-4000-8000-000000000002",
    "s.ferguson": "e2000001-0001-4000-8000-000000000003",
    "k.johnson": "e2000001-0001-4000-8000-000000000004",
    "m.butler": "e2000001-0001-4000-8000-000000000005",
    "a.dean": "e2000001-0001-4000-8000-000000000006",
    "j.smith": "e2000001-0001-4000-8000-000000000007",
    "r.williams": "e2000001-0001-4000-8000-000000000008",
    "c.bain": "e2000001-0001-4000-8000-000000000009",
    "d.thompson": "e2000001-0001-4000-8000-000000000010",
    "n.mcphee": "e2000001-0001-4000-8000-000000000011",
    "dr.moss": "e2000001-0001-4000-8000-000000000012",
    "n.clarke": "e2000001-0001-4000-8000-000000000013",
    "p.seymour": "e2000001-0001-4000-8000-000000000014",
}

STAFF_MEMBERS = [
    # ========================================================================
    # ADMINISTRATION - Leadership
    # ========================================================================
    {
        "id": STAFF_IDS["d.cleare"],
        "user_id": USER_IDS["d.cleare"],
        "employee_number": "EMP-00001",
        "first_name": "Doan",
        "last_name": "Cleare",
        "rank": "SUPERINTENDENT",
        "department": "ADMINISTRATION",
        "hire_date": date(2005, 3, 15),
        "status": "ACTIVE",
        "phone": "(242) 364-9802",
        "emergency_contact_name": "Marie Cleare",
        "emergency_contact_phone": "(242) 393-5521",
        "is_active": True,
    },

    # ========================================================================
    # SECURITY - Supervisors
    # ========================================================================
    {
        "id": STAFF_IDS["t.rolle"],
        "user_id": USER_IDS["t.rolle"],
        "employee_number": "EMP-00101",
        "first_name": "Terrance",
        "last_name": "Rolle",
        "rank": "CHIEF_OFFICER",
        "department": "SECURITY",
        "hire_date": date(2010, 6, 1),
        "status": "ACTIVE",
        "phone": "(242) 364-9811",
        "emergency_contact_name": "Sandra Rolle",
        "emergency_contact_phone": "(242) 341-2215",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["s.ferguson"],
        "user_id": USER_IDS["s.ferguson"],
        "employee_number": "EMP-00102",
        "first_name": "Shantell",
        "last_name": "Ferguson",
        "rank": "CHIEF_OFFICER",
        "department": "SECURITY",
        "hire_date": date(2012, 9, 15),
        "status": "ACTIVE",
        "phone": "(242) 364-9812",
        "emergency_contact_name": "David Ferguson",
        "emergency_contact_phone": "(242) 327-8843",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["k.johnson"],
        "user_id": USER_IDS["k.johnson"],
        "employee_number": "EMP-00103",
        "first_name": "Kevin",
        "last_name": "Johnson",
        "rank": "CHIEF_OFFICER",
        "department": "SECURITY",
        "hire_date": date(2011, 2, 1),
        "status": "ACTIVE",
        "phone": "(242) 364-9813",
        "emergency_contact_name": "Lisa Johnson",
        "emergency_contact_phone": "(242) 393-1127",
        "is_active": True,
    },

    # ========================================================================
    # SECURITY - Officers
    # ========================================================================
    {
        "id": STAFF_IDS["m.butler"],
        "user_id": USER_IDS["m.butler"],
        "employee_number": "EMP-00201",
        "first_name": "Michael",
        "last_name": "Butler",
        "rank": "SENIOR_OFFICER",
        "department": "SECURITY",
        "hire_date": date(2015, 4, 10),
        "status": "ACTIVE",
        "phone": "(242) 364-9820",
        "emergency_contact_name": "Angela Butler",
        "emergency_contact_phone": "(242) 361-4452",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["a.dean"],
        "user_id": USER_IDS["a.dean"],
        "employee_number": "EMP-00202",
        "first_name": "Antoinette",
        "last_name": "Dean",
        "rank": "SENIOR_OFFICER",
        "department": "SECURITY",
        "hire_date": date(2016, 8, 22),
        "status": "ACTIVE",
        "phone": "(242) 364-9821",
        "emergency_contact_name": "Robert Dean",
        "emergency_contact_phone": "(242) 324-6789",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["j.smith"],
        "user_id": USER_IDS["j.smith"],
        "employee_number": "EMP-00203",
        "first_name": "Jamaal",
        "last_name": "Smith",
        "rank": "OFFICER",
        "department": "SECURITY",
        "hire_date": date(2019, 1, 7),
        "status": "ACTIVE",
        "phone": "(242) 364-9822",
        "emergency_contact_name": "Karen Smith",
        "emergency_contact_phone": "(242) 394-5523",
        "is_active": True,
    },

    # ========================================================================
    # INTAKE - Processing Officers
    # ========================================================================
    {
        "id": STAFF_IDS["r.williams"],
        "user_id": USER_IDS["r.williams"],
        "employee_number": "EMP-00301",
        "first_name": "Rashad",
        "last_name": "Williams",
        "rank": "OFFICER",
        "department": "ADMINISTRATION",
        "hire_date": date(2018, 5, 15),
        "status": "ACTIVE",
        "phone": "(242) 364-9830",
        "emergency_contact_name": "Tracy Williams",
        "emergency_contact_phone": "(242) 322-1198",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["c.bain"],
        "user_id": USER_IDS["c.bain"],
        "employee_number": "EMP-00302",
        "first_name": "Crystal",
        "last_name": "Bain",
        "rank": "OFFICER",
        "department": "ADMINISTRATION",
        "hire_date": date(2020, 3, 1),
        "status": "ACTIVE",
        "phone": "(242) 364-9831",
        "emergency_contact_name": "James Bain",
        "emergency_contact_phone": "(242) 361-7234",
        "is_active": True,
    },

    # ========================================================================
    # PROGRAMMES - Coordinators
    # ========================================================================
    {
        "id": STAFF_IDS["d.thompson"],
        "user_id": USER_IDS["d.thompson"],
        "employee_number": "EMP-00401",
        "first_name": "Derek",
        "last_name": "Thompson",
        "rank": "SENIOR_OFFICER",
        "department": "PROGRAMMES",
        "hire_date": date(2014, 10, 20),
        "status": "ACTIVE",
        "phone": "(242) 364-9840",
        "emergency_contact_name": "Michelle Thompson",
        "emergency_contact_phone": "(242) 327-5567",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["n.mcphee"],
        "user_id": USER_IDS["n.mcphee"],
        "employee_number": "EMP-00402",
        "first_name": "Natasha",
        "last_name": "McPhee",
        "rank": "OFFICER",
        "department": "PROGRAMMES",
        "hire_date": date(2017, 7, 12),
        "status": "ACTIVE",
        "phone": "(242) 364-9841",
        "emergency_contact_name": "Paul McPhee",
        "emergency_contact_phone": "(242) 394-8891",
        "is_active": True,
    },

    # ========================================================================
    # MEDICAL - Healthcare Staff
    # ========================================================================
    {
        "id": STAFF_IDS["dr.moss"],
        "user_id": USER_IDS["dr.moss"],
        "employee_number": "EMP-00501",
        "first_name": "Patricia",
        "last_name": "Moss",
        "rank": "CHIEF_OFFICER",  # Medical Director equivalent
        "department": "MEDICAL",
        "hire_date": date(2008, 11, 1),
        "status": "ACTIVE",
        "phone": "(242) 364-9850",
        "emergency_contact_name": "Richard Moss",
        "emergency_contact_phone": "(242) 323-4456",
        "is_active": True,
    },
    {
        "id": STAFF_IDS["n.clarke"],
        "user_id": USER_IDS["n.clarke"],
        "employee_number": "EMP-00502",
        "first_name": "Nicole",
        "last_name": "Clarke",
        "rank": "OFFICER",
        "department": "MEDICAL",
        "hire_date": date(2019, 9, 5),
        "status": "ACTIVE",
        "phone": "(242) 364-9851",
        "emergency_contact_name": "Derek Clarke",
        "emergency_contact_phone": "(242) 361-2234",
        "is_active": True,
    },

    # ========================================================================
    # RECORDS - Administrative Staff
    # ========================================================================
    {
        "id": STAFF_IDS["p.seymour"],
        "user_id": USER_IDS["p.seymour"],
        "employee_number": "EMP-00601",
        "first_name": "Patrice",
        "last_name": "Seymour",
        "rank": "OFFICER",
        "department": "RECORDS",
        "hire_date": date(2021, 2, 15),
        "status": "ACTIVE",
        "phone": "(242) 364-9860",
        "emergency_contact_name": "Anthony Seymour",
        "emergency_contact_phone": "(242) 324-1123",
        "is_active": True,
    },
]

# Training records for staff
STAFF_TRAINING = []
today = date.today()

# Generate training records for each staff member
for staff in STAFF_MEMBERS:
    staff_id = staff["id"]
    hire_date = staff["hire_date"]

    # Orientation (no expiry)
    STAFF_TRAINING.append({
        "id": str(uuid4()),
        "staff_id": staff_id,
        "training_type": "ORIENTATION",
        "training_date": hire_date + timedelta(days=7),
        "expiry_date": None,
        "hours": 40,
        "instructor": "Training Department",
        "certification_number": None,
        "is_current": True,
    })

    # Use of Force (expires annually)
    last_uof = today - timedelta(days=180)  # 6 months ago
    STAFF_TRAINING.append({
        "id": str(uuid4()),
        "staff_id": staff_id,
        "training_type": "USE_OF_FORCE",
        "training_date": last_uof,
        "expiry_date": last_uof + timedelta(days=365),
        "hours": 16,
        "instructor": "Sgt. Marcus Thompson",
        "certification_number": f"UOF-{today.year}-{staff['employee_number'][-3:]}",
        "is_current": True,
    })

    # CPR (expires annually)
    last_cpr = today - timedelta(days=90)  # 3 months ago
    STAFF_TRAINING.append({
        "id": str(uuid4()),
        "staff_id": staff_id,
        "training_type": "CPR",
        "training_date": last_cpr,
        "expiry_date": last_cpr + timedelta(days=365),
        "hours": 8,
        "instructor": "Red Cross Bahamas",
        "certification_number": f"CPR-{today.year}-{staff['employee_number'][-3:]}",
        "is_current": True,
    })

    # First Aid (expires annually)
    STAFF_TRAINING.append({
        "id": str(uuid4()),
        "staff_id": staff_id,
        "training_type": "FIRST_AID",
        "training_date": last_cpr,
        "expiry_date": last_cpr + timedelta(days=365),
        "hours": 8,
        "instructor": "Red Cross Bahamas",
        "certification_number": f"FA-{today.year}-{staff['employee_number'][-3:]}",
        "is_current": True,
    })

    # Security officers get additional training
    if staff["department"] == "SECURITY":
        # Firearms training (quarterly)
        last_firearms = today - timedelta(days=45)
        STAFF_TRAINING.append({
            "id": str(uuid4()),
            "staff_id": staff_id,
            "training_type": "FIREARMS",
            "training_date": last_firearms,
            "expiry_date": last_firearms + timedelta(days=90),
            "hours": 8,
            "instructor": "Royal Bahamas Police Force",
            "certification_number": f"FQR-{today.year}Q4-{staff['employee_number'][-3:]}",
            "is_current": True,
        })

        # Defensive tactics (annual)
        STAFF_TRAINING.append({
            "id": str(uuid4()),
            "staff_id": staff_id,
            "training_type": "DEFENSIVE_TACTICS",
            "training_date": today - timedelta(days=120),
            "expiry_date": today + timedelta(days=245),
            "hours": 16,
            "instructor": "BDCS Training Academy",
            "certification_number": f"DT-{today.year}-{staff['employee_number'][-3:]}",
            "is_current": True,
        })

    # Medical staff get specialized training
    if staff["department"] == "MEDICAL":
        STAFF_TRAINING.append({
            "id": str(uuid4()),
            "staff_id": staff_id,
            "training_type": "MENTAL_HEALTH",
            "training_date": today - timedelta(days=200),
            "expiry_date": today + timedelta(days=165),
            "hours": 24,
            "instructor": "Sandilands Rehabilitation Centre",
            "certification_number": f"MH-{today.year}-{staff['employee_number'][-3:]}",
            "is_current": True,
        })

# Summary statistics
STAFF_STATS = {
    "total_staff": len(STAFF_MEMBERS),
    "by_department": {
        "ADMINISTRATION": len([s for s in STAFF_MEMBERS if s["department"] == "ADMINISTRATION"]),
        "SECURITY": len([s for s in STAFF_MEMBERS if s["department"] == "SECURITY"]),
        "PROGRAMMES": len([s for s in STAFF_MEMBERS if s["department"] == "PROGRAMMES"]),
        "MEDICAL": len([s for s in STAFF_MEMBERS if s["department"] == "MEDICAL"]),
        "RECORDS": len([s for s in STAFF_MEMBERS if s["department"] == "RECORDS"]),
    },
    "by_rank": {
        "SUPERINTENDENT": len([s for s in STAFF_MEMBERS if s["rank"] == "SUPERINTENDENT"]),
        "CHIEF_OFFICER": len([s for s in STAFF_MEMBERS if s["rank"] == "CHIEF_OFFICER"]),
        "SENIOR_OFFICER": len([s for s in STAFF_MEMBERS if s["rank"] == "SENIOR_OFFICER"]),
        "OFFICER": len([s for s in STAFF_MEMBERS if s["rank"] == "OFFICER"]),
    },
    "total_training_records": len(STAFF_TRAINING),
    "active_staff": len([s for s in STAFF_MEMBERS if s["is_active"]]),
}
