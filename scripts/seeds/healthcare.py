"""
BDOCS Seed Data - Healthcare Records with Edge Cases

Comprehensive healthcare data covering critical medical scenarios:
- Sick calls (routine and emergency)
- Chronic conditions (HIV/AIDS, TB, diabetes, hypertension)
- Mental health cases (depression, psychosis, PTSD)
- Medication management (compliance, contraindicated drugs)
- Medical emergencies
- Quarantine/isolation cases
- End-of-life care
- Substance abuse treatment

Session: BD-SEED-08
"""
from datetime import datetime, date, timedelta
import random

# Seed for reproducibility
random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTHCARE EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sick_call_records():
    """Generate sick call records covering routine and emergency cases."""

    sick_calls = []

    # Edge Case 1: EMERGENCY SICK CALLS
    sick_calls.extend([
        {
            "sick_call_id": "SC-2024-00001",
            "inmate_id": "test_inmate_042",
            "booking_number": "BDOCS-2023-00234",
            "request_date": datetime(2024, 1, 15, 2, 30),
            "seen_date": datetime(2024, 1, 15, 2, 35),
            "priority": "EMERGENCY",
            "chief_complaint": "Severe chest pain, difficulty breathing",
            "symptoms": ["Chest pain radiating to left arm", "Shortness of breath", "Sweating", "Nausea"],
            "vital_signs": {
                "blood_pressure": "180/110",
                "heart_rate": 115,
                "respiratory_rate": 24,
                "temperature": 98.4,
                "oxygen_saturation": 89,
            },
            "provider_id": "d1000001-0001-4000-8000-000000000013",  # Dr. Moss
            "diagnosis": "Acute myocardial infarction (suspected)",
            "treatment": "Aspirin 325mg administered, oxygen therapy, emergency transport",
            "disposition": "EMERGENCY_TRANSFER",
            "hospital_name": "Princess Margaret Hospital - Emergency",
            "follow_up_required": True,
            "follow_up_date": date(2024, 1, 20),
            "notes": "CRITICAL - Suspected heart attack. Immediate transport ordered. Code Blue called.",
        },
        {
            "sick_call_id": "SC-2024-00008",
            "inmate_id": "test_inmate_043",
            "booking_number": "BDOCS-2022-00567",
            "request_date": datetime(2024, 1, 22, 16, 45),
            "seen_date": datetime(2024, 1, 22, 16, 47),
            "priority": "EMERGENCY",
            "chief_complaint": "Seizure activity",
            "symptoms": ["Grand mal seizure witnessed", "Post-ictal confusion", "Tongue bitten"],
            "vital_signs": {
                "blood_pressure": "140/90",
                "heart_rate": 98,
                "respiratory_rate": 18,
                "temperature": 99.1,
                "oxygen_saturation": 94,
            },
            "provider_id": "d1000001-0001-4000-8000-000000000014",  # N. Clarke (Nurse)
            "diagnosis": "Seizure disorder - breakthrough seizure",
            "treatment": "Diazepam 10mg IM, airway management, observation",
            "disposition": "OBSERVATION",
            "observation_hours": 24,
            "medications_ordered": ["Phenytoin 300mg daily", "Diazepam PRN"],
            "follow_up_required": True,
            "follow_up_date": date(2024, 1, 23),
            "notes": "Known epileptic. Medication non-compliance suspected. Neuro consult ordered.",
        },
    ])

    # Edge Case 2: CHRONIC CONDITIONS
    sick_calls.extend([
        {
            "sick_call_id": "SC-2024-00015",
            "inmate_id": "test_inmate_044",
            "booking_number": "BDOCS-2021-00891",
            "request_date": datetime(2024, 2, 5, 9, 00),
            "seen_date": datetime(2024, 2, 5, 10, 15),
            "priority": "ROUTINE",
            "chief_complaint": "HIV medication refill",
            "chronic_conditions": ["HIV/AIDS - CD4: 350"],
            "current_medications": [
                "Biktarvy (bictegravir/emtricitabine/tenofovir) 50/200/25mg daily",
                "Trimethoprim-sulfamethoxazole 800/160mg daily (PCP prophylaxis)",
            ],
            "vital_signs": {
                "blood_pressure": "125/80",
                "heart_rate": 72,
                "respiratory_rate": 16,
                "temperature": 98.6,
                "oxygen_saturation": 98,
                "weight": 165,
            },
            "provider_id": "d1000001-0001-4000-8000-000000000013",
            "diagnosis": "HIV infection - stable on ART",
            "treatment": "Medication refill, adherence counseling",
            "lab_work_ordered": ["CD4 count", "Viral load", "Comprehensive metabolic panel"],
            "next_lab_date": date(2024, 3, 5),
            "disposition": "RETURN_TO_HOUSING",
            "follow_up_required": True,
            "follow_up_date": date(2024, 3, 5),
            "confidential": True,  # HIPAA - extra privacy
            "notes": "Excellent medication compliance. Viral load undetectable. Continue current regimen.",
        },
        {
            "sick_call_id": "SC-2024-00017",
            "inmate_id": "test_inmate_045",
            "booking_number": "BDOCS-2020-01234",
            "request_date": datetime(2024, 2, 8, 8, 00),
            "seen_date": datetime(2024, 2, 8, 9, 30),
            "priority": "HIGH",
            "chief_complaint": "Persistent cough, night sweats, weight loss",
            "symptoms": ["Productive cough > 3 weeks", "Hemoptysis", "Night sweats", "15 lb weight loss"],
            "chronic_conditions": [],
            "vital_signs": {
                "blood_pressure": "110/70",
                "heart_rate": 88,
                "respiratory_rate": 20,
                "temperature": 100.8,
                "oxygen_saturation": 93,
                "weight": 145,  # Down from 160
            },
            "provider_id": "d1000001-0001-4000-8000-000000000013",
            "diagnosis": "Pulmonary tuberculosis (suspected)",
            "treatment": "Airborne isolation initiated, sputum samples collected",
            "lab_work_ordered": ["Sputum AFB x3", "Chest X-ray", "PPD test"],
            "disposition": "MEDICAL_ISOLATION",
            "isolation_location": "MED-H Isolation Room 3",
            "isolation_start": date(2024, 2, 8),
            "public_health_notified": True,
            "health_department_case_number": "BS-TB-2024-0012",
            "contact_tracing_initiated": True,
            "follow_up_required": True,
            "follow_up_date": date(2024, 2, 9),
            "notes": "HIGHLY CONTAGIOUS - TB suspected. Airborne precautions. MOH notified.",
        },
    ])

    # Edge Case 3: MENTAL HEALTH CRISES
    sick_calls.extend([
        {
            "sick_call_id": "SC-2024-00020",
            "inmate_id": "test_inmate_046",
            "booking_number": "BDOCS-2023-00567",
            "request_date": datetime(2024, 2, 14, 19, 15),
            "seen_date": datetime(2024, 2, 14, 19, 18),
            "priority": "EMERGENCY",
            "chief_complaint": "Suicidal ideation, auditory hallucinations",
            "symptoms": ["Hears voices commanding self-harm", "Severe depression", "Previous suicide attempt"],
            "mental_health_history": [
                "Schizophrenia - diagnosed 2018",
                "Previous suicide attempt by hanging (2022)",
                "Medication non-compliance",
            ],
            "current_medications": [
                "Risperidone 4mg BID (non-compliant)",
                "Sertraline 100mg daily (non-compliant)",
            ],
            "vital_signs": {
                "blood_pressure": "135/85",
                "heart_rate": 92,
                "respiratory_rate": 18,
                "temperature": 98.6,
            },
            "provider_id": "d1000001-0001-4000-8000-000000000013",
            "psychiatric_consult": True,
            "psychiatrist": "Dr. Jennifer Williams (PMH Psychiatry)",
            "diagnosis": "Acute psychosis with suicidal ideation",
            "treatment": "Suicide watch initiated, medications resumed under direct observation",
            "disposition": "SUICIDE_WATCH",
            "suicide_watch_level": "CONSTANT_OBSERVATION",
            "mental_health_unit": True,
            "medications_ordered": [
                "Risperidone 4mg BID (DOT - Directly Observed Therapy)",
                "Sertraline 100mg daily (DOT)",
                "Lorazepam 1mg PRN for agitation",
            ],
            "follow_up_required": True,
            "follow_up_date": date(2024, 2, 15),  # Daily evaluation
            "notes": "CRITICAL MENTAL HEALTH CRISIS. Constant 1:1 observation. All sharp objects removed.",
        },
    ])

    return sick_calls


