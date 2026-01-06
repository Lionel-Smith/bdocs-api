"""
BDOCS PIS - Test Inmates Seed Data Generator
Source: BDOCS statistics, authentic Bahamian naming conventions
Session: BD-SEED-04

Generates 100 realistic test inmates with proper demographic distribution:
- 90% male / 10% female (actual: 89.6% / 10.4%)
- 37% remand / 63% sentenced
- 9.3% foreign nationals
- Island distribution matches 2022 Census
"""

import hashlib
import random
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

# Fixed seed for reproducible test data
random.seed(42)


def make_uuid(prefix: str, identifier: str) -> UUID:
    """Generate deterministic UUID from prefix and identifier."""
    return UUID(hashlib.md5(f"bdocs-{prefix}-{identifier}".encode()).hexdigest())


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIC BAHAMIAN NAMES
# Common names from Bahamas census and public records
# ═══════════════════════════════════════════════════════════════════════════════

MALE_FIRST_NAMES = [
    "Trevon", "Jamaal", "Rashad", "Deandre", "Terrance", "Kevin", "Michael",
    "Dario", "Jermaine", "Lamar", "Wendell", "Ricardo", "Brandon", "Dwayne",
    "Marcus", "Jerome", "Tyrone", "Marvin", "Carlos", "Darren", "Shaquille",
    "Kendrick", "Devon", "Jamal", "Tavon", "Quinton", "Lamont", "Dominic",
    "Andre", "Travis", "Demetrius", "Leroy", "Cedric", "Desmond", "Rodney",
    "Garfield", "Wellington", "Franklyn", "Godfrey", "Oswald", "Valentino",
    "Renaldo", "Lavardo", "Drexel", "Anthon", "Kirkland", "Delano", "Vernal",
]

FEMALE_FIRST_NAMES = [
    "Shantell", "Latoya", "Antoinette", "Crystal", "Denise", "Tamika",
    "Keisha", "Monique", "Natasha", "Alicia", "Jasmine", "Tanya",
    "Shenique", "Precious", "Desiree", "Shantel", "Bianca", "Lakisha",
    "Vernita", "Rochelle", "Felicia", "Deidre", "Shenika", "Patrice",
    "Claudette", "Indira", "Shavonne", "Raquel", "Tiffany", "Kendra",
]

BAHAMIAN_SURNAMES = [
    "Rolle", "Ferguson", "Johnson", "Butler", "Smith", "Thompson", "Williams",
    "Davis", "Brown", "Sands", "Dean", "Taylor", "Knowles", "Bastian",
    "Seymour", "Bain", "Clarke", "Russell", "Major", "Moss", "Munroe",
    "McPhee", "Adderley", "Stuart", "Curry", "Forbes", "King", "Evans",
    "Lightbourne", "Strachan", "Gibson", "Hepburn", "Cartwright", "Wells",
    "Bethel", "Mackey", "Symonette", "Ingraham", "Percentie", "Armbrister",
    "Pratt", "Cooper", "Miller", "Minnis", "Turnquest", "Christie", "Pinder",
]

# Foreign national names (Haitian, Jamaican, etc.)
HAITIAN_FIRST_NAMES_MALE = ["Jean", "Pierre", "Jacques", "François", "Michel", "Emmanuel", "Joseph", "Claude"]
HAITIAN_FIRST_NAMES_FEMALE = ["Marie", "Rose", "Francoise", "Claudette", "Mireille", "Nadine"]
HAITIAN_SURNAMES = ["Jean-Baptiste", "Pierre", "Louis", "Joseph", "Charles", "Augustin", "Celestin", "Francois"]

JAMAICAN_FIRST_NAMES_MALE = ["Damion", "Kemar", "Romaine", "Shawn", "Ricardo", "Omar", "Devon", "Marlon"]
JAMAICAN_FIRST_NAMES_FEMALE = ["Shanique", "Keisha", "Tricia", "Shanice", "Nadine", "Claudette"]
JAMAICAN_SURNAMES = ["Brown", "Williams", "Campbell", "Stewart", "Gordon", "Reid", "Morrison", "Clarke"]


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTION WEIGHTS
# Based on BDOCS statistics and 2022 Census
# ═══════════════════════════════════════════════════════════════════════════════

