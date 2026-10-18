"""Medical record and persistent context schemas.

Defines data models for lab results, symptoms, conditions, medications,
and persistent conversational medical memory facts with strict provenance tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """Provenance origin of medical information."""
    MANUAL = "manual"
    CONVERSATION = "conversation"
    REPORT_PDF_TEXT = "report_pdf_text"
    REPORT_OCR = "report_ocr"
    IMPORT = "import"


class RecordStatus(str, Enum):
    """Verification and lifecycle status of a medical record."""
    PATIENT_REPORTED = "patient_reported"
    EXTRACTED_UNVERIFIED = "extracted_unverified"
    USER_CONFIRMED = "user_confirmed"
    CLINICIAN_VERIFIED = "clinician_verified"
    SUPERSEDED = "superseded"
    DELETED = "deleted"


class FactType(str, Enum):
    """Categories of persistent patient context facts."""
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    CONDITION = "condition"
    ALLERGY = "allergy"
    LAB_MEASUREMENT = "lab_measurement"
    HISTORICAL_EVENT = "historical_event"


# ==============================================================================
# Persistent Medical Memory Context Schemas (Section 11.8)
# ==============================================================================

class PatientContextFactCreate(BaseModel):
    """Payload to record a persistent medical fact from conversation or input."""
    fact_type: FactType = Field(..., description="Category of the fact")
    original_statement_excerpt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The minimally sufficient excerpt of what the user stated."
    )
    normalized_fact: Dict[str, Any] = Field(
        ...,
        description="Structured key-value representation of the fact (e.g., {'name': 'Metformin', 'dose': '500mg'})."
    )
    source_type: SourceType = Field(
        default=SourceType.CONVERSATION,
        description="Provenance of the fact."
    )
    effective_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$",
        description="Date or year the fact applies to (e.g. '2021' or '2021-06-15')."
    )
    record_status: RecordStatus = Field(
        default=RecordStatus.PATIENT_REPORTED,
        description="Verification status of the fact."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0.0 to 1.0)."
    )
    needs_confirmation: bool = Field(
        default=False,
        description="Whether this fact has ambiguity and requires user confirmation."
    )


class PatientContextFactUpdate(BaseModel):
    """Payload to update or correct a saved persistent context fact."""
    normalized_fact: Optional[Dict[str, Any]] = None
    effective_date: Optional[str] = Field(None, pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")
    record_status: Optional[RecordStatus] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated confidence score.")
    needs_confirmation: Optional[bool] = None


class PatientContextFactOut(BaseModel):
    """Public representation of a saved persistent medical context fact."""
    id: str
    patient_id: str
    owner_user_id: str
    fact_type: FactType
    original_statement_excerpt: str
    normalized_fact: Dict[str, Any]
    source_type: SourceType
    effective_date: Optional[str] = None
    record_status: RecordStatus
    confidence: float
    needs_confirmation: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryPreferenceUpdate(BaseModel):
    """Settings to enable or disable persistent conversational medical memory."""
    memory_enabled: bool = Field(
        ...,
        description="If True, relevant medical facts mentioned in conversation are saved for this patient."
    )


# ==============================================================================
# Laboratory Measurement Schemas (Section 11.4)
# ==============================================================================

class LabResultCreate(BaseModel):
    """Payload for manual entry or extracted lab measurement."""
    original_test_name: str = Field(..., min_length=1, max_length=150, description="Test name as stated (e.g. 'Fasting Blood Sugar')")
    normalized_test_code: Optional[str] = Field(None, description="Standardized code (e.g. 'GLUCOSE_FASTING')")
    value: float = Field(..., description="Numeric value of the measurement")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement (e.g. 'mg/dL', 'mmol/L')")
    reference_range: Optional[str] = Field(None, max_length=100, description="Applicable lab reference range (e.g. '70-99')")
    collected_at: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Specimen collection date (YYYY-MM-DD)")
    source_type: SourceType = Field(default=SourceType.MANUAL)
    notes: Optional[str] = None


class LabResultOut(BaseModel):
    """Public representation of a structured lab measurement."""
    id: str
    patient_id: str
    original_test_name: str
    normalized_test_code: Optional[str] = None
    value: float
    unit: str
    reference_range: Optional[str] = None
    collected_at: Optional[str] = None
    source_type: SourceType
    verification_status: RecordStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Symptom & Condition Schemas (Section 11.5 & 11.6)
# ==============================================================================

class SymptomCreate(BaseModel):
    """Payload to record a patient symptom."""
    symptom_name: str = Field(..., min_length=1, max_length=150, description="Name of the symptom (e.g. 'Shortness of breath')")
    severity: Optional[str] = Field(None, description="Severity rating (e.g. 'mild', 'moderate', 'severe')")
    onset_date: Optional[str] = Field(None, pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")
    is_active: bool = Field(default=True, description="Whether the symptom is currently experienced")
    source_type: SourceType = Field(default=SourceType.MANUAL)
    notes: Optional[str] = None


class SymptomOut(BaseModel):
    """Public representation of a symptom record."""
    id: str
    patient_id: str
    symptom_name: str
    severity: Optional[str] = None
    onset_date: Optional[str] = None
    is_active: bool
    source_type: SourceType
    verification_status: RecordStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConditionCreate(BaseModel):
    """Payload to record a diagnosed or reported medical condition."""
    condition_name: str = Field(..., min_length=1, max_length=150, description="Condition name (e.g. 'Hypertension')")
    diagnosed_date: Optional[str] = Field(None, pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")
    is_active: bool = Field(default=True)
    source_type: SourceType = Field(default=SourceType.MANUAL)
    notes: Optional[str] = None


class ConditionOut(BaseModel):
    """Public representation of a condition record."""
    id: str
    patient_id: str
    condition_name: str
    diagnosed_date: Optional[str] = None
    is_active: bool
    source_type: SourceType
    verification_status: RecordStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Medication Schemas (Section 11.7)
# ==============================================================================

class MedicationCreate(BaseModel):
    """Payload to record a medication."""
    medication_name: str = Field(..., min_length=1, max_length=150, description="Medication name (e.g. 'Metformin')")
    dosage: Optional[str] = Field(None, description="Strength/dose (e.g. '500 mg')")
    frequency: Optional[str] = Field(None, description="Dosing frequency (e.g. 'twice daily')")
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")
    is_current: bool = Field(default=True, description="Whether the patient is currently taking this medication")
    source_type: SourceType = Field(default=SourceType.MANUAL)
    notes: Optional[str] = None


class MedicationOut(BaseModel):
    """Public representation of a medication record."""
    id: str
    patient_id: str
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    is_current: bool
    source_type: SourceType
    verification_status: RecordStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
