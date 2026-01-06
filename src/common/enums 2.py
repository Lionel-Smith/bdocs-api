"""
BDOCS Prison Information System - Enumeration Types

These are specific to Bahamian correctional context.
CRITICAL: The Bahamas does NOT have parole. Uses Prerogative of Mercy (clemency).
"""
from enum import Enum


class InmateStatus(str, Enum):
    """Inmate custody status."""
    REMAND = "REMAND"           # Pre-trial detention (~37% of population)
    SENTENCED = "SENTENCED"     # Convicted and serving sentence
    RELEASED = "RELEASED"       # Released from custody
    TRANSFERRED = "TRANSFERRED" # Transferred to another facility
    DECEASED = "DECEASED"       # Death in custody


class SecurityLevel(str, Enum):
    """Security classification levels."""
    MAXIMUM = "MAXIMUM"
    MEDIUM = "MEDIUM"
    MINIMUM = "MINIMUM"


class Gender(str, Enum):
    """Gender classification for housing."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class UserRole(str, Enum):
    """BDOCS system user roles for RBAC."""
    ADMIN = "ADMIN"             # Full system access
    SUPERVISOR = "SUPERVISOR"   # Department supervisor
    OFFICER = "OFFICER"         # Correctional officer
    INTAKE = "INTAKE"           # Intake processing only
    PROGRAMMES = "PROGRAMMES"   # Programme management
    MEDICAL = "MEDICAL"         # Healthcare access
    RECORDS = "RECORDS"         # Records department
    READONLY = "READONLY"       # View-only access


class ClemencyType(str, Enum):
    """
    Prerogative of Mercy petition types.
    Reference: Constitution of The Bahamas, Articles 90-92
    """
    PARDON = "PARDON"              # Full forgiveness of conviction
    COMMUTATION = "COMMUTATION"    # Reduce sentence
    REMISSION = "REMISSION"        # Time off for good behavior
    RESPITE = "RESPITE"            # Temporary delay of execution
    REPRIEVE = "REPRIEVE"          # Postponement of sentence execution
    EARLY_RELEASE = "EARLY_RELEASE" # Release before sentence end


class PetitionType(str, Enum):
    """
    Types of clemency petitions.
    Reference: Constitution of The Bahamas, Articles 90-92
    """
    COMMUTATION = "COMMUTATION"    # Reduce severity of sentence
    PARDON = "PARDON"              # Full forgiveness, expunges conviction
    REMISSION = "REMISSION"        # Reduction of remaining term
    REPRIEVE = "REPRIEVE"          # Postponement (esp. for death sentences)


class PetitionStatus(str, Enum):
    """
    Clemency petition workflow states.

    Workflow: SUBMITTED → UNDER_REVIEW → COMMITTEE_SCHEDULED →
              AWAITING_MINISTER → GOVERNOR_GENERAL → GRANTED/DENIED
    """
    SUBMITTED = "SUBMITTED"                   # Initial filing
    UNDER_REVIEW = "UNDER_REVIEW"             # Staff review
    COMMITTEE_SCHEDULED = "COMMITTEE_SCHEDULED" # Scheduled for Advisory Committee
    AWAITING_MINISTER = "AWAITING_MINISTER"   # Committee done, awaiting Minister
    GOVERNOR_GENERAL = "GOVERNOR_GENERAL"     # Awaiting Governor-General decision
    GRANTED = "GRANTED"                       # Clemency granted
    DENIED = "DENIED"                         # Clemency denied
    WITHDRAWN = "WITHDRAWN"                   # Petitioner withdrew
    DEFERRED = "DEFERRED"                     # Decision postponed


class MovementType(str, Enum):
    """Types of inmate movement."""
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    COURT_TRANSPORT = "COURT_TRANSPORT"
    MEDICAL_TRANSPORT = "MEDICAL_TRANSPORT"
    WORK_RELEASE = "WORK_RELEASE"
    TEMPORARY_RELEASE = "TEMPORARY_RELEASE"
    FURLOUGH = "FURLOUGH"
    EXTERNAL_APPOINTMENT = "EXTERNAL_APPOINTMENT"
    RELEASE = "RELEASE"


class MovementStatus(str, Enum):
    """Movement workflow status."""
    SCHEDULED = "SCHEDULED"       # Movement planned
    IN_PROGRESS = "IN_PROGRESS"   # Movement underway
    COMPLETED = "COMPLETED"       # Movement finished
    CANCELLED = "CANCELLED"       # Movement cancelled


class SentenceType(str, Enum):
    """Types of sentences in Bahamian courts."""
    IMPRISONMENT = "IMPRISONMENT"   # Fixed-term imprisonment
    LIFE = "LIFE"                   # Life imprisonment
    DEATH = "DEATH"                 # Death penalty (capital cases)
    SUSPENDED = "SUSPENDED"         # Suspended sentence
    TIME_SERVED = "TIME_SERVED"     # Already served pre-trial
    PROBATION = "PROBATION"         # Probation order
    FINE = "FINE"                   # Monetary fine


class AdjustmentType(str, Enum):
    """
    Types of sentence adjustments.

    Reference: Prison Act of The Bahamas
    - Remission: Up to 1/3 off for good behavior
    - Good time: Daily credits for conduct
    """
    GOOD_TIME = "GOOD_TIME"                   # Daily good behavior credits
    REMISSION = "REMISSION"                   # Statutory 1/3 reduction
    TIME_SERVED_CREDIT = "TIME_SERVED_CREDIT" # Pre-trial detention credit
    CLEMENCY_REDUCTION = "CLEMENCY_REDUCTION" # Prerogative of Mercy
    COURT_MODIFICATION = "COURT_MODIFICATION" # Court-ordered change


class HearingType(str, Enum):
    """Court hearing types."""
    ARRAIGNMENT = "ARRAIGNMENT"
    BAIL_HEARING = "BAIL_HEARING"
    PRELIMINARY_INQUIRY = "PRELIMINARY_INQUIRY"
    TRIAL = "TRIAL"
    SENTENCING = "SENTENCING"
    APPEAL = "APPEAL"
    MENTION = "MENTION"
    OTHER = "OTHER"


class IncidentType(str, Enum):
    """Incident classification for reporting."""
    ASSAULT_IOI = "ASSAULT_IOI"       # Inmate on Inmate
    ASSAULT_IOS = "ASSAULT_IOS"       # Inmate on Staff
    CONTRABAND = "CONTRABAND"
    ESCAPE_ATTEMPT = "ESCAPE_ATTEMPT"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    DISTURBANCE = "DISTURBANCE"
    PROPERTY_DAMAGE = "PROPERTY_DAMAGE"
    RULE_VIOLATION = "RULE_VIOLATION"
    DEATH = "DEATH"
    SELF_HARM = "SELF_HARM"
    OTHER = "OTHER"


class AuditAction(str, Enum):
    """Audit log action types."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class CourtType(str, Enum):
    """
    Bahamian court system hierarchy.

    Reference: Courts Act (Chapter 54), The Bahamas
    """
    MAGISTRATES = "MAGISTRATES"         # Minor offenses, preliminary inquiries
    SUPREME = "SUPREME"                 # Serious criminal cases
    COURT_OF_APPEAL = "COURT_OF_APPEAL" # Appeals from Supreme Court
    PRIVY_COUNCIL = "PRIVY_COUNCIL"     # Final appellate (London)
    CORONERS = "CORONERS"               # Death investigations


