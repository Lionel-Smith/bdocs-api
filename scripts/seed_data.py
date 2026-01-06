#!/usr/bin/env python3
"""Seed script for BDOCS Prison Information System"""
import asyncio
import sys
import os
from datetime import date, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.database.async_db import init_db, async_pg_engine


async def seed_database():
    """Seed the database with sample data"""
    await init_db()

    # Re-import after init to get the initialized engine
    from src.database.async_db import async_pg_engine as engine

    async with engine.begin() as conn:
        # Check if data exists
        result = await conn.execute(text("SELECT COUNT(*) FROM inmates"))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} inmates. Skipping seed.")
            return

        print("Seeding database...")

        # Create housing units first
        housing_units = [
            (uuid4(), 'BLOCK-A', 'Maximum Security Block A', 'MAXIMUM', 50),
            (uuid4(), 'BLOCK-B', 'Medium Security Block B', 'MEDIUM', 100),
            (uuid4(), 'BLOCK-C', 'Minimum Security Block C', 'MINIMUM', 75),
            (uuid4(), 'REMAND-1', 'Remand Unit 1', 'MEDIUM', 40),
        ]

        for hu in housing_units:
            await conn.execute(text("""
                INSERT INTO housing_units (id, code, name, security_level, capacity)
                VALUES (:id, :code, :name, :level, :capacity)
                ON CONFLICT DO NOTHING
            """), {"id": str(hu[0]), "code": hu[1], "name": hu[2], "level": hu[3], "capacity": hu[4]})

        # Create inmates
        inmates = [
            {
                "id": uuid4(),
                "booking_number": "BK-2024-0001",
                "nib_number": "NIB-123456",
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": date(1985, 3, 15),
                "gender": "MALE",
                "nationality": "Bahamian",
                "status": "SENTENCED",
                "security_level": "MEDIUM",
                "admission_date": date(2022, 6, 1),
            },
            {
                "id": uuid4(),
                "booking_number": "BK-2024-0002",
                "nib_number": "NIB-234567",
                "first_name": "Michael",
                "last_name": "Johnson",
                "date_of_birth": date(1990, 7, 22),
                "gender": "MALE",
                "nationality": "Bahamian",
                "status": "SENTENCED",
                "security_level": "MAXIMUM",
                "admission_date": date(2020, 1, 15),
            },
            {
                "id": uuid4(),
                "booking_number": "BK-2024-0003",
                "nib_number": "NIB-345678",
                "first_name": "David",
                "last_name": "Williams",
                "date_of_birth": date(1978, 11, 8),
                "gender": "MALE",
                "nationality": "Bahamian",
                "status": "SENTENCED",
                "security_level": "MINIMUM",
                "admission_date": date(2023, 3, 10),
            },
            {
                "id": uuid4(),
                "booking_number": "BK-2024-0004",
                "nib_number": "NIB-456789",
                "first_name": "Robert",
                "last_name": "Brown",
                "date_of_birth": date(1982, 5, 30),
                "gender": "MALE",
                "nationality": "Bahamian",
                "status": "REMAND",
                "security_level": "MEDIUM",
                "admission_date": date(2024, 11, 1),
            },
            {
                "id": uuid4(),
                "booking_number": "BK-2024-0005",
                "nib_number": "NIB-567890",
                "first_name": "James",
                "last_name": "Davis",
                "date_of_birth": date(1995, 9, 12),
                "gender": "MALE",
                "nationality": "Bahamian",
                "status": "SENTENCED",
                "security_level": "MEDIUM",
                "admission_date": date(2021, 8, 20),
            },
        ]

        for inmate in inmates:
            await conn.execute(text("""
                INSERT INTO inmates (id, booking_number, nib_number, first_name, last_name,
                    date_of_birth, gender, nationality, status, security_level, admission_date)
                VALUES (:id, :booking_number, :nib_number, :first_name, :last_name,
                    :date_of_birth, :gender, :nationality, :status, :security_level, :admission_date)
            """), {
                "id": str(inmate["id"]),
                "booking_number": inmate["booking_number"],
                "nib_number": inmate["nib_number"],
                "first_name": inmate["first_name"],
                "last_name": inmate["last_name"],
                "date_of_birth": inmate["date_of_birth"],
                "gender": inmate["gender"],
                "nationality": inmate["nationality"],
                "status": inmate["status"],
                "security_level": inmate["security_level"],
                "admission_date": inmate["admission_date"],
            })

        print(f"Created {len(inmates)} inmates")

        # Create court cases for each convicted inmate
        court_cases = []
        for inmate in inmates:
            if inmate["status"] == "SENTENCED":
                case = {
                    "id": uuid4(),
                    "inmate_id": inmate["id"],
                    "case_number": f"CR-{inmate['admission_date'].year}-{str(inmate['id'])[:4].upper()}",
                    "court_name": "Supreme Court of The Bahamas",
                    "offense_description": "Offense as per court records",
                    "offense_date": inmate["admission_date"] - timedelta(days=90),
                    "arrest_date": inmate["admission_date"] - timedelta(days=60),
                    "case_status": "CLOSED",
                }
                court_cases.append(case)

                await conn.execute(text("""
                    INSERT INTO court_cases (id, inmate_id, case_number, court_name,
                        offense_description, offense_date, arrest_date, case_status)
                    VALUES (:id, :inmate_id, :case_number, :court_name,
                        :offense_description, :offense_date, :arrest_date, :case_status)
                """), {
                    "id": str(case["id"]),
                    "inmate_id": str(case["inmate_id"]),
                    "case_number": case["case_number"],
                    "court_name": case["court_name"],
                    "offense_description": case["offense_description"],
                    "offense_date": case["offense_date"],
                    "arrest_date": case["arrest_date"],
                    "case_status": case["case_status"],
                })

        print(f"Created {len(court_cases)} court cases")

        # Create sentences
        sentences = []
        sentence_configs = [
            {"term_months": 120, "type": "IMPRISONMENT"},  # John Smith - 10 years
            {"term_months": None, "type": "LIFE", "life": True},  # Michael Johnson - Life
            {"term_months": 36, "type": "IMPRISONMENT"},  # David Williams - 3 years
            {"term_months": 60, "type": "IMPRISONMENT"},  # James Davis - 5 years
        ]

        for i, case in enumerate(court_cases):
            config = sentence_configs[i] if i < len(sentence_configs) else {"term_months": 24, "type": "IMPRISONMENT"}
            inmate = next(im for im in inmates if im["id"] == case["inmate_id"])

            sentence = {
                "id": uuid4(),
                "inmate_id": case["inmate_id"],
                "court_case_id": case["id"],
                "sentence_date": inmate["admission_date"],
                "sentence_type": config["type"],
                "original_term_months": config.get("term_months"),
                "life_sentence": config.get("life", False),
                "start_date": inmate["admission_date"],
                "expected_release_date": None if config.get("life") else inmate["admission_date"] + timedelta(days=config.get("term_months", 24) * 30),
                "sentencing_judge": "Hon. Justice Thompson",
            }
            sentences.append(sentence)

            await conn.execute(text("""
                INSERT INTO sentences (id, inmate_id, court_case_id, sentence_date, sentence_type,
                    original_term_months, life_sentence, start_date, expected_release_date, sentencing_judge)
                VALUES (:id, :inmate_id, :court_case_id, :sentence_date, :sentence_type,
                    :original_term_months, :life_sentence, :start_date, :expected_release_date, :sentencing_judge)
            """), {
                "id": str(sentence["id"]),
                "inmate_id": str(sentence["inmate_id"]),
                "court_case_id": str(sentence["court_case_id"]),
                "sentence_date": sentence["sentence_date"],
                "sentence_type": sentence["sentence_type"],
                "original_term_months": sentence["original_term_months"],
                "life_sentence": sentence["life_sentence"],
                "start_date": sentence["start_date"],
                "expected_release_date": sentence["expected_release_date"],
                "sentencing_judge": sentence["sentencing_judge"],
            })

        print(f"Created {len(sentences)} sentences")

        # Create clemency petitions
        petitions = [
            {
                "id": uuid4(),
                "inmate_id": inmates[0]["id"],  # John Smith
                "sentence_id": sentences[0]["id"],
                "petition_number": "CLEM-2024-001",
                "petition_type": "COMMUTATION",
                "status": "UNDER_REVIEW",
                "filed_date": date(2024, 6, 15),
                "petitioner_name": "Mary Smith",
                "petitioner_relationship": "Wife",
                "grounds_for_clemency": "Exemplary behavior during incarceration, completion of rehabilitation programs, and strong family support system.",
            },
            {
                "id": uuid4(),
                "inmate_id": inmates[1]["id"],  # Michael Johnson (Life sentence)
                "sentence_id": sentences[1]["id"],
                "petition_number": "CLEM-2024-002",
                "petition_type": "PARDON",
                "status": "COMMITTEE_SCHEDULED",
                "filed_date": date(2024, 3, 1),
                "petitioner_name": "Public Defender's Office",
                "petitioner_relationship": "Legal Representative",
                "grounds_for_clemency": "New evidence has come to light questioning the conviction. Request for full review of case.",
                "committee_review_date": date(2025, 2, 15),
            },
            {
                "id": uuid4(),
                "inmate_id": inmates[2]["id"],  # David Williams
                "sentence_id": sentences[2]["id"],
                "petition_number": "CLEM-2024-003",
                "petition_type": "REMISSION",
                "status": "AWAITING_MINISTER",
                "filed_date": date(2024, 1, 10),
                "petitioner_name": "David Williams",
                "petitioner_relationship": "Self",
                "grounds_for_clemency": "Good conduct credits earned, participation in vocational training, first-time offender.",
                "committee_review_date": date(2024, 4, 20),
                "committee_recommendation": "The Committee recommends approval of 90-day sentence reduction based on rehabilitation progress.",
            },
            {
                "id": uuid4(),
                "inmate_id": inmates[4]["id"],  # James Davis
                "sentence_id": sentences[3]["id"],
                "petition_number": "CLEM-2023-015",
                "petition_type": "COMMUTATION",
                "status": "GRANTED",
                "filed_date": date(2023, 8, 5),
                "petitioner_name": "Sarah Davis",
                "petitioner_relationship": "Mother",
                "grounds_for_clemency": "Terminal illness of petitioner, inmate is sole caregiver prospect.",
                "committee_review_date": date(2023, 10, 12),
                "committee_recommendation": "Recommend approval on compassionate grounds.",
                "minister_review_date": date(2023, 11, 5),
                "minister_recommendation": "Concur with committee recommendation.",
                "governor_general_date": date(2023, 12, 1),
                "decision_date": date(2023, 12, 15),
                "decision_notes": "Sentence commuted by 18 months on compassionate grounds.",
                "granted_reduction_days": 540,
            },
            {
                "id": uuid4(),
                "inmate_id": inmates[0]["id"],  # John Smith - second petition
                "sentence_id": sentences[0]["id"],
                "petition_number": "CLEM-2023-008",
                "petition_type": "REMISSION",
                "status": "DENIED",
                "filed_date": date(2023, 4, 20),
                "petitioner_name": "John Smith",
                "petitioner_relationship": "Self",
                "grounds_for_clemency": "Request for early release consideration.",
                "committee_review_date": date(2023, 6, 10),
                "committee_recommendation": "Insufficient time served. Recommend denial.",
                "minister_review_date": date(2023, 7, 1),
                "minister_recommendation": "Agree with committee. Deny petition.",
                "decision_date": date(2023, 7, 15),
                "decision_notes": "Petition denied. Minimum required time not yet served.",
            },
        ]

        for petition in petitions:
            await conn.execute(text("""
                INSERT INTO clemency_petitions (id, inmate_id, sentence_id, petition_number, petition_type,
                    status, filed_date, petitioner_name, petitioner_relationship, grounds_for_clemency,
                    committee_review_date, committee_recommendation, minister_review_date,
                    minister_recommendation, governor_general_date, decision_date, decision_notes, granted_reduction_days)
                VALUES (:id, :inmate_id, :sentence_id, :petition_number, :petition_type,
                    :status, :filed_date, :petitioner_name, :petitioner_relationship, :grounds_for_clemency,
                    :committee_review_date, :committee_recommendation, :minister_review_date,
                    :minister_recommendation, :governor_general_date, :decision_date, :decision_notes, :granted_reduction_days)
            """), {
                "id": str(petition["id"]),
                "inmate_id": str(petition["inmate_id"]),
                "sentence_id": str(petition["sentence_id"]),
                "petition_number": petition["petition_number"],
                "petition_type": petition["petition_type"],
                "status": petition["status"],
                "filed_date": petition["filed_date"],
                "petitioner_name": petition["petitioner_name"],
                "petitioner_relationship": petition["petitioner_relationship"],
                "grounds_for_clemency": petition["grounds_for_clemency"],
                "committee_review_date": petition.get("committee_review_date"),
                "committee_recommendation": petition.get("committee_recommendation"),
                "minister_review_date": petition.get("minister_review_date"),
                "minister_recommendation": petition.get("minister_recommendation"),
                "governor_general_date": petition.get("governor_general_date"),
                "decision_date": petition.get("decision_date"),
                "decision_notes": petition.get("decision_notes"),
                "granted_reduction_days": petition.get("granted_reduction_days"),
            })

        print(f"Created {len(petitions)} clemency petitions")

        print("\nSeed completed successfully!")
        print(f"  - {len(inmates)} inmates")
        print(f"  - {len(court_cases)} court cases")
        print(f"  - {len(sentences)} sentences")
        print(f"  - {len(petitions)} clemency petitions")


if __name__ == "__main__":
    asyncio.run(seed_database())
