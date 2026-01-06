"""
Healthcare Management Models - Medical records and treatment tracking for BDOCS.

This module handles inmate medical records, encounters, and medication
administration with HIPAA-compliant data handling requirements.

HIPAA NOTE: All medical data requires role-based access control.
Only authorized medical staff should access these records.

Three core entities:
- MedicalRecord: Comprehensive health profile (one per inmate)
- MedicalEncounter: Individual medical visits/treatments
- MedicationAdministration: Medication scheduling and tracking
"""
from datetime import date, time, datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Date, Time, DateTime, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.async_db import AsyncBase
from src.models.mixins import UUIDMixin, AuditMixin
from src.common.enums import (
    BloodType, EncounterType, ProviderType,
    RouteType, MedAdminStatus
)


class MedicalRecord(AsyncBase, UUIDMixin, AuditMixin):
    """
    Inmate medical record - comprehensive health profile.

    One record per inmate, created during intake screening.
    Contains allergies, chronic conditions, medications, and
    special flags like mental health and suicide watch.

    HIPAA: This record contains Protected Health Information (PHI).
    Access must be restricted to authorized medical personnel.
    """
    __tablename__ = 'medical_records'

    # One-to-one with inmate
    inmate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    # Blood type
    blood_type: Mapped[Optional[BloodType]] = mapped_column(
        ENUM(BloodType, name='blood_type_enum', create_type=False),
        nullable=True
    )

    # Allergies - array of {allergen, severity, reaction}
    allergies: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {allergen, severity, reaction}"
    )

    # Chronic conditions - array of {condition, diagnosed_date, notes}
    chronic_conditions: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {condition, diagnosed_date, notes}"
    )

    # Current medications - array of {name, dosage, frequency, prescriber}
    current_medications: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {name, dosage, frequency, prescriber}"
    )

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )

    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Format: (242) XXX-XXXX"
    )

    # Physical examination schedule
    last_physical_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    next_physical_due: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Mental health flags - CRITICAL for safety
    mental_health_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Requires mental health monitoring"
    )

    suicide_watch: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="CRITICAL: Requires constant observation"
    )

    # Dietary restrictions - array of {type, details}
    dietary_restrictions: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {type, details} - medical or religious"
    )

    # Disability accommodations
    disability_accommodations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Required ADA accommodations"
    )

    # Created by (medical staff who performed intake)
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_medical_records_inmate', 'inmate_id'),
        Index('ix_medical_records_blood_type', 'blood_type'),
        Index('ix_medical_records_mental_health', 'mental_health_flag'),
        Index('ix_medical_records_suicide_watch', 'suicide_watch'),
        Index('ix_medical_records_next_physical', 'next_physical_due'),
    )

    # Relationships
    inmate = relationship(
        'Inmate',
        lazy='selectin'
    )

    creator = relationship(
        'User',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    encounters = relationship(
        'MedicalEncounter',
        back_populates='medical_record',
        lazy='selectin',
        cascade='all, delete-orphan',
        foreign_keys='MedicalEncounter.inmate_id',
        primaryjoin='MedicalRecord.inmate_id == MedicalEncounter.inmate_id'
    )

    def __repr__(self) -> str:
        flags = []
        if self.mental_health_flag:
            flags.append("MH")
        if self.suicide_watch:
            flags.append("SW")
        flag_str = f" [{','.join(flags)}]" if flags else ""
        return f"<MedicalRecord Inmate:{self.inmate_id}{flag_str}>"


class MedicalEncounter(AsyncBase, UUIDMixin, AuditMixin):
    """
    Medical encounter - individual medical visit or treatment.

    Records each interaction between inmate and healthcare provider,
    including chief complaint, vitals, diagnosis, and treatment.

    HIPAA: Contains Protected Health Information (PHI).
    """
    __tablename__ = 'medical_encounters'

    # Inmate reference
    inmate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False
    )

    # Encounter details
    encounter_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    encounter_type: Mapped[EncounterType] = mapped_column(
        ENUM(EncounterType, name='encounter_type_enum', create_type=False),
        nullable=False
    )

    # Chief complaint
    chief_complaint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Patient's main reason for visit"
    )

    # Vitals - {bp, pulse, temp, weight, resp_rate, o2_sat}
    vitals: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Vital signs: bp, pulse, temp, weight, resp_rate, o2_sat"
    )

    # Clinical findings
    diagnosis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    treatment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Medications prescribed during this encounter
    medications_prescribed: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of {name, dosage, frequency, duration}"
    )

    # Follow-up
    follow_up_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    follow_up_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Provider information
    provider_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    provider_type: Mapped[ProviderType] = mapped_column(
        ENUM(ProviderType, name='provider_type_enum', create_type=False),
        nullable=False
    )

    # Location
    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Medical Unit",
        comment="Where encounter took place"
    )

    # External referral
    referred_external: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Referred to outside facility"
    )

    external_facility: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of external facility if referred"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Created by (provider who documented)
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )

    # Table indexes
    __table_args__ = (
        Index('ix_medical_encounters_inmate', 'inmate_id'),
        Index('ix_medical_encounters_date', 'encounter_date'),
        Index('ix_medical_encounters_type', 'encounter_type'),
        Index('ix_medical_encounters_provider_type', 'provider_type'),
        Index('ix_medical_encounters_follow_up', 'follow_up_date'),
        Index('ix_medical_encounters_external', 'referred_external'),
    )

    # Relationships
    inmate = relationship(
        'Inmate',
        lazy='selectin'
    )

    medical_record = relationship(
        'MedicalRecord',
        back_populates='encounters',
        foreign_keys=[inmate_id],
        primaryjoin='MedicalEncounter.inmate_id == MedicalRecord.inmate_id',
        lazy='selectin',
        viewonly=True
    )

    creator = relationship(
        'User',
        foreign_keys=[created_by],
        lazy='selectin'
    )

    def __repr__(self) -> str:
        return f"<MedicalEncounter {self.encounter_type.value} {self.encounter_date}>"