class CaseStatus(str, Enum):
    """Court case status."""
    PENDING = "PENDING"         # Case filed, awaiting proceedings
    ACTIVE = "ACTIVE"           # Case in progress
    ADJUDICATED = "ADJUDICATED" # Case decided
    DISMISSED = "DISMISSED"     # Case dismissed
    APPEALED = "APPEALED"       # Decision under appeal


class AppearanceType(str, Enum):
    """Types of court appearances."""
    ARRAIGNMENT = "ARRAIGNMENT"     # Initial appearance, plea entry
    BAIL_HEARING = "BAIL_HEARING"   # Bail/remand decision
    TRIAL = "TRIAL"                 # Trial proceedings
    SENTENCING = "SENTENCING"       # Sentencing hearing
    APPEAL = "APPEAL"               # Appeal hearing
    MOTION = "MOTION"               # Motion hearing


class AppearanceOutcome(str, Enum):
    """Outcome of a court appearance."""
    ADJOURNED = "ADJOURNED"         # Case adjourned to later date
    BAIL_GRANTED = "BAIL_GRANTED"   # Bail granted
    BAIL_DENIED = "BAIL_DENIED"     # Bail denied, remanded
    CONVICTED = "CONVICTED"         # Found guilty
    ACQUITTED = "ACQUITTED"         # Found not guilty
    SENTENCED = "SENTENCED"         # Sentence imposed
    REMANDED = "REMANDED"           # Remanded to custody


