"""
BDOCS Seed Data - Sentence Records with Edge Cases

Comprehensive sentence data covering all edge cases:
- Death penalty sentences with execution dates
- Life imprisonment (with and without parole)
- Concurrent vs consecutive sentences
- Suspended sentences with probation
- Time served credits (pretrial detention)
- Sentence appeals and modifications
- Good time credits
- Early release scenarios

Session: BD-SEED-06
"""
from datetime import date, timedelta
import random

# Seed for reproducibility
random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════════
# SENTENCE EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sentence_records():
    """
    Generate sentence records covering all edge cases.
    Links to test_inmates.py data.
    """
    sentences = []

    # Edge Case 1: DEATH ROW SENTENCES
    # Multiple death row inmates with various statuses
    sentences.extend([
        {
            "inmate_id": "test_inmate_001",  # High profile murder case
            "booking_number": "BDOCS-2020-00123",
            "case_number": "SC-CR-2019-00234",
            "offense": "First Degree Murder (Multiple Victims)",
            "statute": "Penal Code Ch. 291 § 3",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Cheryl Grant-Thompson",
            "conviction_date": date(2020, 6, 15),
            "sentence_date": date(2020, 6, 15),
            "sentence_type": "DEATH",
            "sentence_length_years": None,
            "sentence_length_months": None,
            "sentence_length_days": None,
            "execution_scheduled_date": date(2027, 1, 15),  # Future execution
            "execution_stayed": False,
            "appeals_pending": True,
            "appeal_court": "Privy Council",
            "appeal_filed_date": date(2020, 8, 1),
            "clemency_eligible": True,
            "clemency_filed": True,
            "clemency_status": "UNDER_REVIEW",
            "time_served_credit_days": 547,  # Pretrial detention
            "good_time_credit_days": 0,  # Not applicable for death row
            "projected_release_date": None,
            "actual_release_date": None,
            "is_concurrent": False,
            "concurrent_with_case": None,
            "notes": "Awaiting Privy Council appeal decision. High profile case - triple homicide.",
        },
        {
            "inmate_id": "test_inmate_002",
            "booking_number": "BDOCS-2018-00456",
            "case_number": "SC-CR-2017-00891",
            "offense": "Capital Murder (Police Officer)",
            "statute": "Penal Code Ch. 291 § 3(a)",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Ian Winder",
            "conviction_date": date(2018, 3, 22),
            "sentence_date": date(2018, 3, 22),
            "sentence_type": "DEATH",
            "sentence_length_years": None,
            "sentence_length_months": None,
            "sentence_length_days": None,
            "execution_scheduled_date": None,  # Stayed indefinitely
            "execution_stayed": True,
            "stay_reason": "Pending constitutional challenge to death penalty",
            "appeals_pending": True,
            "appeal_court": "Court of Appeal",
            "appeal_filed_date": date(2018, 5, 10),
            "clemency_eligible": True,
            "clemency_filed": False,
            "time_served_credit_days": 892,
            "good_time_credit_days": 0,
            "projected_release_date": None,
            "actual_release_date": None,
            "is_concurrent": False,
            "notes": "Execution stayed pending constitutional challenge. Murder of police officer during armed robbery.",
        },
    ])

    # Edge Case 2: LIFE SENTENCES (various types)
    sentences.extend([
        {
            "inmate_id": "test_inmate_003",
            "booking_number": "BDOCS-2015-00789",
            "case_number": "SC-CR-2014-01234",
            "offense": "Murder",
            "statute": "Penal Code Ch. 291 § 2",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Indra Charles",
            "conviction_date": date(2015, 11, 8),
            "sentence_date": date(2015, 11, 8),
            "sentence_type": "LIFE",
            "sentence_length_years": None,
            "sentence_length_months": None,
            "sentence_length_days": None,
            "minimum_parole_years": 25,  # Eligible for parole after 25 years
            "parole_eligible_date": date(2040, 11, 8),
            "life_without_parole": False,
            "time_served_credit_days": 423,
            "good_time_credit_days": 1825,  # 5 years good time
            "projected_release_date": date(2040, 11, 8),  # Earliest possible
            "actual_release_date": None,
            "is_concurrent": False,
            "notes": "Life with possibility of parole. Model prisoner - extensive good time credits.",
        },
        {
            "inmate_id": "test_inmate_004",
            "booking_number": "BDOCS-2019-01011",
            "case_number": "SC-CR-2018-00567",
            "offense": "Murder (During Commission of Rape)",
            "statute": "Penal Code Ch. 291 § 2, Ch. 99 § 3",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Cheryl Grant-Thompson",
            "conviction_date": date(2019, 4, 17),
            "sentence_date": date(2019, 4, 17),
            "sentence_type": "LIFE",
            "sentence_length_years": None,
            "sentence_length_months": None,
            "sentence_length_days": None,
            "minimum_parole_years": None,
            "parole_eligible_date": None,
            "life_without_parole": True,  # LWOP - never eligible
            "time_served_credit_days": 678,
            "good_time_credit_days": 0,  # Not applicable for LWOP
            "projected_release_date": None,
            "actual_release_date": None,
            "is_concurrent": False,
            "notes": "Life without possibility of parole (LWOP). Heinous crime - rape-murder.",
        },
    ])

    # Edge Case 3: CONCURRENT VS CONSECUTIVE SENTENCES
    sentences.extend([
        {
            "inmate_id": "test_inmate_005",
            "booking_number": "BDOCS-2021-00234",
            "case_number": "SC-CR-2020-00345",
            "offense": "Armed Robbery",
            "statute": "Penal Code Ch. 329 § 1",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Cheryl Grant-Thompson",
            "conviction_date": date(2021, 2, 10),
            "sentence_date": date(2021, 2, 10),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 12,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "time_served_credit_days": 425,
            "good_time_credit_days": 730,  # 2 years
            "is_concurrent": True,
            "concurrent_with_case": "SC-CR-2020-00346",  # Runs concurrently
            "projected_release_date": date(2031, 2, 10),
            "actual_release_date": None,
            "notes": "12 years concurrent with weapons possession charge. Total effective: 12 years.",
        },
        {
            "inmate_id": "test_inmate_005",  # Same inmate
            "booking_number": "BDOCS-2021-00234",
            "case_number": "SC-CR-2020-00346",
            "offense": "Possession of Unlicensed Firearm",
            "statute": "Firearms Act Ch. 213 § 29",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Cheryl Grant-Thompson",
            "conviction_date": date(2021, 2, 10),
            "sentence_date": date(2021, 2, 10),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 5,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "time_served_credit_days": 425,
            "good_time_credit_days": 730,
            "is_concurrent": True,
            "concurrent_with_case": "SC-CR-2020-00345",  # Runs concurrently
            "projected_release_date": date(2031, 2, 10),  # Same as primary
            "actual_release_date": None,
            "notes": "5 years concurrent with armed robbery. Runs at same time.",
        },
        {
            "inmate_id": "test_inmate_006",
            "booking_number": "BDOCS-2022-00567",
            "case_number": "SC-CR-2021-00789",
            "offense": "Drug Trafficking (Cocaine)",
            "statute": "Dangerous Drugs Act Ch. 228 § 29(1)(a)",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Indra Charles",
            "conviction_date": date(2022, 7, 14),
            "sentence_date": date(2022, 7, 14),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 15,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "time_served_credit_days": 298,
            "good_time_credit_days": 0,  # Lost for misconduct
            "is_concurrent": False,
            "consecutive_with_case": "SC-CR-2021-00790",  # CONSECUTIVE
            "projected_release_date": date(2042, 7, 14),  # 15 + 5 = 20 years total
            "actual_release_date": None,
            "notes": "15 years CONSECUTIVE with money laundering. Total: 20 years effective.",
        },
        {
            "inmate_id": "test_inmate_006",  # Same inmate
            "booking_number": "BDOCS-2022-00567",
            "case_number": "SC-CR-2021-00790",
            "offense": "Money Laundering",
            "statute": "Proceeds of Crime Act Ch. 93A § 48",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Indra Charles",
            "conviction_date": date(2022, 7, 14),
            "sentence_date": date(2022, 7, 14),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 5,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "time_served_credit_days": 298,
            "good_time_credit_days": 0,
            "is_concurrent": False,
            "consecutive_with_case": "SC-CR-2021-00789",  # CONSECUTIVE
            "projected_release_date": date(2042, 7, 14),  # After first sentence
            "actual_release_date": None,
            "notes": "5 years CONSECUTIVE to drug trafficking. Must serve both fully.",
        },
    ])

    # Edge Case 4: SUSPENDED SENTENCES
    sentences.extend([
        {
            "inmate_id": "test_inmate_007",
            "booking_number": "BDOCS-2023-00123",
            "case_number": "MC-CR-2023-01234",
            "offense": "Assault Causing Harm",
            "statute": "Penal Code Ch. 84 § 29",
            "court": "Magistrate's Court - New Providence",
            "judge": "Magistrate Derence Rolle-Davis",
            "conviction_date": date(2023, 3, 15),
            "sentence_date": date(2023, 3, 15),
            "sentence_type": "SUSPENDED",
            "sentence_length_years": 2,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "suspension_period_years": 3,  # Suspended for 3 years
            "suspension_end_date": date(2026, 3, 15),
            "probation_officer": "Officer Marcus Thompson",
            "probation_conditions": [
                "Report to probation officer monthly",
                "Complete anger management programme",
                "No contact with victim",
                "Maintain employment",
                "No alcohol consumption",
            ],
            "suspension_violated": False,
            "time_served_credit_days": 89,  # Remand time
            "projected_release_date": date(2023, 3, 15),  # Already released on probation
            "actual_release_date": date(2023, 3, 15),
            "notes": "2 years suspended for 3 years. Released on strict probation conditions.",
        },
        {
            "inmate_id": "test_inmate_008",
            "booking_number": "BDOCS-2021-00891",
            "case_number": "MC-CR-2021-05678",
            "offense": "Theft",
            "statute": "Penal Code Ch. 84 § 378",
            "court": "Magistrate's Court - New Providence",
            "judge": "Magistrate Kendra Kelly",
            "conviction_date": date(2021, 6, 22),
            "sentence_date": date(2021, 6, 22),
            "sentence_type": "SUSPENDED",
            "sentence_length_years": 1,
            "sentence_length_months": 6,
            "sentence_length_days": 0,
            "suspension_period_years": 2,
            "suspension_end_date": date(2023, 6, 22),
            "probation_officer": "Officer Natasha McPhee",
            "probation_conditions": [
                "Weekly probation meetings",
                "Restitution to victim ($5,000)",
                "Community service (200 hours)",
            ],
            "suspension_violated": True,  # VIOLATED
            "violation_date": date(2022, 11, 10),
            "violation_reason": "Failed to complete community service, new arrest",
            "time_served_credit_days": 45,
            "projected_release_date": date(2024, 5, 22),  # Now serving full term
            "actual_release_date": None,
            "notes": "Suspended sentence ACTIVATED due to probation violation. Now serving 18 months.",
        },
    ])

    # Edge Case 5: SENTENCE MODIFICATIONS & APPEALS
    sentences.extend([
        {
            "inmate_id": "test_inmate_009",
            "booking_number": "BDOCS-2020-01234",
            "case_number": "SC-CR-2019-02345",
            "offense": "Rape",
            "statute": "Sexual Offences Act Ch. 99 § 3",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Ian Winder",
            "conviction_date": date(2020, 9, 18),
            "sentence_date": date(2020, 9, 18),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 20,  # ORIGINAL
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "modified_sentence": True,
            "modification_date": date(2023, 4, 12),
            "modification_court": "Court of Appeal",
            "modified_years": 12,  # REDUCED to 12 years
            "modified_months": 0,
            "modified_days": 0,
            "modification_reason": "Appeal successful - excessive sentence for circumstances",
            "time_served_credit_days": 1247,
            "good_time_credit_days": 1095,  # 3 years
            "projected_release_date": date(2029, 9, 18),  # Recalculated
            "actual_release_date": None,
            "notes": "Sentence reduced from 20 to 12 years on appeal. Sentence deemed manifestly excessive.",
        },
        {
            "inmate_id": "test_inmate_010",
            "booking_number": "BDOCS-2019-05678",
            "case_number": "SC-CR-2018-06789",
            "offense": "Manslaughter",
            "statute": "Penal Code Ch. 291 § 292",
            "court": "Supreme Court of The Bahamas",
            "judge": "Hon. Justice Cheryl Grant-Thompson",
            "conviction_date": date(2019, 5, 23),
            "sentence_date": date(2019, 5, 23),
            "sentence_type": "IMPRISONMENT",
            "sentence_length_years": 15,
            "sentence_length_months": 0,
            "sentence_length_days": 0,
            "appeals_pending": True,
            "appeal_court": "Privy Council",
            "appeal_filed_date": date(2024, 1, 15),
            "appeal_grounds": "Conviction unsafe - new evidence discovered",
            "appeal_status": "PENDING_HEARING",
            "time_served_credit_days": 534,
            "good_time_credit_days": 1460,  # 4 years
            "projected_release_date": date(2030, 5, 23),
            "actual_release_date": None,
            "notes": "Final appeal to Privy Council pending. New DNA evidence may exonerate.",
        },
    ])

    return sentences


# Summary statistics
SENTENCE_STATS = {
    "total_sentences": "Generated dynamically",
    "death_row": 2,
    "life_sentences": 2,
    "life_without_parole": 1,
    "concurrent_sentences": 2,
    "consecutive_sentences": 2,
    "suspended_sentences": 2,
    "suspended_activated": 1,
    "modified_sentences": 1,
    "appeals_pending": 3,
}
