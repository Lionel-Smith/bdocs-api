"""
BDOCS Seed Data - BTVI Programmes & Internal Rehabilitation

Bahamas Technical and Vocational Institute (BTVI) certified programmes
and internal BDOCS rehabilitation programmes.

Source: BDOCS_QUICK_REFERENCE.md, BTVI Course Catalog

Programme Model Fields:
- code: Programme code (e.g., BTVI-AM)
- name: Programme name
- description: Detailed description
- category: EDUCATIONAL | VOCATIONAL | THERAPEUTIC | RELIGIOUS | LIFE_SKILLS
- provider: Provider organization name
- duration_weeks: Programme length
- max_participants: Max enrollment per cohort
- eligibility_criteria: JSONB with flexible rules (BTVI-specific fields here)
- is_active: Currently accepting enrollments
"""
from uuid import uuid4

# Fixed UUIDs for referential integrity
PROGRAMME_IDS = {
    # BTVI Vocational Programmes
    "BTVI-AM": "b1000001-0001-4000-8000-000000000001",
    "BTVI-BB": "b1000001-0001-4000-8000-000000000002",
    "BTVI-BC": "b1000001-0001-4000-8000-000000000003",
    "BTVI-BM": "b1000001-0001-4000-8000-000000000004",
    "BTVI-BE": "b1000001-0001-4000-8000-000000000005",
    "BTVI-BP": "b1000001-0001-4000-8000-000000000006",
    "BTVI-GM": "b1000001-0001-4000-8000-000000000007",
    "BTVI-IT": "b1000001-0001-4000-8000-000000000008",
    "BTVI-HD": "b1000001-0001-4000-8000-000000000009",
    # Internal Programmes
    "CBT-ANG": "c1000001-0001-4000-8000-000000000010",
    "CBT-SUB": "c1000001-0001-4000-8000-000000000011",
    "EDU-GED": "e1000001-0001-4000-8000-000000000012",
    "EDU-LIT": "e1000001-0001-4000-8000-000000000013",
}


# ============================================================================
# BTVI CERTIFIED VOCATIONAL PROGRAMMES
# ============================================================================
BTVI_PROGRAMMES = [
    {
        "id": PROGRAMME_IDS["BTVI-AM"],
        "code": "BTVI-AM",
        "name": "Auto Mechanics",
        "description": (
            "Automotive repair and maintenance training including engine diagnostics, "
            "brake systems, and electrical systems. BTVI certified programme with "
            "industry-recognized credentials. Prepares inmates for employment in "
            "automotive repair shops and dealerships."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 15,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "AM-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic literacy", "Physical fitness for shop work"],
            "equipment_required": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-BB"],
        "code": "BTVI-BB",
        "name": "Barbering",
        "description": (
            "Professional barbering skills including hair cutting, styling, and "
            "shop management. BTVI certified programme leading to professional "
            "barber license eligibility upon release. Includes sanitation, "
            "customer service, and business fundamentals."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 12,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "BB-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic literacy"],
            "provides_prison_service": True,  # Can provide services within prison
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-BC"],
        "code": "BTVI-BC",
        "name": "Basic Carpentry",
        "description": (
            "Fundamental woodworking and construction carpentry skills. "
            "Covers framing, finishing, cabinet making basics, and tool safety. "
            "BTVI certified programme preparing inmates for construction industry "
            "employment."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 15,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "BC-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic math", "Physical fitness"],
            "equipment_required": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-BM"],
        "code": "BTVI-BM",
        "name": "Basic Masonry",
        "description": (
            "Block laying, concrete work, and basic masonry construction. "
            "Covers foundation work, block walls, stucco application, and safety. "
            "BTVI certified programme with high demand in Bahamian construction industry."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 15,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "BM-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic math", "Physical fitness for heavy work"],
            "equipment_required": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-BE"],
        "code": "BTVI-BE",
        "name": "Basic Electrical Installation",
        "description": (
            "Residential electrical wiring, safety codes, and installation procedures. "
            "Covers Bahamian electrical code compliance, circuit design, and "
            "troubleshooting. BTVI certified programme for licensed electrician pathway."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 12,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "BE-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic math", "Basic literacy", "No violent offenses"],
            "equipment_required": True,
            "background_restrictions": ["No arson convictions"],
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-BP"],
        "code": "BTVI-BP",
        "name": "Basic Plumbing",
        "description": (
            "Pipe fitting, fixture installation, and basic plumbing repair. "
            "Covers water supply systems, drainage, and code compliance. "
            "BTVI certified programme for plumbing apprenticeship pathway."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 12,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "BP-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic math", "Physical fitness"],
            "equipment_required": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-GM"],
        "code": "BTVI-GM",
        "name": "Garment Manufacturing",
        "description": (
            "Sewing, pattern making, and garment construction skills. "
            "Industrial sewing machine operation, quality control, and "
            "production techniques. BTVI certified programme suitable for "
            "both male and female inmates."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 20,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "GM-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic literacy"],
            "gender_inclusive": True,  # Open to all genders
            "provides_prison_service": True,  # Prison uniform repair
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-IT"],
        "code": "BTVI-IT",
        "name": "Information Technology",
        "description": (
            "Computer basics, Microsoft Office, and introduction to networking. "
            "Digital literacy, internet safety, and basic troubleshooting. "
            "BTVI certified programme essential for modern employment."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 20,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "IT-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic literacy", "Basic math"],
            "special_restrictions": [
                "No computer/cyber crime convictions",
                "No fraud convictions",
            ],
            "supervised_internet_access": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["BTVI-HD"],
        "code": "BTVI-HD",
        "name": "Hair Dressing",
        "description": (
            "Cosmetology skills including hair styling, coloring, and salon management. "
            "Covers hair treatments, customer service, and business basics. "
            "BTVI certified programme for professional cosmetology license pathway."
        ),
        "category": "VOCATIONAL",
        "provider": "Bahamas Technical and Vocational Institute (BTVI)",
        "duration_weeks": 10,
        "max_participants": 12,
        "eligibility_criteria": {
            "is_btvi_certified": True,
            "btvi_course_code": "HD-101",
            "work_experience_weeks": 12,
            "security_levels": ["MINIMUM", "MEDIUM"],
            "min_sentence_remaining_months": 6,
            "prerequisites": ["Basic literacy"],
            "gender_inclusive": True,
            "provides_prison_service": True,
        },
        "is_active": True,
    },
]