# ============================================================================
# Programme Module Enums (Phase 2)
# ============================================================================

class ProgrammeCategory(str, Enum):
    """
    Categories of rehabilitation programmes.

    Reference: BDOCS Rehabilitation Framework
    """
    EDUCATIONAL = "EDUCATIONAL"     # GED, literacy, academic courses
    VOCATIONAL = "VOCATIONAL"       # Trade skills (carpentry, plumbing, etc.)
    THERAPEUTIC = "THERAPEUTIC"     # Substance abuse, anger management
    RELIGIOUS = "RELIGIOUS"         # Faith-based programmes
    LIFE_SKILLS = "LIFE_SKILLS"     # Financial literacy, parenting, etc.


class SessionStatus(str, Enum):
    """Status of a programme session."""
    SCHEDULED = "SCHEDULED"         # Session planned
    COMPLETED = "COMPLETED"         # Session held successfully
    CANCELLED = "CANCELLED"         # Session cancelled


class EnrollmentStatus(str, Enum):
    """
    Status of an inmate's programme enrollment.

    Workflow: ENROLLED → ACTIVE → COMPLETED
    Alternative paths: WITHDRAWN, SUSPENDED
    """
    ENROLLED = "ENROLLED"           # Initially enrolled, not yet started
    ACTIVE = "ACTIVE"               # Currently participating
    COMPLETED = "COMPLETED"         # Successfully completed programme
    WITHDRAWN = "WITHDRAWN"         # Voluntarily withdrew
    SUSPENDED = "SUSPENDED"         # Enrollment suspended (discipline, etc.)


# ============================================================================
# BTVI Certification Enums
# ============================================================================

class BTVICertType(str, Enum):
    """
    BTVI (Bahamas Technical and Vocational Institute) certification types.

    Reference: BTVI Programme Offerings
    These align with industry-standard vocational trades.
    """
    AUTOMOTIVE = "AUTOMOTIVE"       # Auto mechanics, body work
    ELECTRICAL = "ELECTRICAL"       # Electrical installation, wiring
    PLUMBING = "PLUMBING"           # Plumbing installation, repair
    CARPENTRY = "CARPENTRY"         # Wood construction, cabinetry
    WELDING = "WELDING"             # Metal welding, fabrication
    CULINARY = "CULINARY"           # Food preparation, cooking
    COSMETOLOGY = "COSMETOLOGY"     # Hair, beauty services
    HVAC = "HVAC"                   # Heating, ventilation, air conditioning
    MASONRY = "MASONRY"             # Block/brick laying, concrete work


class SkillLevel(str, Enum):
    """
    Skill proficiency level for vocational certifications.

    Progression: BASIC → INTERMEDIATE → ADVANCED → MASTER
    """
    BASIC = "BASIC"                 # Entry-level skills
    INTERMEDIATE = "INTERMEDIATE"   # Journeyman-level competency
    ADVANCED = "ADVANCED"           # Expert-level proficiency
    MASTER = "MASTER"               # Instructor/master craftsman level


# ============================================================================
# Case Management Enums
# ============================================================================

class NoteType(str, Enum):
    """
    Types of case notes for inmate documentation.

    These support comprehensive case management and
    rehabilitation tracking.
    """
    INITIAL_ASSESSMENT = "INITIAL_ASSESSMENT"   # Intake assessment
    PROGRESS_UPDATE = "PROGRESS_UPDATE"         # Regular progress notes
    INCIDENT_REPORT = "INCIDENT_REPORT"         # Behavioral incidents
    PROGRAMME_REVIEW = "PROGRAMME_REVIEW"       # Programme participation review
    RELEASE_PLANNING = "RELEASE_PLANNING"       # Pre-release preparation
    GENERAL = "GENERAL"                         # General case notes


