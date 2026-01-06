#!/usr/bin/env python3
"""
BDOCS Prison Information System - Seed Data Runner

Session: BD-SEED-01
Purpose: Seed housing units and BTVI programmes

Usage:
    cd bdocs-api
    pipenv run python scripts/seeds/run_seeds.py

Options:
    --housing-only    Seed only housing units
    --programmes-only Seed only programmes
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


async def verify_prerequisites():
    """Verify database connection and schema exists."""
    await init_db()
    from src.database.async_db import async_pg_engine as engine

    async with engine.begin() as conn:
        # Check if required tables exist
        tables_check = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('housing_units', 'programmes')
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

    print("\n=== Verification Complete ===")


async def run_seeds(
    housing_only: bool = False,
    programmes_only: bool = False,
    clear: bool = False,
    verify: bool = False
):
    """Main seed runner."""
    print("=" * 60)
    print("BDOCS Prison Information System - Seed Data Runner")
    print(f"Session: BD-SEED-01")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    if verify:
        await verify_seed_data()
        return True

    # Verify prerequisites
    if not await verify_prerequisites():
        return False

    from src.database.async_db import async_pg_engine as engine

    async with engine.begin() as conn:
        success = True

        if not programmes_only:
            housing_success = await seed_housing_units(conn, clear_existing=clear)
            success = success and housing_success

        if not housing_only:
            programmes_success = await seed_programmes(conn, clear_existing=clear)
            success = success and programmes_success

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
        description="BDOCS Seed Data Runner - Housing Units & Programmes"
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
        clear=args.clear,
        verify=args.verify
    ))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