def generate_medication_records():
    """Generate medication records with compliance tracking."""

    medications = []

    # Chronic disease medications
    medications.extend([
        {
            "medication_id": "MED-2024-00001",
            "inmate_id": "test_inmate_047",
            "medication_name": "Metformin",
            "dosage": "1000mg",
            "frequency": "BID (twice daily)",
            "route": "PO (oral)",
            "indication": "Type 2 Diabetes Mellitus",
            "prescriber_id": "d1000001-0001-4000-8000-000000000013",
            "start_date": date(2023, 6, 15),
            "end_date": None,  # Ongoing
            "active": True,
            "compliance_rate": 98.5,  # Excellent
            "missed_doses_last_30_days": 1,
            "directly_observed": False,
            "notes": "Well controlled. A1C: 6.2%. Excellent compliance.",
        },
        {
            "medication_id": "MED-2024-00005",
            "inmate_id": "test_inmate_048",
            "medication_name": "Lisinopril",
            "dosage": "20mg",
            "frequency": "Daily",
            "route": "PO",
            "indication": "Hypertension",
            "prescriber_id": "d1000001-0001-4000-8000-000000000013",
            "start_date": date(2022, 3, 10),
            "end_date": None,
            "active": True,
            "compliance_rate": 45.2,  # POOR - non-compliant
            "missed_doses_last_30_days": 18,
            "directly_observed": False,
            "needs_dot": True,  # Should be switched to DOT
            "side_effects_reported": ["Persistent cough"],
            "notes": "POOR COMPLIANCE. BP uncontrolled 160/95. Consider DOT or alternative agent.",
        },
        {
            "medication_id": "MED-2024-00012",
            "inmate_id": "test_inmate_044",  # HIV patient
            "medication_name": "Biktarvy",
            "dosage": "50/200/25mg",
            "frequency": "Daily",
            "route": "PO",
            "indication": "HIV infection",
            "prescriber_id": "d1000001-0001-4000-8000-000000000013",
            "start_date": date(2021, 8, 20),
            "end_date": None,
            "active": True,
            "compliance_rate": 100.0,  # Perfect
            "missed_doses_last_30_days": 0,
            "directly_observed": True,  # All HIV meds are DOT
            "confidential": True,
            "lab_monitoring_required": True,
            "last_lab_date": date(2024, 1, 5),
            "next_lab_date": date(2024, 4, 5),
            "notes": "Perfect compliance. Viral load undetectable. CD4 stable at 450.",
        },
    ])

    # Mental health medications
    medications.extend([
        {
            "medication_id": "MED-2024-00018",
            "inmate_id": "test_inmate_046",  # Schizophrenia patient
            "medication_name": "Risperidone",
            "dosage": "4mg",
            "frequency": "BID",
            "route": "PO",
            "indication": "Schizophrenia",
            "prescriber_id": "Dr. Jennifer Williams (Psychiatry)",
            "start_date": date(2023, 2, 15),
            "end_date": None,
            "active": True,
            "compliance_rate": 35.0,  # VERY POOR
            "missed_doses_last_30_days": 42,
            "directly_observed": True,  # Now DOT after crisis
            "needs_dot": True,
            "side_effects_reported": ["Weight gain", "Drowsiness"],
            "black_box_warning": True,
            "warning_text": "Increased mortality in elderly with dementia-related psychosis",
            "notes": "Recently switched to DOT after suicide attempt. Previous non-compliance.",
        },
    ])

    # Contraindicated medication - SAFETY ALERT
    medications.extend([
        {
            "medication_id": "MED-2024-00025",
            "inmate_id": "test_inmate_049",
            "medication_name": "Warfarin",
            "dosage": "5mg",
            "frequency": "Daily",
            "route": "PO",
            "indication": "Atrial fibrillation",
            "prescriber_id": "d1000001-0001-4000-8000-000000000013",
            "start_date": date(2024, 1, 10),
            "end_date": date(2024, 1, 25),  # DISCONTINUED
            "active": False,
            "discontinued_reason": "Drug interaction - started on contraindicated medication",
            "drug_interaction_alert": {
                "interacting_drug": "Rifampin (for TB treatment)",
                "severity": "MAJOR",
                "effect": "Decreased warfarin efficacy, risk of clotting",
                "action_taken": "Switched to Apixaban (no interaction)",
            },
            "lab_monitoring_required": True,
            "last_inr": 1.8,
            "notes": "DISCONTINUED due to major drug interaction with TB meds. Switched to Apixaban.",
        },
    ])

    return medications