class GoalType(str, Enum):
    """
    Types of rehabilitation goals for inmates.

    Aligned with evidence-based rehabilitation practices
    and reintegration preparation.
    """
    EDUCATION = "EDUCATION"                     # GED, literacy, academic
    VOCATIONAL = "VOCATIONAL"                   # Trade skills, BTVI certs
    BEHAVIORAL = "BEHAVIORAL"                   # Anger management, conflict resolution
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE"         # Addiction treatment, recovery
    FAMILY_REUNIFICATION = "FAMILY_REUNIFICATION"  # Family relationships
    EMPLOYMENT = "EMPLOYMENT"                   # Job readiness, skills
    HOUSING = "HOUSING"                         # Post-release housing plan


class GoalStatus(str, Enum):
    """
    Status of rehabilitation goals.

    Workflow: NOT_STARTED → IN_PROGRESS → COMPLETED
    Alternative paths: DEFERRED, CANCELLED
    """
    NOT_STARTED = "NOT_STARTED"     # Goal set but not begun
    IN_PROGRESS = "IN_PROGRESS"     # Actively working on goal
    COMPLETED = "COMPLETED"         # Goal achieved
    DEFERRED = "DEFERRED"           # Goal postponed
    CANCELLED = "CANCELLED"         # Goal no longer applicable


# ============================================================================
# Work Release Enums
# ============================================================================

class WorkReleaseStatus(str, Enum):
    """
    Status of work release assignments.

    Workflow: PENDING_APPROVAL → APPROVED → ACTIVE → COMPLETED
    Alternative paths: SUSPENDED, TERMINATED
    """
    PENDING_APPROVAL = "PENDING_APPROVAL"   # Awaiting supervisor approval
    APPROVED = "APPROVED"                   # Approved, not yet started
    ACTIVE = "ACTIVE"                       # Currently working
    SUSPENDED = "SUSPENDED"                 # Temporarily suspended
    COMPLETED = "COMPLETED"                 # Successfully completed
    TERMINATED = "TERMINATED"               # Ended early (disciplinary, etc.)


class LogStatus(str, Enum):
    """
    Status of work release daily logs.

    Tracks inmate departures and returns for security.
    """
    DEPARTED = "DEPARTED"               # Left for work, not yet returned
    RETURNED_ON_TIME = "RETURNED_ON_TIME"   # Returned by expected time
    RETURNED_LATE = "RETURNED_LATE"     # Returned after expected time
    DID_NOT_RETURN = "DID_NOT_RETURN"   # Failed to return (serious incident)
    EXCUSED = "EXCUSED"                 # Absence excused (holiday, sick, etc.)


# ============================================================================
# Reentry Planning Enums
# ============================================================================

class PlanStatus(str, Enum):
    """
    Status of reentry/release preparation plan.

    Workflow: DRAFT → IN_PROGRESS → READY → COMPLETED
    """
    DRAFT = "DRAFT"                     # Initial plan creation
    IN_PROGRESS = "IN_PROGRESS"         # Actively working on preparation
    READY = "READY"                     # All items complete, ready for release
    COMPLETED = "COMPLETED"             # Inmate released, plan executed


class HousingPlan(str, Enum):
    """
    Post-release housing arrangement type.

    Housing stability is critical for successful reintegration.
    """
    FAMILY = "FAMILY"                   # Returning to family residence
    SHELTER = "SHELTER"                 # Emergency/transitional shelter
    TRANSITIONAL = "TRANSITIONAL"       # Transitional housing programme
    INDEPENDENT = "INDEPENDENT"         # Own residence/rental
    UNKNOWN = "UNKNOWN"                 # Housing not yet determined


class ChecklistType(str, Enum):
    """
    Categories of reentry preparation checklist items.

    Each category addresses a key area for successful reintegration.
    """
    DOCUMENTATION = "DOCUMENTATION"     # ID, birth certificate, NIB card
    HOUSING = "HOUSING"                 # Housing arrangement confirmed
    EMPLOYMENT = "EMPLOYMENT"           # Job or job search plan
    HEALTHCARE = "HEALTHCARE"           # Medical needs, prescriptions
    FAMILY = "FAMILY"                   # Family reunification contacts
    FINANCIAL = "FINANCIAL"             # Savings, bank account, benefits
    SUPERVISION = "SUPERVISION"         # Probation/reporting requirements