ISLAND_WEIGHTS = {
    "New Providence": 0.745,
    "Grand Bahama": 0.119,
    "Abaco": 0.042,
    "Eleuthera": 0.023,
    "Andros": 0.020,
    "Exuma": 0.018,
    "Long Island": 0.008,
    "Cat Island": 0.004,
    "Bimini": 0.005,
    "San Salvador": 0.002,
    "Inagua": 0.002,
    "Harbour Island": 0.005,
    "Other Family Islands": 0.007,
}

FOREIGN_NATIONALITIES = [
    ("Haitian", 0.60),      # 60% of foreign nationals
    ("Jamaican", 0.20),     # 20%
    ("American", 0.10),     # 10%
    ("Cuban", 0.05),        # 5%
    ("Dominican", 0.05),    # 5%
]

# Housing unit assignment rules
HOUSING_ASSIGNMENTS = {
    "MALE_REMAND": ["REM-1"],
    "MALE_MAXIMUM": ["MAX-A", "MAX-B"],
    "MALE_MEDIUM": ["MED-1", "MED-2"],
    "MALE_MINIMUM": ["MIN-1"],
    "FEMALE_ANY": ["FEM-1"],
    "JUVENILE": ["JUV-1"],
    "MEDICAL": ["MED-H"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_booking_number(year: int, sequence: int) -> str:
    """Generate booking number in BDOCS-YYYY-NNNNN format."""
    return f"BDOCS-{year}-{sequence:05d}"


def generate_age() -> int:
    """Generate realistic age (weighted toward 20-40)."""
    # Age distribution: 18-25 (30%), 26-35 (35%), 36-45 (20%), 46-55 (10%), 56+ (5%)
    ranges = [(18, 25), (26, 35), (36, 45), (46, 55), (56, 65)]
    weights = [30, 35, 20, 10, 5]
    age_range = random.choices(ranges, weights=weights)[0]
    return random.randint(age_range[0], age_range[1])


def generate_dob_from_age(age: int) -> date:
    """Generate date of birth from age, with random day in the year."""
    today = date.today()
    birth_year = today.year - age
    # Random day of year (avoiding Feb 29 issues)
    birth_month = random.randint(1, 12)
    max_day = 28 if birth_month == 2 else 30 if birth_month in [4, 6, 9, 11] else 31
    birth_day = random.randint(1, max_day)
    return date(birth_year, birth_month, birth_day)


def generate_physical_description(is_male: bool) -> dict:
    """Generate realistic physical description."""
    if is_male:
        height = random.randint(165, 195)
        weight = random.randint(65, 110)
    else:
        height = random.randint(155, 180)
        weight = random.randint(50, 90)

    return {
        "height_cm": height,
        "weight_kg": float(weight),
        "eye_color": random.choice(["Brown", "Dark Brown", "Black", "Hazel"]),
        "hair_color": random.choice(["Black", "Dark Brown", "Brown", "Gray"]),
    }


def assign_housing_unit(gender: str, status: str, security_level: str, age: int) -> str:
    """Assign appropriate housing unit based on inmate characteristics."""
    if age < 18:
        return "JUV-1"

    if gender == "FEMALE":
        return "FEM-1"

    if status == "REMAND":
        return "REM-1"

    if security_level == "MAXIMUM":
        return random.choice(["MAX-A", "MAX-B"])
    elif security_level == "MINIMUM":
        return "MIN-1"
    else:
        return random.choice(["MED-1", "MED-2"])


def generate_emergency_contact(last_name: str) -> dict:
    """Generate emergency contact with same or different surname."""
    relationships = ["Mother", "Father", "Wife", "Husband", "Sister", "Brother", "Cousin", "Aunt", "Uncle"]
    relationship = random.choice(relationships)

    # 70% chance same surname (family member)
    if random.random() < 0.7:
        contact_surname = last_name
    else:
        contact_surname = random.choice(BAHAMIAN_SURNAMES)

    # First name based on gender implied by relationship
    if relationship in ["Mother", "Wife", "Sister", "Aunt"]:
        contact_first = random.choice(FEMALE_FIRST_NAMES)
    else:
        contact_first = random.choice(MALE_FIRST_NAMES)

    # Generate Bahamian phone number (242) XXX-XXXX
    phone_prefix = random.choice(["322", "323", "324", "325", "326", "327", "328", "341", "361", "364", "376"])
    phone_suffix = f"{random.randint(1000, 9999)}"

    return {
        "name": f"{contact_first} {contact_surname}",
        "phone": f"(242) {phone_prefix}-{phone_suffix}",
        "relationship": relationship,
    }


def generate_inmate(sequence: int) -> dict:
    """Generate a single realistic inmate record."""

    # Determine gender (89.6% male)
    is_male = random.random() < 0.896
    gender = "MALE" if is_male else "FEMALE"

    # Determine if foreign national (9.3%)
    is_foreign = random.random() < 0.093

    # Generate name based on nationality
    if is_foreign:
        nationality_choice = random.choices(
            [n[0] for n in FOREIGN_NATIONALITIES],
            weights=[n[1] for n in FOREIGN_NATIONALITIES]
        )[0]

        if nationality_choice == "Haitian":
            if is_male:
                first_name = random.choice(HAITIAN_FIRST_NAMES_MALE)
            else:
                first_name = random.choice(HAITIAN_FIRST_NAMES_FEMALE)
            last_name = random.choice(HAITIAN_SURNAMES)
        elif nationality_choice == "Jamaican":
            if is_male:
                first_name = random.choice(JAMAICAN_FIRST_NAMES_MALE)
            else:
                first_name = random.choice(JAMAICAN_FIRST_NAMES_FEMALE)
            last_name = random.choice(JAMAICAN_SURNAMES)
        else:
            # American, Cuban, Dominican - use generic names
            first_name = random.choice(MALE_FIRST_NAMES if is_male else FEMALE_FIRST_NAMES)
            last_name = random.choice(BAHAMIAN_SURNAMES)

        nationality = nationality_choice
        island_of_origin = None  # Foreign nationals have no Bahamian island
    else:
        first_name = random.choice(MALE_FIRST_NAMES if is_male else FEMALE_FIRST_NAMES)
        last_name = random.choice(BAHAMIAN_SURNAMES)
        nationality = "Bahamian"
        island_of_origin = random.choices(
            list(ISLAND_WEIGHTS.keys()),
            weights=list(ISLAND_WEIGHTS.values())
        )[0]

    # Generate age and DOB
    age = generate_age()
    dob = generate_dob_from_age(age)

    # Determine status (37% remand, 63% sentenced)
    is_remand = random.random() < 0.37
    status = "REMAND" if is_remand else "SENTENCED"

    # Security level based on status
    if is_remand:
        # Remand inmates get medium or maximum based on charge severity
        security_level = random.choice(["MEDIUM", "MAXIMUM"])
    else:
        # Sentenced inmates - weighted distribution
        # 30% maximum, 50% medium, 20% minimum
        security_level = random.choices(
            ["MAXIMUM", "MEDIUM", "MINIMUM"],
            weights=[30, 50, 20]
        )[0]

    # Admission date (within last 3 years for variety)
    days_ago = random.randint(30, 1095)
    admission_date = datetime.now() - timedelta(days=days_ago)

    # Housing assignment
    housing_unit = assign_housing_unit(gender, status, security_level, age)

    # Physical description
    physical = generate_physical_description(is_male)

    # Emergency contact (80% have one)
    emergency_contact = None
    if random.random() < 0.80:
        emergency_contact = generate_emergency_contact(last_name)

    # Middle name (30% chance)
    middle_name = None
    if random.random() < 0.30:
        if is_male:
            middle_name = random.choice(MALE_FIRST_NAMES)
        else:
            middle_name = random.choice(FEMALE_FIRST_NAMES)

    # Build inmate record
    inmate = {
        "id": make_uuid("inmate", f"{sequence:05d}"),
        "booking_number": generate_booking_number(admission_date.year, sequence),
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "gender": gender,
        "date_of_birth": dob,
        "nationality": nationality,
        "island_of_origin": island_of_origin,
        "status": status,
        "security_level": security_level,
        "admission_date": admission_date,
        "housing_unit_code": housing_unit,
        "height_cm": physical["height_cm"],
        "weight_kg": physical["weight_kg"],
        "eye_color": physical["eye_color"],
        "hair_color": physical["hair_color"],
        "emergency_contact": emergency_contact,
    }

    return inmate


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_test_inmates(count: int = 100) -> list[dict]:
    """
    Generate a batch of test inmates.

    Args:
        count: Number of inmates to generate

    Returns:
        List of inmate dictionaries
    """
    # Reset seed for reproducibility
    random.seed(42)

    inmates = []
    for i in range(1, count + 1):
        inmates.append(generate_inmate(i))

    return inmates


# Pre-generated for import
TEST_INMATES = generate_test_inmates(100)


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_statistics(inmates: list[dict]) -> dict:
    """Calculate demographic statistics for generated inmates."""
    total = len(inmates)
    if total == 0:
        return {"total": 0}

    male = sum(1 for i in inmates if i["gender"] == "MALE")
    female = sum(1 for i in inmates if i["gender"] == "FEMALE")
    remand = sum(1 for i in inmates if i["status"] == "REMAND")
    sentenced = sum(1 for i in inmates if i["status"] == "SENTENCED")
    foreign = sum(1 for i in inmates if i["nationality"] != "Bahamian")

    by_unit = {}
    for inmate in inmates:
        unit = inmate["housing_unit_code"]
        by_unit[unit] = by_unit.get(unit, 0) + 1

    by_island = {}
    for inmate in inmates:
        island = inmate["island_of_origin"] or "Foreign Born"
        by_island[island] = by_island.get(island, 0) + 1

    by_security = {}
    for inmate in inmates:
        level = inmate["security_level"]
        by_security[level] = by_security.get(level, 0) + 1

    return {
        "total": total,
        "gender": {
            "male": male,
            "female": female,
            "male_pct": f"{(male/total*100):.1f}%",
            "female_pct": f"{(female/total*100):.1f}%",
        },
        "status": {
            "remand": remand,
            "sentenced": sentenced,
            "remand_pct": f"{(remand/total*100):.1f}%",
            "sentenced_pct": f"{(sentenced/total*100):.1f}%",
        },
        "nationality": {
            "bahamian": total - foreign,
            "foreign": foreign,
            "foreign_pct": f"{(foreign/total*100):.1f}%",
        },
        "by_unit": by_unit,
        "by_island": by_island,
        "by_security": by_security,
    }


INMATE_STATS = calculate_statistics(TEST_INMATES)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI PREVIEW
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("BDOCS Test Inmates - Preview")
    print("=" * 70)

    stats = INMATE_STATS
    print(f"\nTotal Inmates: {stats['total']}")
    print(f"\nGender Distribution:")
    print(f"  Male:   {stats['gender']['male']:3} ({stats['gender']['male_pct']})")
    print(f"  Female: {stats['gender']['female']:3} ({stats['gender']['female_pct']})")

    print(f"\nStatus Distribution:")
    print(f"  Remand:    {stats['status']['remand']:3} ({stats['status']['remand_pct']})")
    print(f"  Sentenced: {stats['status']['sentenced']:3} ({stats['status']['sentenced_pct']})")

    print(f"\nNationality:")
    print(f"  Bahamian: {stats['nationality']['bahamian']:3}")
    print(f"  Foreign:  {stats['nationality']['foreign']:3} ({stats['nationality']['foreign_pct']})")

    print(f"\nBy Housing Unit:")
    for unit, count in sorted(stats["by_unit"].items()):
        print(f"  {unit:10}: {count:3}")

    print(f"\nBy Security Level:")
    for level, count in sorted(stats["by_security"].items()):
        print(f"  {level:10}: {count:3}")

    print(f"\nSample Inmates (first 10):")
    print("-" * 70)
    for inmate in TEST_INMATES[:10]:
        island = inmate["island_of_origin"] or "Foreign"
        print(
            f"  {inmate['booking_number']} | {inmate['last_name']:12} | "
            f"{inmate['gender']:6} | {inmate['status']:9} | {inmate['security_level']:7} | "
            f"{island[:15]}"
        )
