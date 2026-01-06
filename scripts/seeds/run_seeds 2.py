#!/usr/bin/env python3
"""
BDOCS Prison Information System - Seed Data Runner

Sessions: BD-SEED-01, BD-SEED-02
Purpose: Seed housing units, BTVI programmes, and system users

Usage:
    cd bdocs-api
    pipenv run python scripts/seeds/run_seeds.py

Options:
    --housing-only    Seed only housing units
    --programmes-only Seed only programmes
    --users-only      Seed only system users
    --clear           Clear existing seed data before seeding
    --verify          Verify seed data without inserting
"""
import asyncio
import sys
import os
import argparse
import json
from datetime import datetime, timezone

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.database.async_db import init_db, async_pg_engine

# Import seed data
from scripts.seeds.housing_units import HOUSING_UNITS, HOUSING_STATS
from scripts.seeds.btvi_programmes import ALL_PROGRAMMES, PROGRAMME_STATS
from scripts.seeds.users import SYSTEM_USERS, USER_STATS, DEFAULT_PASSWORD

# Import reference data (not stored in database, used for lookups)
from scripts.seeds.courts import BAHAMAS_COURTS, COURT_STATS
from scripts.seeds.islands import BAHAMAS_ISLANDS, ISLAND_STATS
from scripts.seeds.agencies import RELATED_AGENCIES, AGENCY_STATS

# Password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("WARNING: bcrypt not installed. Using SHA256 fallback (not recommended for production).")
    import hashlib


def hash_password(password: str) -> str:
    """Hash password using bcrypt (preferred) or SHA256 fallback."""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    else:
        # Fallback - not secure for production!
        return hashlib.sha256(password.encode('utf-8')).hexdigest()