class ServiceType(str, Enum):
    """
    Types of external support services for referrals.

    These services support successful community reintegration.
    """
    HOUSING_ASSISTANCE = "HOUSING_ASSISTANCE"       # Housing support programmes
    JOB_PLACEMENT = "JOB_PLACEMENT"                 # Employment services
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE"             # Addiction treatment
    MENTAL_HEALTH = "MENTAL_HEALTH"                 # Mental health services
    FAMILY_COUNSELING = "FAMILY_COUNSELING"         # Family therapy/mediation
    FINANCIAL_AID = "FINANCIAL_AID"                 # Financial assistance
    TRANSPORTATION = "TRANSPORTATION"               # Transport assistance
    LEGAL_AID = "LEGAL_AID"                         # Legal services


class ReferralStatus(str, Enum):
    """
    Status of service referral.

    Workflow: PENDING → ACCEPTED → IN_PROGRESS → COMPLETED
    Alternative: DECLINED
    """
    PENDING = "PENDING"                 # Referral submitted, awaiting response
    ACCEPTED = "ACCEPTED"               # Provider accepted referral
    IN_PROGRESS = "IN_PROGRESS"         # Services being provided
    COMPLETED = "COMPLETED"             # Services successfully completed
    DECLINED = "DECLINED"               # Referral declined by provider


# ============================================================================
# Incident Management Enums (Phase 3)
# ============================================================================

class IncidentType(str, Enum):
    """
    Classification of security incidents.

    Covers range from minor rule violations to critical events
    requiring external notification.
    """
    ASSAULT = "ASSAULT"                     # Physical altercation (IOI or IOS)
    CONTRABAND = "CONTRABAND"               # Prohibited items discovered
    ESCAPE_ATTEMPT = "ESCAPE_ATTEMPT"       # Attempted or actual escape
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY" # Medical crisis requiring response
    FIRE = "FIRE"                           # Fire or arson
    DISTURBANCE = "DISTURBANCE"             # Riot, protest, group disturbance
    PROPERTY_DAMAGE = "PROPERTY_DAMAGE"     # Vandalism, destruction
    DEATH = "DEATH"                         # Death in custody
    SUICIDE_ATTEMPT = "SUICIDE_ATTEMPT"     # Self-harm with suicidal intent
    DRUG_USE = "DRUG_USE"                   # Drug/alcohol use or intoxication
    WEAPON = "WEAPON"                       # Weapon found or used
    OTHER = "OTHER"                         # Other incidents


class IncidentSeverity(str, Enum):
    """
    Severity level of incidents.

    Determines response urgency and notification requirements.
    """
    LOW = "LOW"             # Minor incident, routine handling
    MEDIUM = "MEDIUM"       # Moderate incident, supervisor notification
    HIGH = "HIGH"           # Serious incident, management notification
    CRITICAL = "CRITICAL"   # Emergency, external notification may be required


class IncidentStatus(str, Enum):
    """
    Status of incident investigation and resolution.

    Workflow: REPORTED → UNDER_INVESTIGATION → RESOLVED → CLOSED
    """
    REPORTED = "REPORTED"                       # Initial report filed
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION" # Investigation in progress
    RESOLVED = "RESOLVED"                       # Investigation complete, awaiting closure
    CLOSED = "CLOSED"                           # Incident fully closed


class InvolvementType(str, Enum):
    """
    Type of involvement in an incident.

    Categorizes role of each person in the incident.
    """
    VICTIM = "VICTIM"           # Person harmed in incident
    PERPETRATOR = "PERPETRATOR" # Person responsible for incident
    WITNESS = "WITNESS"         # Person who witnessed incident
    RESPONDER = "RESPONDER"     # Staff who responded to incident
    OTHER = "OTHER"             # Other involvement


# ============================================================================
# Staff Management Enums (Phase 3)
# ============================================================================

class StaffRank(str, Enum):
    """
    Correctional officer ranks in BDOCS.

    Reference: Bahamas Department of Correctional Services hierarchy.
    Ranks follow Commonwealth correctional service structure.
    """
    SUPERINTENDENT = "SUPERINTENDENT"               # Facility commander
    DEPUTY_SUPERINTENDENT = "DEPUTY_SUPERINTENDENT" # Second in command
    ASSISTANT_SUPERINTENDENT = "ASSISTANT_SUPERINTENDENT"  # Department head
    CHIEF_OFFICER = "CHIEF_OFFICER"                 # Senior supervisory
    SENIOR_OFFICER = "SENIOR_OFFICER"               # Experienced officer
    OFFICER = "OFFICER"                             # Standard correctional officer
    RECRUIT = "RECRUIT"                             # Trainee officer