# ============================================================================
# INTERNAL REHABILITATION PROGRAMMES
# ============================================================================
INTERNAL_PROGRAMMES = [
    {
        "id": PROGRAMME_IDS["CBT-ANG"],
        "code": "CBT-ANG",
        "name": "Anger Management (CBT)",
        "description": (
            "Cognitive Behavioral Therapy for anger management and conflict resolution. "
            "Evidence-based programme addressing triggers, coping strategies, and "
            "behavioral change. Required for many inmates prior to minimum security "
            "reclassification or work release consideration."
        ),
        "category": "THERAPEUTIC",
        "provider": "BDOCS Rehabilitation Services",
        "duration_weeks": 8,
        "max_participants": 15,
        "eligibility_criteria": {
            "is_btvi_certified": False,
            "work_experience_weeks": 0,
            "security_levels": ["MAXIMUM", "MEDIUM", "MINIMUM"],
            "min_sentence_remaining_months": 2,
            "prerequisites": ["Basic literacy"],
            "mandatory_for": ["Assault convictions", "Violent offenders"],
            "facilitator_type": "Licensed counselor or psychologist",
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["CBT-SUB"],
        "code": "CBT-SUB",
        "name": "Substance Abuse Recovery",
        "description": (
            "Substance abuse counseling and recovery support programme. "
            "Covers addiction science, 12-step principles, relapse prevention, "
            "and peer support development. Integration with community AA/NA "
            "meetings for continuity upon release."
        ),
        "category": "THERAPEUTIC",
        "provider": "BDOCS Rehabilitation Services",
        "duration_weeks": 12,
        "max_participants": 12,
        "eligibility_criteria": {
            "is_btvi_certified": False,
            "work_experience_weeks": 0,
            "security_levels": ["MAXIMUM", "MEDIUM", "MINIMUM"],
            "min_sentence_remaining_months": 3,
            "prerequisites": ["Acknowledgment of substance use issue"],
            "mandatory_for": ["Drug convictions", "DUI convictions"],
            "facilitator_type": "Certified addiction counselor",
            "external_partnerships": ["Alcoholics Anonymous", "Narcotics Anonymous"],
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["EDU-GED"],
        "code": "EDU-GED",
        "name": "GED Preparation",
        "description": (
            "High school equivalency diploma (GED) preparation programme. "
            "Covers mathematics, language arts, social studies, and science. "
            "Testing administered in partnership with Ministry of Education. "
            "Completion significantly improves employment prospects."
        ),
        "category": "EDUCATIONAL",
        "provider": "BDOCS Education Department",
        "duration_weeks": 16,
        "max_participants": 20,
        "eligibility_criteria": {
            "is_btvi_certified": False,
            "work_experience_weeks": 0,
            "security_levels": ["MAXIMUM", "MEDIUM", "MINIMUM"],
            "min_sentence_remaining_months": 4,
            "prerequisites": ["Basic literacy (Grade 6 reading level)"],
            "external_partnerships": ["Ministry of Education"],
            "examination_available": True,
        },
        "is_active": True,
    },
    {
        "id": PROGRAMME_IDS["EDU-LIT"],
        "code": "EDU-LIT",
        "name": "Adult Literacy",
        "description": (
            "Basic reading and writing skills for adult learners. "
            "Covers phonics, reading comprehension, basic writing, and "
            "functional literacy for daily life. Prerequisite pathway for "
            "GED and vocational programmes."
        ),
        "category": "EDUCATIONAL",
        "provider": "BDOCS Education Department",
        "duration_weeks": 12,
        "max_participants": 15,
        "eligibility_criteria": {
            "is_btvi_certified": False,
            "work_experience_weeks": 0,
            "security_levels": ["MAXIMUM", "MEDIUM", "MINIMUM"],
            "min_sentence_remaining_months": 3,
            "prerequisites": [],  # No prerequisites - foundational programme
            "assessment_required": True,  # Literacy assessment on intake
            "individualized_instruction": True,
        },
        "is_active": True,
    },
]

# Combined list for seeding
ALL_PROGRAMMES = BTVI_PROGRAMMES + INTERNAL_PROGRAMMES

# Summary statistics for verification
PROGRAMME_STATS = {
    "btvi_programmes": len(BTVI_PROGRAMMES),
    "internal_programmes": len(INTERNAL_PROGRAMMES),
    "total_programmes": len(ALL_PROGRAMMES),
    "total_capacity": sum(p["max_participants"] for p in ALL_PROGRAMMES),
    "vocational_count": len([p for p in ALL_PROGRAMMES if p["category"] == "VOCATIONAL"]),
    "educational_count": len([p for p in ALL_PROGRAMMES if p["category"] == "EDUCATIONAL"]),
    "therapeutic_count": len([p for p in ALL_PROGRAMMES if p["category"] == "THERAPEUTIC"]),
}

# 9 BTVI programmes, 4 internal programmes = 13 total
