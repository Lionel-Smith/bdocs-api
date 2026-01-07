"""
BDOCS Seed Data - Report Definitions

Standard report definitions for the BDOCS reporting module.
Each report has a unique code following the pattern RPT-{CATEGORY}-{NUMBER}.

Report Definition Fields:
- code: Unique identifier (RPT-XXX-NNN)
- name: Human-readable name
- description: Detailed description
- category: POPULATION | INCIDENT | PROGRAMME | HEALTHCARE | COMPLIANCE | FINANCIAL | OPERATIONAL
- output_format: PDF | EXCEL | CSV | JSON
- parameters_schema: JSON Schema for required parameters
- is_scheduled: Whether report can be scheduled
- schedule_cron: Cron expression for scheduled reports
- created_by: User ID who created the definition
"""
from datetime import datetime, timezone
from uuid import uuid4

# Import user IDs for created_by references
from scripts.seeds.users import USER_IDS

# Fixed UUIDs for report definitions
REPORT_IDS = {
    "pop-001": "f3000001-0001-4000-8000-000000000001",
    "pop-002": "f3000001-0001-4000-8000-000000000002",
    "pop-003": "f3000001-0001-4000-8000-000000000003",
    "inc-001": "f3000001-0001-4000-8000-000000000004",
    "inc-002": "f3000001-0001-4000-8000-000000000005",
    "prg-001": "f3000001-0001-4000-8000-000000000006",
    "prg-002": "f3000001-0001-4000-8000-000000000007",
    "hlt-001": "f3000001-0001-4000-8000-000000000008",
    "hlt-002": "f3000001-0001-4000-8000-000000000009",
    "cmp-001": "f3000001-0001-4000-8000-000000000010",
    "cmp-002": "f3000001-0001-4000-8000-000000000011",
    "opr-001": "f3000001-0001-4000-8000-000000000012",
    "opr-002": "f3000001-0001-4000-8000-000000000013",
    "fin-001": "f3000001-0001-4000-8000-000000000014",
}