class Department(str, Enum):
    """
    BDOCS organizational departments.

    Each department has specific responsibilities within
    correctional facility operations.
    """
    ADMINISTRATION = "ADMINISTRATION"   # Administrative staff
    SECURITY = "SECURITY"               # Security and custody
    PROGRAMMES = "PROGRAMMES"           # Rehabilitation programmes
    MEDICAL = "MEDICAL"                 # Healthcare services
    RECORDS = "RECORDS"                 # Inmate records and data
    MAINTENANCE = "MAINTENANCE"         # Facility maintenance
    KITCHEN = "KITCHEN"                 # Food services


class StaffStatus(str, Enum):
    """
    Employment status of staff members.

    Active status required for shift assignments and system access.
    """
    ACTIVE = "ACTIVE"           # Currently employed and working
    ON_LEAVE = "ON_LEAVE"       # Approved leave (vacation, medical, etc.)
    SUSPENDED = "SUSPENDED"     # Administrative suspension
    TERMINATED = "TERMINATED"   # Employment ended


class ShiftType(str, Enum):
    """
    Work shift classifications.

    Standard 8-hour shifts covering 24-hour operations.
    """
    DAY = "DAY"         # Typically 0700-1500
    EVENING = "EVENING" # Typically 1500-2300
    NIGHT = "NIGHT"     # Typically 2300-0700


class ShiftStatus(str, Enum):
    """
    Status of scheduled shifts.

    Tracks shift assignment lifecycle from scheduling to completion.
    """
    SCHEDULED = "SCHEDULED"     # Shift assigned, not yet started
    IN_PROGRESS = "IN_PROGRESS" # Shift currently active
    COMPLETED = "COMPLETED"     # Shift finished normally
    ABSENT = "ABSENT"           # Staff did not report for shift
    SWAPPED = "SWAPPED"         # Shift traded with another officer


class TrainingType(str, Enum):
    """
    Types of staff training and certifications.

    Many certifications have expiry dates and require periodic renewal.
    Reference: ACA (American Correctional Association) standards.
    """
    ORIENTATION = "ORIENTATION"             # New employee orientation
    USE_OF_FORCE = "USE_OF_FORCE"           # Use of force policies and procedures
    FIRST_AID = "FIRST_AID"                 # Basic first aid (expires annually)
    CPR = "CPR"                             # CPR certification (expires annually)
    FIREARMS = "FIREARMS"                   # Firearms qualification
    CRISIS_INTERVENTION = "CRISIS_INTERVENTION"  # Crisis response and de-escalation
    ACA_STANDARDS = "ACA_STANDARDS"         # ACA compliance training
    DEFENSIVE_TACTICS = "DEFENSIVE_TACTICS" # Self-defense and control techniques


# ============================================================================
# Visitation Management Enums (Phase 3)
# ============================================================================

class Relationship(str, Enum):
    """
    Relationship types for approved visitors.

    Determines visitation privileges and verification requirements.
    """
    SPOUSE = "SPOUSE"                   # Married partner
    PARENT = "PARENT"                   # Mother or father
    CHILD = "CHILD"                     # Son or daughter
    SIBLING = "SIBLING"                 # Brother or sister
    GRANDPARENT = "GRANDPARENT"         # Grandmother or grandfather
    LEGAL_COUNSEL = "LEGAL_COUNSEL"     # Attorney (privileged visits)
    CLERGY = "CLERGY"                   # Religious minister/pastor
    OTHER = "OTHER"                     # Other approved relationship


class IDType(str, Enum):
    """
    Accepted identification types for visitor verification.

    Reference: Common Bahamian identification documents.
    """
    PASSPORT = "PASSPORT"               # Bahamian or foreign passport
    DRIVERS_LICENSE = "DRIVERS_LICENSE" # Valid driver's license
    NIB_CARD = "NIB_CARD"               # National Insurance Board card
    VOTER_CARD = "VOTER_CARD"           # Voter registration card