def generate_chronic_condition_records():
    """Generate records for inmates with serious chronic conditions."""

    conditions = []

    conditions.extend([
        {
            "condition_id": "CC-2024-00001",
            "inmate_id": "test_inmate_050",
            "condition": "End-Stage Renal Disease (ESRD)",
            "icd10_code": "N18.6",
            "diagnosis_date": date(2019, 5, 12),
            "severity": "CRITICAL",
            "treatment_plan": "Hemodialysis 3x/week (Mon/Wed/Fri)",
            "dialysis_center": "Princess Margaret Hospital Dialysis Unit",
            "transport_required": True,
            "transport_schedule": ["Monday 6:00 AM", "Wednesday 6:00 AM", "Friday 6:00 AM"],
            "special_diet": "Renal diet - low sodium, low potassium, fluid restriction",
            "fluid_restriction_ml": 1000,
            "managing_physician": "Dr. Patricia Moss + Nephrologist Dr. Robert Smith",
            "prognosis": "Poor - awaiting kidney transplant",
            "transplant_list": True,
            "compassionate_release_eligible": True,
            "notes": "Terminal condition. Requires 3x/week dialysis. High cost of care. Compassionate release petition filed.",
        },
        {
            "condition_id": "CC-2024-00003",
            "inmate_id": "test_inmate_051",
            "condition": "Metastatic Lung Cancer - Stage IV",
            "icd10_code": "C34.90",
            "diagnosis_date": date(2023, 11, 8),
            "severity": "TERMINAL",
            "treatment_plan": "Palliative care only - DNR order in place",
            "prognosis": "Terminal - 3-6 months life expectancy",
            "dnr_order": True,
            "dnr_signed_date": date(2024, 1, 5),
            "pain_management": "Morphine IV PCA, Gabapentin, Acetaminophen",
            "hospice_care": True,
            "family_notification": "Daily updates to family",
            "compassionate_release_eligible": True,
            "compassionate_release_filed": date(2024, 1, 10),
            "end_of_life_planning": True,
            "notes": "TERMINAL. Comfort care only. Family visits daily. Compassionate release approved - awaiting paperwork.",
        },
    ])

    return conditions


# Summary statistics
HEALTHCARE_STATS = {
    "sick_calls": "Generated dynamically",
    "emergency_sick_calls": 3,
    "chronic_conditions": 2,
    "mental_health_cases": 1,
    "tb_cases": 1,
    "hiv_patients": 1,
    "medication_records": "Generated dynamically",
    "dot_medications": 2,
    "terminal_patients": 1,
    "dialysis_patients": 1,
}