REPORT_DEFINITIONS = [
    # ========================================================================
    # POPULATION Reports
    # ========================================================================
    {
        "id": REPORT_IDS["pop-001"],
        "code": "RPT-POP-001",
        "name": "Daily Population Summary",
        "description": "Daily snapshot of total population by housing unit, security level, and status. "
                       "Includes capacity utilization and movement counts for the reporting period.",
        "category": "POPULATION",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "as_of_date": {"type": "string", "format": "date", "description": "Report date"}
            },
            "required": ["as_of_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 6 * * *",  # Daily at 6 AM
        "created_by": USER_IDS["admin"],
    },
    {
        "id": REPORT_IDS["pop-002"],
        "code": "RPT-POP-002",
        "name": "Monthly Population Statistics",
        "description": "Monthly population trends, demographics breakdown by age, nationality, and gender. "
                       "Includes admission/release rates and average length of stay metrics.",
        "category": "POPULATION",
        "output_format": "EXCEL",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Report year"},
                "month": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Report month"}
            },
            "required": ["year", "month"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 7 1 * *",  # 1st of each month at 7 AM
        "created_by": USER_IDS["admin"],
    },
    {
        "id": REPORT_IDS["pop-003"],
        "code": "RPT-POP-003",
        "name": "Housing Unit Capacity Report",
        "description": "Detailed capacity analysis by housing unit including overcrowding indicators, "
                       "bed availability, and maintenance status.",
        "category": "POPULATION",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "as_of_date": {"type": "string", "format": "date"}
            }
        },
        "is_scheduled": False,
        "schedule_cron": None,
        "created_by": USER_IDS["admin"],
    },

    # ========================================================================
    # INCIDENT Reports
    # ========================================================================
    {
        "id": REPORT_IDS["inc-001"],
        "code": "RPT-INC-001",
        "name": "Weekly Incident Summary",
        "description": "Summary of all incidents during the reporting week by type, severity, location, "
                       "and resolution status. Includes use of force incidents breakdown.",
        "category": "INCIDENT",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 8 * * 1",  # Every Monday at 8 AM
        "created_by": USER_IDS["admin"],
    },
    {
        "id": REPORT_IDS["inc-002"],
        "code": "RPT-INC-002",
        "name": "Use of Force Report",
        "description": "Detailed analysis of all use of force incidents including type of force used, "
                       "circumstances, injuries, and review outcomes. Required for ACA compliance.",
        "category": "INCIDENT",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 8 1 * *",  # 1st of each month
        "created_by": USER_IDS["admin"],
    },

    # ========================================================================
    # PROGRAMME Reports
    # ========================================================================
    {
        "id": REPORT_IDS["prg-001"],
        "code": "RPT-PRG-001",
        "name": "Programme Participation Report",
        "description": "Enrollment and completion statistics for all rehabilitation programmes. "
                       "Includes BTVI certification rates and waitlist information.",
        "category": "PROGRAMME",
        "output_format": "EXCEL",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "programme_code": {"type": "string", "description": "Filter by specific programme"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 9 1 * *",  # 1st of each month
        "created_by": USER_IDS["d.thompson"],
    },
    {
        "id": REPORT_IDS["prg-002"],
        "code": "RPT-PRG-002",
        "name": "BTVI Certification Report",
        "description": "BTVI vocational training completion and certification report. "
                       "Tracks accredited courses, student outcomes, and certification dates.",
        "category": "PROGRAMME",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "quarter": {"type": "integer", "minimum": 1, "maximum": 4}
            },
            "required": ["year", "quarter"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 9 1 1,4,7,10 *",  # Quarterly
        "created_by": USER_IDS["n.mcphee"],
    },

    # ========================================================================
    # HEALTHCARE Reports
    # ========================================================================
    {
        "id": REPORT_IDS["hlt-001"],
        "code": "RPT-HLT-001",
        "name": "Daily Healthcare Activity",
        "description": "Daily summary of healthcare services including sick calls, medication distribution, "
                       "chronic care visits, and mental health encounters.",
        "category": "HEALTHCARE",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"}
            },
            "required": ["date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 17 * * *",  # Daily at 5 PM
        "created_by": USER_IDS["dr.moss"],
    },
    {
        "id": REPORT_IDS["hlt-002"],
        "code": "RPT-HLT-002",
        "name": "Medication Compliance Report",
        "description": "Medication administration compliance rates, refusals, and distribution statistics. "
                       "Required for NCCHC accreditation.",
        "category": "HEALTHCARE",
        "output_format": "EXCEL",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 8 * * 1",  # Weekly on Monday
        "created_by": USER_IDS["dr.moss"],
    },

    # ========================================================================
    # COMPLIANCE Reports
    # ========================================================================
    {
        "id": REPORT_IDS["cmp-001"],
        "code": "RPT-CMP-001",
        "name": "ACA Compliance Status",
        "description": "Current compliance status against ACA (American Correctional Association) standards. "
                       "Shows compliance percentage, gaps, and corrective action status.",
        "category": "COMPLIANCE",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "as_of_date": {"type": "string", "format": "date"}
            }
        },
        "is_scheduled": True,
        "schedule_cron": "0 7 1 * *",  # Monthly
        "created_by": USER_IDS["admin"],
    },
    {
        "id": REPORT_IDS["cmp-002"],
        "code": "RPT-CMP-002",
        "name": "Audit Preparation Report",
        "description": "Comprehensive pre-audit report with evidence status, documentation gaps, "
                       "and recommended actions for upcoming ACA audits.",
        "category": "COMPLIANCE",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "audit_date": {"type": "string", "format": "date"},
                "standards": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["audit_date"]
        },
        "is_scheduled": False,
        "schedule_cron": None,
        "created_by": USER_IDS["admin"],
    },

    # ========================================================================
    # OPERATIONAL Reports
    # ========================================================================
    {
        "id": REPORT_IDS["opr-001"],
        "code": "RPT-OPR-001",
        "name": "Staff Schedule Report",
        "description": "Daily staff schedule showing coverage by shift, housing unit assignments, "
                       "leave status, and overtime hours.",
        "category": "OPERATIONAL",
        "output_format": "EXCEL",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "department": {"type": "string"}
            },
            "required": ["date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 5 * * *",  # Daily at 5 AM
        "created_by": USER_IDS["t.rolle"],
    },
    {
        "id": REPORT_IDS["opr-002"],
        "code": "RPT-OPR-002",
        "name": "Visitation Summary Report",
        "description": "Visitation statistics including visitor counts, visit types, denials, "
                       "and duration metrics.",
        "category": "OPERATIONAL",
        "output_format": "PDF",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 8 * * 1",  # Weekly on Monday
        "created_by": USER_IDS["admin"],
    },

    # ========================================================================
    # FINANCIAL Reports
    # ========================================================================
    {
        "id": REPORT_IDS["fin-001"],
        "code": "RPT-FIN-001",
        "name": "Commissary Sales Report",
        "description": "Commissary transaction summary including sales by category, inmate spending patterns, "
                       "and inventory status.",
        "category": "FINANCIAL",
        "output_format": "EXCEL",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["start_date", "end_date"]
        },
        "is_scheduled": True,
        "schedule_cron": "0 9 1 * *",  # Monthly
        "created_by": USER_IDS["admin"],
    },
]

# Summary statistics
REPORT_STATS = {
    "total_definitions": len(REPORT_DEFINITIONS),
    "by_category": {
        "POPULATION": len([r for r in REPORT_DEFINITIONS if r["category"] == "POPULATION"]),
        "INCIDENT": len([r for r in REPORT_DEFINITIONS if r["category"] == "INCIDENT"]),
        "PROGRAMME": len([r for r in REPORT_DEFINITIONS if r["category"] == "PROGRAMME"]),
        "HEALTHCARE": len([r for r in REPORT_DEFINITIONS if r["category"] == "HEALTHCARE"]),
        "COMPLIANCE": len([r for r in REPORT_DEFINITIONS if r["category"] == "COMPLIANCE"]),
        "OPERATIONAL": len([r for r in REPORT_DEFINITIONS if r["category"] == "OPERATIONAL"]),
        "FINANCIAL": len([r for r in REPORT_DEFINITIONS if r["category"] == "FINANCIAL"]),
    },
    "scheduled_reports": len([r for r in REPORT_DEFINITIONS if r["is_scheduled"]]),
    "ad_hoc_reports": len([r for r in REPORT_DEFINITIONS if not r["is_scheduled"]]),
}