class CheckStatus(str, Enum):
    """
    Background check status for visitor approval.

    Visitors must pass background check before approval.
    """
    PENDING = "PENDING"     # Check requested, awaiting results
    APPROVED = "APPROVED"   # Background check passed
    DENIED = "DENIED"       # Background check failed
    EXPIRED = "EXPIRED"     # Previous approval expired, needs renewal


class VisitType(str, Enum):
    """
    Types of visitation.

    Different types have different rules and durations.
    """
    GENERAL = "GENERAL"             # Standard family/friend visit
    LEGAL = "LEGAL"                 # Attorney visit (privileged, private)
    CLERGY = "CLERGY"               # Religious minister visit
    FAMILY_SPECIAL = "FAMILY_SPECIAL"  # Extended family visit (special approval)
    VIDEO = "VIDEO"                 # Video/virtual visit


class VisitStatus(str, Enum):
    """
    Status of a scheduled visit.

    Workflow: SCHEDULED → CHECKED_IN → IN_PROGRESS → COMPLETED
    Alternative paths: CANCELLED, NO_SHOW
    """
    SCHEDULED = "SCHEDULED"     # Visit booked
    CHECKED_IN = "CHECKED_IN"   # Visitor arrived and checked in
    IN_PROGRESS = "IN_PROGRESS" # Visit currently underway
    COMPLETED = "COMPLETED"     # Visit finished normally
    CANCELLED = "CANCELLED"     # Visit cancelled before occurrence
    NO_SHOW = "NO_SHOW"         # Visitor did not arrive


# ============================================================================
# Healthcare Management Enums (Phase 3)
# ============================================================================

class BloodType(str, Enum):
    """
    Blood type classification.

    Standard ABO blood group system with Rh factor.
    """
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "UNKNOWN"


class EncounterType(str, Enum):
    """
    Types of medical encounters.

    Intake screening is mandatory for all new inmates.
    """
    INTAKE_SCREENING = "INTAKE_SCREENING"   # Initial health assessment on admission
    SICK_CALL = "SICK_CALL"                 # Routine sick call request
    EMERGENCY = "EMERGENCY"                 # Emergency medical situation
    SCHEDULED = "SCHEDULED"                 # Pre-scheduled appointment
    MENTAL_HEALTH = "MENTAL_HEALTH"         # Mental health evaluation/treatment
    DENTAL = "DENTAL"                       # Dental care
    FOLLOW_UP = "FOLLOW_UP"                 # Follow-up from previous encounter


class ProviderType(str, Enum):
    """
    Types of healthcare providers.

    Determines scope of practice and treatment authority.
    """
    PHYSICIAN = "PHYSICIAN"         # Medical doctor
    NURSE = "NURSE"                 # Registered nurse
    MENTAL_HEALTH = "MENTAL_HEALTH" # Psychologist/counselor
    DENTIST = "DENTIST"             # Dental provider
    PARAMEDIC = "PARAMEDIC"         # Emergency medical technician


class RouteType(str, Enum):
    """
    Medication administration routes.

    Determines how medication is delivered.
    """
    ORAL = "ORAL"           # By mouth
    INJECTION = "INJECTION" # Intramuscular or subcutaneous
    TOPICAL = "TOPICAL"     # Applied to skin
    INHALED = "INHALED"     # Inhaled (respiratory)


class MedAdminStatus(str, Enum):
    """
    Status of medication administration.

    Refused medications require witness documentation.
    """
    SCHEDULED = "SCHEDULED"       # Dose scheduled, not yet due
    ADMINISTERED = "ADMINISTERED" # Medication given successfully
    REFUSED = "REFUSED"           # Inmate refused medication (requires witness)
    MISSED = "MISSED"             # Dose missed (inmate unavailable)
    HELD = "HELD"                 # Held per provider order


# ============================================================================
# ACA Compliance Reporting Enums (Phase 3)
# ============================================================================

class ACACategory(str, Enum):
    """
    ACA Standards categories.

    Reference: ACA Performance-Based Standards for Adult Correctional Institutions.
    Each category addresses a key area of correctional operations.
    """
    SAFETY = "SAFETY"                   # Fire safety, emergency procedures
    SECURITY = "SECURITY"               # Security operations, contraband control
    ORDER = "ORDER"                     # Facility order, discipline
    CARE = "CARE"                       # Healthcare, sanitation, food service
    PROGRAMS = "PROGRAMS"               # Educational, vocational, treatment programs
    JUSTICE = "JUSTICE"                 # Inmate rights, grievances, due process
    ADMINISTRATION = "ADMINISTRATION"   # Management, training, records
    PHYSICAL_PLANT = "PHYSICAL_PLANT"   # Facility maintenance, conditions


