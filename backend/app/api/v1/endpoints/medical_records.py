"""Medical records endpoints for manual entry and historical timelines."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import verify_patient_access, to_object_id
from app.database.mongodb import get_database
from app.schemas.medical_record import (
    LabResultCreate,
    LabResultOut,
    SymptomCreate,
    SymptomOut,
    ConditionCreate,
    ConditionOut,
    MedicationCreate,
    MedicationOut,
    RecordStatus,
    SourceType,
)

router = APIRouter()


# ==============================================================================
# Laboratory Measurements
# ==============================================================================

@router.post(
    "/{patient_id}/labs",
    response_model=LabResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add Laboratory Measurement",
    description="Manually records a validated lab measurement for an authorized patient.",
)
async def create_lab_result(
    lab_in: LabResultCreate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> LabResultOut:
    """Record a lab result with provenance."""
    now = datetime.now(timezone.utc)
    patient_id_str = str(patient["_id"])

    doc = {
        "patient_id": patient_id_str,
        "owner_user_id": patient["owner_user_id"],
        "original_test_name": lab_in.original_test_name,
        "normalized_test_code": lab_in.normalized_test_code,
        "value": lab_in.value,
        "unit": lab_in.unit,
        "reference_range": lab_in.reference_range,
        "collected_at": lab_in.collected_at,
        "source_type": lab_in.source_type,
        "verification_status": RecordStatus.USER_CONFIRMED,
        "notes": lab_in.notes,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.lab_results.insert_one(doc)

    return LabResultOut(
        id=str(result.inserted_id),
        patient_id=doc["patient_id"],
        original_test_name=doc["original_test_name"],
        normalized_test_code=doc["normalized_test_code"],
        value=doc["value"],
        unit=doc["unit"],
        reference_range=doc["reference_range"],
        collected_at=doc["collected_at"],
        source_type=doc["source_type"],
        verification_status=doc["verification_status"],
        created_at=doc["created_at"],
    )


@router.get(
    "/{patient_id}/labs",
    response_model=List[LabResultOut],
    status_code=status.HTTP_200_OK,
    summary="List Laboratory Measurements",
    description="Retrieves all recorded lab measurements for an authorized patient.",
)
async def list_lab_results(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[LabResultOut]:
    """List lab measurements for patient."""
    cursor = db.lab_results.find({"patient_id": str(patient["_id"])})
    results = []
    async for doc in cursor:
        results.append(
            LabResultOut(
                id=str(doc["_id"]),
                patient_id=doc["patient_id"],
                original_test_name=doc["original_test_name"],
                normalized_test_code=doc.get("normalized_test_code"),
                value=doc["value"],
                unit=doc["unit"],
                reference_range=doc.get("reference_range"),
                collected_at=doc.get("collected_at"),
                source_type=doc["source_type"],
                verification_status=doc["verification_status"],
                created_at=doc["created_at"],
            )
        )
    return results


# ==============================================================================
# Symptoms
# ==============================================================================

@router.post(
    "/{patient_id}/symptoms",
    response_model=SymptomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add Symptom Record",
)
async def create_symptom(
    symptom_in: SymptomCreate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SymptomOut:
    """Record a patient symptom."""
    now = datetime.now(timezone.utc)
    doc = {
        "patient_id": str(patient["_id"]),
        "owner_user_id": patient["owner_user_id"],
        "symptom_name": symptom_in.symptom_name,
        "severity": symptom_in.severity,
        "onset_date": symptom_in.onset_date,
        "is_active": symptom_in.is_active,
        "source_type": symptom_in.source_type,
        "verification_status": RecordStatus.PATIENT_REPORTED,
        "notes": symptom_in.notes,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.symptoms.insert_one(doc)

    return SymptomOut(
        id=str(result.inserted_id),
        patient_id=doc["patient_id"],
        symptom_name=doc["symptom_name"],
        severity=doc["severity"],
        onset_date=doc["onset_date"],
        is_active=doc["is_active"],
        source_type=doc["source_type"],
        verification_status=doc["verification_status"],
        created_at=doc["created_at"],
    )


@router.get(
    "/{patient_id}/symptoms",
    response_model=List[SymptomOut],
    status_code=status.HTTP_200_OK,
    summary="List Symptoms",
)
async def list_symptoms(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[SymptomOut]:
    """List symptoms for patient."""
    cursor = db.symptoms.find({"patient_id": str(patient["_id"])})
    results = []
    async for doc in cursor:
        results.append(
            SymptomOut(
                id=str(doc["_id"]),
                patient_id=doc["patient_id"],
                symptom_name=doc["symptom_name"],
                severity=doc.get("severity"),
                onset_date=doc.get("onset_date"),
                is_active=doc.get("is_active", True),
                source_type=doc["source_type"],
                verification_status=doc["verification_status"],
                created_at=doc["created_at"],
            )
        )
    return results


# ==============================================================================
# Conditions
# ==============================================================================

@router.post(
    "/{patient_id}/conditions",
    response_model=ConditionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add Condition History",
)
async def create_condition(
    condition_in: ConditionCreate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ConditionOut:
    """Record a diagnosed or known condition."""
    now = datetime.now(timezone.utc)
    doc = {
        "patient_id": str(patient["_id"]),
        "owner_user_id": patient["owner_user_id"],
        "condition_name": condition_in.condition_name,
        "diagnosed_date": condition_in.diagnosed_date,
        "is_active": condition_in.is_active,
        "source_type": condition_in.source_type,
        "verification_status": RecordStatus.USER_CONFIRMED,
        "notes": condition_in.notes,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.conditions.insert_one(doc)

    return ConditionOut(
        id=str(result.inserted_id),
        patient_id=doc["patient_id"],
        condition_name=doc["condition_name"],
        diagnosed_date=doc["diagnosed_date"],
        is_active=doc["is_active"],
        source_type=doc["source_type"],
        verification_status=doc["verification_status"],
        created_at=doc["created_at"],
    )


@router.get(
    "/{patient_id}/conditions",
    response_model=List[ConditionOut],
    status_code=status.HTTP_200_OK,
    summary="List Conditions",
)
async def list_conditions(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[ConditionOut]:
    """List conditions for patient."""
    cursor = db.conditions.find({"patient_id": str(patient["_id"])})
    results = []
    async for doc in cursor:
        results.append(
            ConditionOut(
                id=str(doc["_id"]),
                patient_id=doc["patient_id"],
                condition_name=doc["condition_name"],
                diagnosed_date=doc.get("diagnosed_date"),
                is_active=doc.get("is_active", True),
                source_type=doc["source_type"],
                verification_status=doc["verification_status"],
                created_at=doc["created_at"],
            )
        )
    return results


# ==============================================================================
# Medications
# ==============================================================================

@router.post(
    "/{patient_id}/medications",
    response_model=MedicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add Medication Record",
)
async def create_medication(
    med_in: MedicationCreate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> MedicationOut:
    """Record a medication with dosage and frequency."""
    now = datetime.now(timezone.utc)
    doc = {
        "patient_id": str(patient["_id"]),
        "owner_user_id": patient["owner_user_id"],
        "medication_name": med_in.medication_name,
        "dosage": med_in.dosage,
        "frequency": med_in.frequency,
        "start_date": med_in.start_date,
        "is_current": med_in.is_current,
        "source_type": med_in.source_type,
        "verification_status": RecordStatus.USER_CONFIRMED,
        "notes": med_in.notes,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.medications.insert_one(doc)

    return MedicationOut(
        id=str(result.inserted_id),
        patient_id=doc["patient_id"],
        medication_name=doc["medication_name"],
        dosage=doc["dosage"],
        frequency=doc["frequency"],
        start_date=doc["start_date"],
        is_current=doc["is_current"],
        source_type=doc["source_type"],
        verification_status=doc["verification_status"],
        created_at=doc["created_at"],
    )


@router.get(
    "/{patient_id}/medications",
    response_model=List[MedicationOut],
    status_code=status.HTTP_200_OK,
    summary="List Medications",
)
async def list_medications(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[MedicationOut]:
    """List medications for patient."""
    cursor = db.medications.find({"patient_id": str(patient["_id"])})
    results = []
    async for doc in cursor:
        results.append(
            MedicationOut(
                id=str(doc["_id"]),
                patient_id=doc["patient_id"],
                medication_name=doc["medication_name"],
                dosage=doc.get("dosage"),
                frequency=doc.get("frequency"),
                start_date=doc.get("start_date"),
                is_current=doc.get("is_current", True),
                source_type=doc["source_type"],
                verification_status=doc["verification_status"],
                created_at=doc["created_at"],
            )
        )
    return results


# ==============================================================================
# Comprehensive Patient Medical History
# ==============================================================================

@router.get(
    "/{patient_id}/history",
    status_code=status.HTTP_200_OK,
    summary="Unified Patient History",
    description="Returns an aggregated timeline of all labs, symptoms, conditions, medications, and confirmed memory facts.",
)
async def get_patient_history(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """Aggregate all historical medical records for patient."""
    patient_id_str = str(patient["_id"])

    # Query all collections
    labs = await db.lab_results.find({"patient_id": patient_id_str}).to_list(100)
    symptoms = await db.symptoms.find({"patient_id": patient_id_str}).to_list(100)
    conditions = await db.conditions.find({"patient_id": patient_id_str}).to_list(100)
    medications = await db.medications.find({"patient_id": patient_id_str}).to_list(100)
    facts = await db.patient_context_facts.find({
        "patient_id": patient_id_str,
        "record_status": {"$ne": RecordStatus.DELETED.value}
    }).to_list(100)

    # Format IDs
    def format_docs(docs):
        out = []
        for d in docs:
            d_copy = dict(d)
            d_copy["id"] = str(d_copy.pop("_id"))
            out.append(d_copy)
        return out

    return {
        "patient_id": patient_id_str,
        "patient_name": patient["display_name"],
        "counts": {
            "labs": len(labs),
            "symptoms": len(symptoms),
            "conditions": len(conditions),
            "medications": len(medications),
            "context_facts": len(facts),
        },
        "labs": format_docs(labs),
        "symptoms": format_docs(symptoms),
        "conditions": format_docs(conditions),
        "medications": format_docs(medications),
        "context_facts": format_docs(facts),
    }