class MedicationAdministration(AsyncBase, UUIDMixin, AuditMixin):
    """
    Medication administration record.

    Tracks scheduled medications and their administration status.
    Refused medications MUST have a witness documented.

    HIPAA: Contains Protected Health Information (PHI).
    """
    __tablename__ = 'medication_administrations'

    # Inmate reference
    inmate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('inmates.id', ondelete='CASCADE'),
        nullable=False
    )

    # Medication details
    medication_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    dosage: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g., '500mg', '2 tablets'"
    )

    route: Mapped[RouteType] = mapped_column(
        ENUM(RouteType, name='route_type_enum', create_type=False),
        nullable=False,
        default=RouteType.ORAL
    )

    # Scheduling
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Administration
    administered_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    administered_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )

    # Status
    status: Mapped[MedAdminStatus] = mapped_column(
        ENUM(MedAdminStatus, name='med_admin_status_enum', create_type=False),
        nullable=False,
        default=MedAdminStatus.SCHEDULED
    )

    # Refusal documentation - REQUIRED if status is REFUSED
    refusal_witnessed_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Required if medication refused"
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Table indexes
    __table_args__ = (
        Index('ix_med_admin_inmate', 'inmate_id'),
        Index('ix_med_admin_scheduled', 'scheduled_time'),
        Index('ix_med_admin_status', 'status'),
        Index('ix_med_admin_medication', 'medication_name'),
        # Partial index for pending medications
        Index(
            'ix_med_admin_pending',
            'scheduled_time', 'status',
            postgresql_where='status = \'SCHEDULED\''
        ),
    )

    # Relationships
    inmate = relationship(
        'Inmate',
        lazy='selectin'
    )

    administrator = relationship(
        'User',
        foreign_keys=[administered_by],
        lazy='selectin'
    )

    refusal_witness = relationship(
        'User',
        foreign_keys=[refusal_witnessed_by],
        lazy='selectin'
    )

    def __repr__(self) -> str:
        return f"<MedicationAdministration {self.medication_name} {self.scheduled_time} [{self.status.value}]>"