class AuditType(str, Enum):
    """
    Types of compliance audits.

    Self-assessments are internal, official audits are by ACA auditors.
    """
    SELF_ASSESSMENT = "SELF_ASSESSMENT" # Internal self-evaluation
    MOCK_AUDIT = "MOCK_AUDIT"           # Practice audit before official
    OFFICIAL_AUDIT = "OFFICIAL_AUDIT"   # Official ACA accreditation audit


class AuditStatus(str, Enum):
    """
    Status of a compliance audit.

    Workflow: SCHEDULED → IN_PROGRESS → COMPLETED → SUBMITTED
    """
    SCHEDULED = "SCHEDULED"     # Audit planned
    IN_PROGRESS = "IN_PROGRESS" # Audit underway
    COMPLETED = "COMPLETED"     # Audit finished, report ready
    SUBMITTED = "SUBMITTED"     # Report submitted to ACA


class ComplianceStatus(str, Enum):
    """
    Compliance status for individual standards.

    Determines if corrective action is needed.
    """
    COMPLIANT = "COMPLIANT"           # Meets standard requirements
    NON_COMPLIANT = "NON_COMPLIANT"   # Does not meet standard
    PARTIAL = "PARTIAL"               # Partially compliant, needs improvement
    NOT_APPLICABLE = "NOT_APPLICABLE" # Standard does not apply to facility


# ============================================================================
# External Integration Enums (Phase 4)
# ============================================================================

class RequestType(str, Enum):
    """
    Types of external system integration requests.

    Reference: RBPF (Royal Bahamas Police Force) integration points.
    """
    INMATE_LOOKUP = "INMATE_LOOKUP"               # Look up person by NIB number
    WARRANT_CHECK = "WARRANT_CHECK"               # Check for active warrants
    CRIMINAL_HISTORY = "CRIMINAL_HISTORY"         # Retrieve criminal history
    BOOKING_NOTIFICATION = "BOOKING_NOTIFICATION" # Notify RBPF of new booking
    RELEASE_NOTIFICATION = "RELEASE_NOTIFICATION" # Notify RBPF of release


class IntegrationStatus(str, Enum):
    """
    Status of external integration requests.

    Tracks the lifecycle of API calls to external systems.
    """
    PENDING = "PENDING"     # Request initiated, awaiting response
    SUCCESS = "SUCCESS"     # Request completed successfully
    FAILED = "FAILED"       # Request failed (error from external system)
    TIMEOUT = "TIMEOUT"     # Request timed out


# ============================================================================
# Reports Module Enums (Phase 4)
# ============================================================================

class ReportCategory(str, Enum):
    """
    Categories of reports in BDOCS.

    Organizes reports by functional area for navigation.
    """
    POPULATION = "POPULATION"       # Inmate count, demographics, housing
    INCIDENT = "INCIDENT"           # Security incidents, use of force
    PROGRAMME = "PROGRAMME"         # Rehabilitation programs, BTVI
    HEALTHCARE = "HEALTHCARE"       # Medical stats, medication compliance
    COMPLIANCE = "COMPLIANCE"       # ACA compliance, audit results
    FINANCIAL = "FINANCIAL"         # Costs, budgets, commissary
    OPERATIONAL = "OPERATIONAL"     # Staff, shifts, visitation


class OutputFormat(str, Enum):
    """
    Supported report output formats.

    Each format serves different use cases.
    """
    PDF = "PDF"         # Printable, formal reports
    EXCEL = "EXCEL"     # Data analysis, spreadsheets
    CSV = "CSV"         # Data export, integration
    JSON = "JSON"       # API consumption, automation


class ReportStatus(str, Enum):
    """
    Status of report generation execution.

    Workflow: QUEUED → GENERATING → COMPLETED/FAILED
    """
    QUEUED = "QUEUED"           # In queue, waiting to start
    GENERATING = "GENERATING"   # Currently being generated
    COMPLETED = "COMPLETED"     # Successfully generated
    FAILED = "FAILED"           # Generation failed
