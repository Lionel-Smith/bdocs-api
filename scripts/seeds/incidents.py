"""
BDOCS Seed Data - Incident Records with Edge Cases

Comprehensive incident data covering critical scenarios:
- Inmate-on-inmate assaults (IOI)
- Inmate-on-staff assaults (IOS)
- Contraband discoveries (drugs, weapons, phones)
- Escape attempts
- Medical emergencies
- Deaths in custody
- Self-harm incidents
- Mass disturbances/riots
- Use of force incidents

Session: BD-SEED-07
"""
from datetime import datetime, timedelta
import random

# Seed for reproducibility
random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════════
# INCIDENT EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_incident_records():
    """Generate incident records covering all edge cases."""

    incidents = []

    # Edge Case 1: INMATE-ON-INMATE ASSAULTS (IOI)
    incidents.extend([
        {
            "incident_number": "INC-2024-00001",
            "incident_type": "ASSAULT_IOI",
            "severity": "CRITICAL",
            "location": "MAX-A",
            "date_occurred": datetime(2024, 1, 15, 14, 23),
            "date_reported": datetime(2024, 1, 15, 14, 25),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000003",  # T. Rolle (Supervisor)
            "involved_inmates": ["test_inmate_011", "test_inmate_012"],
            "aggressor": "test_inmate_011",
            "victim": "test_inmate_012",
            "weapon_used": "Shank (improvised weapon)",
            "injuries": "Multiple stab wounds to torso, punctured lung",
            "medical_response": "Emergency transport to Princess Margaret Hospital",
            "hospital_admission": True,
            "hospital_name": "Princess Margaret Hospital",
            "days_hospitalized": 5,
            "use_of_force": True,
            "force_type": "Physical restraint, OC spray",
            "officers_involved": ["d1000001-0001-4000-8000-000000000006"],  # M. Butler
            "witnesses": ["test_inmate_013", "test_inmate_014"],
            "gang_related": True,
            "gang_affiliation": "Bloods vs Crips conflict",
            "charges_filed": True,
            "criminal_charges": "Attempted murder, assault with deadly weapon",
            "disciplinary_action": "30 days segregation, loss of privileges",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Gang retaliation attack. Weapon found hidden in mattress.",
            "corrective_actions": "Enhanced cell searches, segregation of rival gang members",
            "status": "CLOSED",
            "notes": "Most serious assault in 2024. Victim survived but critical injuries. Aggressor charged criminally.",
        },
        {
            "incident_number": "INC-2024-00012",
            "incident_type": "ASSAULT_IOI",
            "severity": "MEDIUM",
            "location": "MED-1",
            "date_occurred": datetime(2024, 2, 8, 19, 45),
            "date_reported": datetime(2024, 2, 8, 19, 47),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000008",  # J. Smith (Officer)
            "involved_inmates": ["test_inmate_015", "test_inmate_016"],
            "aggressor": "test_inmate_015",
            "victim": "test_inmate_016",
            "weapon_used": None,
            "injuries": "Bruised face, split lip",
            "medical_response": "On-site treatment by medical staff",
            "hospital_admission": False,
            "use_of_force": True,
            "force_type": "Physical separation",
            "officers_involved": ["d1000001-0001-4000-8000-000000000008"],
            "witnesses": ["test_inmate_017", "test_inmate_018", "test_inmate_019"],
            "gang_related": False,
            "charges_filed": False,
            "disciplinary_action": "7 days loss of recreation, counseling mandated",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Dispute over TV channel. Both inmates counseled.",
            "status": "CLOSED",
            "notes": "Minor altercation. Resolved with mediation.",
        },
    ])

    # Edge Case 2: INMATE-ON-STAFF ASSAULTS (IOS)
    incidents.extend([
        {
            "incident_number": "INC-2024-00003",
            "incident_type": "ASSAULT_IOS",
            "severity": "CRITICAL",
            "location": "REM-1",
            "date_occurred": datetime(2024, 1, 22, 8, 15),
            "date_reported": datetime(2024, 1, 22, 8, 16),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000005",  # K. Johnson (Supervisor)
            "involved_inmates": ["test_inmate_020"],
            "aggressor": "test_inmate_020",
            "victim_staff_id": "d1000001-0001-4000-8000-000000000009",  # R. Williams (Intake Officer)
            "weapon_used": "Fists",
            "injuries_staff": "Broken nose, concussion, multiple contusions",
            "medical_response": "Emergency transport to Doctor's Hospital",
            "hospital_admission": True,
            "hospital_name": "Doctor's Hospital",
            "days_hospitalized": 2,
            "use_of_force": True,
            "force_type": "Takedown, handcuffs, OC spray",
            "officers_involved": [
                "d1000001-0001-4000-8000-000000000005",
                "d1000001-0001-4000-8000-000000000006",
            ],
            "witnesses": ["test_inmate_021", "test_inmate_022"],
            "charges_filed": True,
            "criminal_charges": "Assault on correctional officer (felony)",
            "disciplinary_action": "90 days segregation, indefinite loss of all privileges",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Unprovoked attack during intake processing. Inmate has history of violence.",
            "corrective_actions": "Enhanced security protocols during intake, victim counseling",
            "workers_comp_filed": True,
            "status": "CLOSED",
            "notes": "Serious assault on staff. Criminal prosecution ongoing. Officer on medical leave.",
        },
    ])

    # Edge Case 3: CONTRABAND DISCOVERIES
    incidents.extend([
        {
            "incident_number": "INC-2024-00005",
            "incident_type": "CONTRABAND",
            "severity": "HIGH",
            "location": "MAX-B",
            "date_occurred": datetime(2024, 1, 28, 6, 30),
            "date_reported": datetime(2024, 1, 28, 6, 35),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000003",
            "involved_inmates": ["test_inmate_023", "test_inmate_024", "test_inmate_025"],
            "contraband_type": "DRUGS",
            "contraband_details": "35 grams marijuana, 12 ecstasy pills, 8 grams cocaine",
            "contraband_value_estimate": 4500.00,
            "discovery_method": "Random cell search",
            "hiding_location": "Inside hollowed-out book, false bottom in shoes",
            "source_suspected": "Visitor - girlfriend of inmate_023",
            "charges_filed": True,
            "criminal_charges": "Possession with intent to distribute in correctional facility",
            "disciplinary_action": "60 days segregation, loss of visitation for 6 months",
            "investigation_status": "ONGOING",
            "investigation_findings": "Large-scale drug operation. Multiple inmates involved. Visitor banned.",
            "corrective_actions": "Enhanced visitor screening, K9 searches increased",
            "status": "OPEN",
            "notes": "Significant drug bust. Investigation ongoing to identify smuggling route.",
        },
        {
            "incident_number": "INC-2024-00018",
            "incident_type": "CONTRABAND",
            "severity": "CRITICAL",
            "location": "MED-2",
            "date_occurred": datetime(2024, 3, 5, 15, 20),
            "date_reported": datetime(2024, 3, 5, 15, 22),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000006",
            "involved_inmates": ["test_inmate_026"],
            "contraband_type": "WEAPON",
            "contraband_details": "Improvised firearm (zip gun), 3 rounds .22 ammunition",
            "discovery_method": "Tip from confidential informant",
            "hiding_location": "Buried in recreation yard",
            "source_suspected": "Unknown - possibly thrown over fence",
            "charges_filed": True,
            "criminal_charges": "Possession of firearm in prison (federal offense)",
            "disciplinary_action": "Indefinite segregation, transfer to supermax pending",
            "investigation_status": "ONGOING",
            "investigation_findings": "Extremely dangerous. FBI and ATF notified.",
            "corrective_actions": "Perimeter security review, yard metal detector sweeps",
            "status": "OPEN",
            "notes": "CRITICAL - firearm in prison. Full lockdown ordered. Federal investigation.",
        },
        {
            "incident_number": "INC-2024-00023",
            "incident_type": "CONTRABAND",
            "severity": "MEDIUM",
            "location": "FEM-1",
            "date_occurred": datetime(2024, 3, 18, 11, 10),
            "date_reported": datetime(2024, 3, 18, 11, 12),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000007",  # A. Dean
            "involved_inmates": ["test_inmate_027"],
            "contraband_type": "PHONE",
            "contraband_details": "Samsung smartphone, charger, SIM card",
            "discovery_method": "Intercepted incoming mail",
            "hiding_location": "Concealed in package labeled 'legal documents'",
            "source_suspected": "Family member",
            "charges_filed": False,
            "disciplinary_action": "30 days loss of phone privileges, 15 days segregation",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Phone smuggling attempt. Family member educated on consequences.",
            "status": "CLOSED",
            "notes": "Cell phone intercepted before delivery. Package sender identified and banned.",
        },
    ])

    # Edge Case 4: ESCAPE ATTEMPTS
    incidents.extend([
        {
            "incident_number": "INC-2024-00007",
            "incident_type": "ESCAPE_ATTEMPT",
            "severity": "CRITICAL",
            "location": "MIN-1",
            "date_occurred": datetime(2024, 2, 3, 2, 45),
            "date_reported": datetime(2024, 2, 3, 2, 50),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000008",  # Night shift
            "involved_inmates": ["test_inmate_028", "test_inmate_029"],
            "escape_method": "Cut fence with bolt cutters, attempted to scale perimeter wall",
            "escape_successful": False,
            "recapture_details": "Caught by perimeter guards, dogs deployed",
            "time_at_large": timedelta(minutes=12),
            "weapons_found": "Bolt cutters, rope ladder",
            "charges_filed": True,
            "criminal_charges": "Escape from lawful custody",
            "disciplinary_action": "Transfer to maximum security, indefinite segregation",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Tools smuggled in work programme. Inside help suspected.",
            "corrective_actions": "Work programme suspended, tool inventory enhanced",
            "status": "CLOSED",
            "notes": "Serious escape attempt. Security breach identified and corrected.",
        },
    ])

    # Edge Case 5: MEDICAL EMERGENCIES
    incidents.extend([
        {
            "incident_number": "INC-2024-00009",
            "incident_type": "MEDICAL_EMERGENCY",
            "severity": "CRITICAL",
            "location": "MAX-A",
            "date_occurred": datetime(2024, 2, 10, 16, 30),
            "date_reported": datetime(2024, 2, 10, 16, 31),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000006",
            "involved_inmates": ["test_inmate_030"],
            "medical_issue": "Cardiac arrest",
            "medical_response": "CPR performed, AED used, emergency transport",
            "hospital_admission": True,
            "hospital_name": "Princess Margaret Hospital - ICU",
            "days_hospitalized": 14,
            "outcome": "Survived - cardiac stent placed",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Pre-existing heart condition. Medical protocol followed correctly.",
            "corrective_actions": "Enhanced cardiac screening for all inmates over 50",
            "status": "CLOSED",
            "notes": "Life-saving intervention. Medical staff commended.",
        },
    ])

    # Edge Case 6: DEATHS IN CUSTODY
    incidents.extend([
        {
            "incident_number": "INC-2024-00011",
            "incident_type": "DEATH",
            "severity": "CRITICAL",
            "location": "MED-H",
            "date_occurred": datetime(2024, 2, 14, 3, 17),
            "date_reported": datetime(2024, 2, 14, 3, 20),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000013",  # Dr. Moss
            "involved_inmates": ["test_inmate_031"],
            "cause_of_death": "Natural causes - terminal cancer",
            "death_location": "Medical block",
            "medical_response": "Palliative care provided, family notified",
            "autopsy_performed": True,
            "autopsy_findings": "Confirmed metastatic pancreatic cancer",
            "coroner_notified": True,
            "family_notified": True,
            "family_notification_date": datetime(2024, 2, 14, 4, 30),
            "investigation_status": "COMPLETED",
            "investigation_findings": "Natural death. Appropriate end-of-life care provided.",
            "external_review": True,
            "external_reviewer": "Ministry of National Security Inspector General",
            "status": "CLOSED",
            "notes": "Expected death. Compassionate care documented. Family present at time of death.",
        },
        {
            "incident_number": "INC-2024-00015",
            "incident_type": "DEATH",
            "severity": "CRITICAL",
            "location": "SEG-1",
            "date_occurred": datetime(2024, 2, 28, 22, 45),
            "date_reported": datetime(2024, 2, 28, 22, 47),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000008",
            "involved_inmates": ["test_inmate_032"],
            "cause_of_death": "Suicide by hanging",
            "death_location": "Segregation cell",
            "suicide_watch": False,  # NOT on suicide watch
            "previous_self_harm": True,
            "medical_response": "CPR attempted, unsuccessful",
            "autopsy_performed": True,
            "autopsy_findings": "Asphyxiation by hanging, no foul play",
            "coroner_notified": True,
            "family_notified": True,
            "investigation_status": "ONGOING",
            "investigation_findings": "Suicide. Questions about adequacy of mental health screening.",
            "external_review": True,
            "external_reviewer": "Coroner's inquest pending",
            "status": "OPEN",
            "notes": "Tragic suicide. Full review of mental health protocols initiated.",
        },
    ])

    # Edge Case 7: SELF-HARM INCIDENTS
    incidents.extend([
        {
            "incident_number": "INC-2024-00013",
            "incident_type": "SELF_HARM",
            "severity": "HIGH",
            "location": "FEM-1",
            "date_occurred": datetime(2024, 2, 20, 18, 15),
            "date_reported": datetime(2024, 2, 20, 18, 17),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000007",
            "involved_inmates": ["test_inmate_033"],
            "self_harm_method": "Cutting - razor blade",
            "injuries": "Multiple lacerations to forearms",
            "medical_response": "Stitches required, psychiatric evaluation",
            "hospital_admission": False,
            "suicide_watch_initiated": True,
            "psychiatric_evaluation": True,
            "mental_health_follow_up": "Daily counseling sessions, medication adjustment",
            "investigation_status": "COMPLETED",
            "investigation_findings": "Depression exacerbated by family issues. Treatment plan updated.",
            "status": "CLOSED",
            "notes": "Self-harm episode. Now on suicide watch with enhanced mental health support.",
        },
    ])

    # Edge Case 8: MASS DISTURBANCE/RIOT
    incidents.extend([
        {
            "incident_number": "INC-2024-00020",
            "incident_type": "DISTURBANCE",
            "severity": "CRITICAL",
            "location": "REM-1",
            "date_occurred": datetime(2024, 3, 10, 13, 00),
            "date_reported": datetime(2024, 3, 10, 13, 02),
            "reported_by_user_id": "d1000001-0001-4000-8000-000000000005",
            "involved_inmates": [
                "test_inmate_034", "test_inmate_035", "test_inmate_036",
                "test_inmate_037", "test_inmate_038", "test_inmate_039",
                "test_inmate_040", "test_inmate_041",  # 8+ inmates
            ],
            "disturbance_type": "Riot - food protest",
            "number_involved": 47,  # Mass incident
            "use_of_force": True,
            "force_type": "Riot control team, OC spray, batons",
            "injuries": "Multiple minor injuries - inmates and staff",
            "injuries_staff": "3 officers - minor cuts and bruises",
            "medical_response": "On-site triage, 2 inmates transported to hospital",
            "property_damage": True,
            "damage_estimate": 15000.00,
            "damage_description": "Broken windows, destroyed furniture, damaged cells",
            "facility_lockdown": True,
            "lockdown_duration_hours": 72,
            "investigation_status": "ONGOING",
            "investigation_findings": "Organized protest over food quality. Gang leaders identified.",
            "corrective_actions": "Food services review, gang leaders segregated",
            "status": "OPEN",
            "notes": "Major disturbance. Facility locked down for 3 days. Full investigation underway.",
        },
    ])

    return incidents


# Summary statistics
INCIDENT_STATS = {
    "total_incidents": "Generated dynamically",
    "assault_ioi": 2,
    "assault_ios": 1,
    "contraband": 3,
    "escape_attempts": 1,
    "medical_emergencies": 1,
    "deaths": 2,
    "self_harm": 1,
    "mass_disturbances": 1,
    "critical_severity": 7,
    "use_of_force_incidents": 6,
}
