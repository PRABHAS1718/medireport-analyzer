"""Unit tests for medical record schemas and persistent context data models."""

import pytest
from pydantic import ValidationError
from app.schemas.medical_record import (
    SourceType,
    RecordStatus,
    FactType,
    PatientContextFactCreate,
    LabResultCreate,
    SymptomCreate,
    ConditionCreate,
    MedicationCreate,
)


def test_schema_valid_enums():
    """Verify that predefined domain enums match expected values."""
    assert SourceType.CONVERSATION == "conversation"
    assert SourceType.MANUAL == "manual"
    assert RecordStatus.PATIENT_REPORTED == "patient_reported"
    assert RecordStatus.USER_CONFIRMED == "user_confirmed"
    assert FactType.MEDICATION == "medication"
    assert FactType.SYMPTOM == "symptom"


def test_schema_patient_context_fact_valid():
    """Verify creating a valid persistent patient context fact."""
    fact = PatientContextFactCreate(
        fact_type=FactType.MEDICATION,
        original_statement_excerpt="Patient stated: taking Metformin 500mg daily since 2021",
        normalized_fact={"name": "Metformin", "dose": "500mg", "frequency": "once daily"},
        effective_date="2021",
        confidence=0.95,
        needs_confirmation=False,
    )
    assert fact.fact_type == FactType.MEDICATION
    assert fact.confidence == 0.95
    assert fact.source_type == SourceType.CONVERSATION


def test_schema_patient_context_fact_invalid_confidence():
    """Verify confidence must be bounded between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        PatientContextFactCreate(
            fact_type=FactType.SYMPTOM,
            original_statement_excerpt="Headaches",
            normalized_fact={"symptom": "Headache"},
            confidence=1.5,  # Invalid: > 1.0
        )


def test_schema_lab_result_validation():
    """Verify lab result schema accepts numeric values and enforces required fields."""
    lab = LabResultCreate(
        original_test_name="Fasting Blood Glucose",
        normalized_test_code="GLUCOSE_FASTING",
        value=115.5,
        unit="mg/dL",
        reference_range="70-99",
        collected_at="2026-03-10",
    )
    assert lab.value == 115.5
    assert lab.source_type == SourceType.MANUAL

    # Missing required unit
    with pytest.raises(ValidationError):
        LabResultCreate(
            original_test_name="Fasting Blood Glucose",
            value=115.5,
            unit="",  # Invalid: empty string
        )


def test_schema_flexible_date_patterns():
    """Verify date pattern accepts YYYY, YYYY-MM, or YYYY-MM-DD for historical context."""
    med1 = MedicationCreate(medication_name="Aspirin", start_date="2020")
    assert med1.start_date == "2020"

    med2 = MedicationCreate(medication_name="Aspirin", start_date="2020-05")
    assert med2.start_date == "2020-05"

    med3 = MedicationCreate(medication_name="Aspirin", start_date="2020-05-20")
    assert med3.start_date == "2020-05-20"

    # Invalid date pattern
    with pytest.raises(ValidationError):
        MedicationCreate(medication_name="Aspirin", start_date="May 2020")