async def verify_prerequisites():
    """Verify database connection and schema exists."""
    await init_db()
    from src.database.async_db import async_pg_engine as engine

    async with engine.begin() as conn:
        # Check if required tables exist
        tables_check = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('housing_units', 'programmes', 'users')
        """))
        tables = [row[0] for row in tables_check.fetchall()]

        if 'housing_units' not in tables:
            print("ERROR: housing_units table does not exist.")
            print("Run: pipenv run alembic upgrade head")
            return False

        if 'programmes' not in tables:
            print("ERROR: programmes table does not exist.")
            print("Run: pipenv run alembic upgrade head")
            return False

        if 'users' not in tables:
            print("ERROR: users table does not exist.")
            print("Create auth module and run migrations.")
            return False

        print("Database prerequisites verified.")
        return True


async def seed_housing_units(conn, clear_existing: bool = False):
    """Seed housing units data."""
    print("\n--- Seeding Housing Units ---")

    if clear_existing:
        print("Clearing existing housing units...")
        await conn.execute(text("DELETE FROM housing_units"))
        print("Existing housing units cleared.")

    # Check existing count
    result = await conn.execute(text("SELECT COUNT(*) FROM housing_units"))
    existing_count = result.scalar()

    if existing_count > 0 and not clear_existing:
        print(f"WARNING: {existing_count} housing units already exist.")
        print("Use --clear to remove existing data first.")
        return False

    now = datetime.now(timezone.utc)
    inserted = 0
    for unit in HOUSING_UNITS:
        try:
            await conn.execute(text("""
                INSERT INTO housing_units (
                    id, code, name, security_level, capacity, current_occupancy,
                    gender_restriction, is_active, is_juvenile, description,
                    inserted_by, inserted_date
                ) VALUES (
                    :id, :code, :name, :security_level, :capacity, :current_occupancy,
                    :gender_restriction, :is_active, :is_juvenile, :description,
                    :inserted_by, :inserted_date
                )
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    security_level = EXCLUDED.security_level,
                    capacity = EXCLUDED.capacity,
                    current_occupancy = EXCLUDED.current_occupancy,
                    gender_restriction = EXCLUDED.gender_restriction,
                    is_active = EXCLUDED.is_active,
                    is_juvenile = EXCLUDED.is_juvenile,
                    description = EXCLUDED.description,
                    updated_by = EXCLUDED.inserted_by,
                    updated_date = EXCLUDED.inserted_date
            """), {
                "id": unit["id"],
                "code": unit["code"],
                "name": unit["name"],
                "security_level": unit["security_level"],
                "capacity": unit["capacity"],
                "current_occupancy": unit["current_occupancy"],
                "gender_restriction": unit.get("gender_restriction"),
                "is_active": unit["is_active"],
                "is_juvenile": unit["is_juvenile"],
                "description": unit.get("description"),
                "inserted_by": "seed_script",
                "inserted_date": now,
            })
            inserted += 1
            print(f"  Seeded: {unit['code']} - {unit['name']}")
        except Exception as e:
            print(f"  ERROR seeding {unit['code']}: {e}")

    print(f"\nHousing Units Summary:")
    print(f"  Total Units: {HOUSING_STATS['total_units']}")
    print(f"  Total Capacity: {HOUSING_STATS['total_capacity']}")
    print(f"  Total Population: {HOUSING_STATS['total_population']}")
    print(f"  Occupancy Rate: {HOUSING_STATS['occupancy_rate']}%")
    print(f"  Units Inserted: {inserted}")

    return inserted == len(HOUSING_UNITS)


async def seed_programmes(conn, clear_existing: bool = False):
    """Seed programmes data."""
    print("\n--- Seeding Programmes ---")

    if clear_existing:
        print("Clearing existing programmes...")
        await conn.execute(text("DELETE FROM programmes"))
        print("Existing programmes cleared.")

    # Check existing count
    result = await conn.execute(text("SELECT COUNT(*) FROM programmes"))
    existing_count = result.scalar()

    if existing_count > 0 and not clear_existing:
        print(f"WARNING: {existing_count} programmes already exist.")
        print("Use --clear to remove existing data first.")
        return False

    now = datetime.now(timezone.utc)
    inserted = 0
    for prog in ALL_PROGRAMMES:
        try:
            await conn.execute(text("""
                INSERT INTO programmes (
                    id, code, name, description, category, provider,
                    duration_weeks, max_participants, eligibility_criteria, is_active,
                    is_deleted, inserted_by, inserted_date
                ) VALUES (
                    :id, :code, :name, :description, :category, :provider,
                    :duration_weeks, :max_participants, :eligibility_criteria, :is_active,
                    :is_deleted, :inserted_by, :inserted_date
                )
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    provider = EXCLUDED.provider,
                    duration_weeks = EXCLUDED.duration_weeks,
                    max_participants = EXCLUDED.max_participants,
                    eligibility_criteria = EXCLUDED.eligibility_criteria,
                    is_active = EXCLUDED.is_active,
                    updated_by = EXCLUDED.inserted_by,
                    updated_date = EXCLUDED.inserted_date
            """), {
                "id": prog["id"],
                "code": prog["code"],
                "name": prog["name"],
                "description": prog.get("description"),
                "category": prog["category"],
                "provider": prog["provider"],
                "duration_weeks": prog["duration_weeks"],
                "max_participants": prog["max_participants"],
                "eligibility_criteria": json.dumps(prog.get("eligibility_criteria", {})),
                "is_active": prog["is_active"],
                "is_deleted": False,
                "inserted_by": "seed_script",
                "inserted_date": now,
            })
            inserted += 1
            btvi_tag = "[BTVI]" if prog.get("eligibility_criteria", {}).get("is_btvi_certified") else "[Internal]"
            print(f"  Seeded: {prog['code']} - {prog['name']} {btvi_tag}")
        except Exception as e:
            print(f"  ERROR seeding {prog['code']}: {e}")

    print(f"\nProgrammes Summary:")
    print(f"  BTVI Programmes: {PROGRAMME_STATS['btvi_programmes']}")
    print(f"  Internal Programmes: {PROGRAMME_STATS['internal_programmes']}")
    print(f"  Total Programmes: {PROGRAMME_STATS['total_programmes']}")
    print(f"  Vocational: {PROGRAMME_STATS['vocational_count']}")
    print(f"  Educational: {PROGRAMME_STATS['educational_count']}")
    print(f"  Therapeutic: {PROGRAMME_STATS['therapeutic_count']}")
    print(f"  Programmes Inserted: {inserted}")

    return inserted == len(ALL_PROGRAMMES)


async def seed_users(conn, clear_existing: bool = False):
    """Seed system users data."""
    print("\n--- Seeding System Users ---")

    if clear_existing:
        print("Clearing existing users...")
        await conn.execute(text("DELETE FROM users"))
        print("Existing users cleared.")

    # Check existing count
    result = await conn.execute(text("SELECT COUNT(*) FROM users"))
    existing_count = result.scalar()

    if existing_count > 0 and not clear_existing:
        print(f"WARNING: {existing_count} users already exist.")
        print("Use --clear to remove existing data first.")
        return False

    now = datetime.now(timezone.utc)
    password_hash = hash_password(DEFAULT_PASSWORD)
    inserted = 0

    for user in SYSTEM_USERS:
        try:
            await conn.execute(text("""
                INSERT INTO users (
                    id, username, email, password_hash, first_name, last_name,
                    role, badge_number, phone, position, assigned_unit, shift,
                    is_active, is_system_account, is_external,
                    must_change_password, failed_login_attempts,
                    is_deleted, inserted_by, inserted_date
                ) VALUES (
                    :id, :username, :email, :password_hash, :first_name, :last_name,
                    :role, :badge_number, :phone, :position, :assigned_unit, :shift,
                    :is_active, :is_system_account, :is_external,
                    :must_change_password, :failed_login_attempts,
                    :is_deleted, :inserted_by, :inserted_date
                )
                ON CONFLICT (username) DO UPDATE SET
                    email = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    role = EXCLUDED.role,
                    badge_number = EXCLUDED.badge_number,
                    phone = EXCLUDED.phone,
                    position = EXCLUDED.position,
                    assigned_unit = EXCLUDED.assigned_unit,
                    shift = EXCLUDED.shift,
                    is_active = EXCLUDED.is_active,
                    is_system_account = EXCLUDED.is_system_account,
                    is_external = EXCLUDED.is_external,
                    updated_by = EXCLUDED.inserted_by,
                    updated_date = EXCLUDED.inserted_date
            """), {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "password_hash": password_hash,
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
                "badge_number": user.get("badge_number"),
                "phone": user.get("phone"),
                "position": user.get("position"),
                "assigned_unit": user.get("assigned_unit"),
                "shift": user.get("shift"),
                "is_active": user["is_active"],
                "is_system_account": user.get("is_system_account", False),
                "is_external": user.get("is_external", False),
                "must_change_password": user.get("must_change_password", True),
                "failed_login_attempts": 0,
                "is_deleted": False,
                "inserted_by": "seed_script",
                "inserted_date": now,
            })
            inserted += 1
            role_tag = f"[{user['role']}]"
            ext_tag = " (external)" if user.get("is_external") else ""
            print(f"  Seeded: {user['username']:15} {role_tag:12} - {user['first_name']} {user['last_name']}{ext_tag}")
        except Exception as e:
            print(f"  ERROR seeding {user['username']}: {e}")

    print(f"\nUsers Summary:")
    print(f"  Total Users: {USER_STATS['total_users']}")
    print(f"  By Role:")
    for role, count in USER_STATS['by_role'].items():
        if count > 0:
            print(f"    {role}: {count}")
    print(f"  Internal: {USER_STATS['internal_users']}")
    print(f"  External: {USER_STATS['external_users']}")
    print(f"  Users Inserted: {inserted}")
    print(f"\n  Default Password: {DEFAULT_PASSWORD}")
    print(f"  (Users with must_change_password=True will be prompted to change)")

    return inserted == len(SYSTEM_USERS)


async def verify_seed_data():
    """Verify seed data without inserting."""
    print("\n=== Seed Data Verification ===\n")

    print("Housing Units:")
    print(f"  Count: {HOUSING_STATS['total_units']}")
    print(f"  Capacity: {HOUSING_STATS['total_capacity']}")
    print(f"  Population: {HOUSING_STATS['total_population']}")
    print(f"  Occupancy: {HOUSING_STATS['occupancy_rate']}%")
    print("\n  Units:")
    for unit in HOUSING_UNITS:
        occ_rate = round(unit["current_occupancy"] / unit["capacity"] * 100, 1)
        status = "OVERCROWDED" if occ_rate > 100 else "OK"
        print(f"    {unit['code']:12} | {unit['security_level']:8} | "
              f"{unit['current_occupancy']:3}/{unit['capacity']:3} ({occ_rate:5.1f}%) | {status}")

    print("\nProgrammes:")
    print(f"  Total: {PROGRAMME_STATS['total_programmes']}")
    print(f"  BTVI Certified: {PROGRAMME_STATS['btvi_programmes']}")
    print(f"  Internal: {PROGRAMME_STATS['internal_programmes']}")
    print("\n  Programmes:")
    for prog in ALL_PROGRAMMES:
        btvi = "BTVI" if prog.get("eligibility_criteria", {}).get("is_btvi_certified") else "INT"
        print(f"    {prog['code']:10} | {prog['category']:12} | {btvi:4} | "
              f"{prog['duration_weeks']:2}wk | {prog['max_participants']:2} cap | {prog['name'][:30]}")

    print("\nSystem Users:")
    print(f"  Total: {USER_STATS['total_users']}")
    print(f"  Internal: {USER_STATS['internal_users']}")
    print(f"  External: {USER_STATS['external_users']}")
    print("\n  Users:")
    for user in SYSTEM_USERS:
        ext = "(ext)" if user.get("is_external") else ""
        unit = user.get("assigned_unit", "-")
        print(f"    {user['username']:15} | {user['role']:12} | {unit:10} | "
              f"{user['first_name']} {user['last_name']} {ext}")

    print("\n=== Verification Complete ===")


async def run_seeds(
    housing_only: bool = False,
    programmes_only: bool = False,
    users_only: bool = False,
    clear: bool = False,
    verify: bool = False
):
    """Main seed runner."""
    print("=" * 60)
    print("BDOCS Prison Information System - Seed Data Runner")
    print(f"Sessions: BD-SEED-01, BD-SEED-02")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    if verify:
        await verify_seed_data()
        return True

    # Verify prerequisites
    if not await verify_prerequisites():
        return False

    from src.database.async_db import async_pg_engine as engine

    # Determine what to seed
    seed_all = not (housing_only or programmes_only or users_only)

    async with engine.begin() as conn:
        success = True

        if seed_all or housing_only:
            housing_success = await seed_housing_units(conn, clear_existing=clear)
            success = success and housing_success

        if seed_all or programmes_only:
            programmes_success = await seed_programmes(conn, clear_existing=clear)
            success = success and programmes_success

        if seed_all or users_only:
            users_success = await seed_users(conn, clear_existing=clear)
            success = success and users_success

        if success:
            print("\n" + "=" * 60)
            print("SEED COMPLETED SUCCESSFULLY")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("SEED COMPLETED WITH WARNINGS")
            print("=" * 60)

        return success


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BDOCS Seed Data Runner - Housing Units, Programmes & Users"
    )
    parser.add_argument(
        "--housing-only",
        action="store_true",
        help="Seed only housing units"
    )
    parser.add_argument(
        "--programmes-only",
        action="store_true",
        help="Seed only programmes"
    )
    parser.add_argument(
        "--users-only",
        action="store_true",
        help="Seed only system users"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing seed data before seeding"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify seed data without inserting"
    )

    args = parser.parse_args()

    success = asyncio.run(run_seeds(
        housing_only=args.housing_only,
        programmes_only=args.programmes_only,
        users_only=args.users_only,
        clear=args.clear,
        verify=args.verify
    ))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
