"""Persistent conversational medical memory & context endpoints.

Enables capturing structured facts from conversations, reviewing candidate facts,
confirming ambiguous facts, correcting medical memory, and configuring memory preferences.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import verify_patient_access, to_object_id
from app.database.mongodb import get_database
from app.services.context_extractor import context_extractor
from app.schemas.medical_record import (
    FactType,
    RecordStatus,
    SourceType,
    PatientContextFactCreate,
    PatientContextFactUpdate,
    PatientContextFactOut,
    MemoryPreferenceUpdate,
)

router = APIRouter()


class CaptureRequest(BaseModel):
    """Payload to capture facts from a natural-language statement."""
    statement: str = Field(..., min_length=2, max_length=1000, description="Patient's conversational statement.")


class CaptureResponse(BaseModel):
    """Response containing extracted candidate facts and memory status."""
    memory_enabled: bool
    status: str
    message: str
    facts_captured: int
    facts: List[PatientContextFactOut]


@router.post(
    "/{patient_id}/context/capture",
    response_model=CaptureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Capture Medical Facts from Conversation",
    description="Extracts candidate medical facts from patient statements and persists them with provenance.",
)
async def capture_context_facts(
    payload: CaptureRequest,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> CaptureResponse:
    """Extract candidate medical facts and save to patient_context_facts."""
    patient_id_str = str(patient["_id"])
    owner_id_str = patient["owner_user_id"]
    memory_enabled = patient.get("memory_enabled", True)

    # Check if persistent memory is enabled for this patient
    if not memory_enabled:
        return CaptureResponse(
            memory_enabled=False,
            status="disabled",
            message="Persistent medical memory is currently disabled for this patient profile.",
            facts_captured=0,
            facts=[],
        )

    # Extract candidate facts using rule-based clinical extractor
    extracted_candidates = context_extractor.extract_candidate_facts(payload.statement)
    if not extracted_candidates:
        return CaptureResponse(
            memory_enabled=True,
            status="no_facts_found",
            message="No structured medical facts were identified in the statement.",
            facts_captured=0,
            facts=[],
        )

    saved_facts = []
    now = datetime.now(timezone.utc)

    for cand in extracted_candidates:
        doc = {
            "patient_id": patient_id_str,
            "owner_user_id": owner_id_str,
            "fact_type": cand["fact_type"],
            "original_statement_excerpt": cand["original_statement_excerpt"],
            "normalized_fact": cand["normalized_fact"],
            "source_type": SourceType.CONVERSATION,
            "effective_date": cand.get("effective_date"),
            "record_status": RecordStatus.PATIENT_REPORTED,
            "confidence": cand.get("confidence", 1.0),
            "needs_confirmation": cand.get("needs_confirmation", False),
            "created_at": now,
            "updated_at": now,
        }

        res = await db.patient_context_facts.insert_one(doc)
        saved_facts.append(
            PatientContextFactOut(
                id=str(res.inserted_id),
                patient_id=doc["patient_id"],
                owner_user_id=doc["owner_user_id"],
                fact_type=doc["fact_type"],
                original_statement_excerpt=doc["original_statement_excerpt"],
                normalized_fact=doc["normalized_fact"],
                source_type=doc["source_type"],
                effective_date=doc["effective_date"],
                record_status=doc["record_status"],
                confidence=doc["confidence"],
                needs_confirmation=doc["needs_confirmation"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
        )

    return CaptureResponse(
        memory_enabled=True,
        status="captured",
        message=f"Successfully extracted and saved {len(saved_facts)} candidate medical fact(s).",
        facts_captured=len(saved_facts),
        facts=saved_facts,
    )


@router.post(
    "/{patient_id}/context",
    response_model=PatientContextFactOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Context Fact Manually",
    description="Directly creates a structured medical context fact with provenance.",
)
async def create_context_fact(
    fact_in: PatientContextFactCreate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PatientContextFactOut:
    """Manually record a structured medical context fact."""
    now = datetime.now(timezone.utc)
    patient_id_str = str(patient["_id"])
    owner_id_str = patient["owner_user_id"]

    doc = {
        "patient_id": patient_id_str,
        "owner_user_id": owner_id_str,
        "fact_type": fact_in.fact_type,
        "original_statement_excerpt": fact_in.original_statement_excerpt,
        "normalized_fact": fact_in.normalized_fact,
        "source_type": fact_in.source_type,
        "effective_date": fact_in.effective_date,
        "record_status": fact_in.record_status,
        "confidence": fact_in.confidence,
        "needs_confirmation": fact_in.needs_confirmation,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.patient_context_facts.insert_one(doc)
    return PatientContextFactOut(
        id=str(res.inserted_id),
        patient_id=doc["patient_id"],
        owner_user_id=doc["owner_user_id"],
        fact_type=doc["fact_type"],
        original_statement_excerpt=doc["original_statement_excerpt"],
        normalized_fact=doc["normalized_fact"],
        source_type=doc["source_type"],
        effective_date=doc["effective_date"],
        record_status=doc["record_status"],
        confidence=doc["confidence"],
        needs_confirmation=doc["needs_confirmation"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get(
    "/{patient_id}/context",
    response_model=List[PatientContextFactOut],
    status_code=status.HTTP_200_OK,
    summary="List Saved Context Facts",
    description="Retrieves persistent medical context facts for the authorized patient.",
)
async def list_context_facts(
    patient: Dict[str, Any] = Depends(verify_patient_access),
    fact_type: Optional[FactType] = Query(None, description="Filter by fact type"),
    needs_confirmation: Optional[bool] = Query(None, description="Filter by confirmation status"),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[PatientContextFactOut]:
    """List medical context facts with optional filters."""
    query: Dict[str, Any] = {
        "patient_id": str(patient["_id"]),
        "record_status": {"$ne": RecordStatus.DELETED.value},
    }

    if fact_type:
        query["fact_type"] = fact_type.value
    if needs_confirmation is not None:
        query["needs_confirmation"] = needs_confirmation

    cursor = db.patient_context_facts.find(query).sort("created_at", -1)
    facts = []
    async for doc in cursor:
        facts.append(
            PatientContextFactOut(
                id=str(doc["_id"]),
                patient_id=doc["patient_id"],
                owner_user_id=doc["owner_user_id"],
                fact_type=doc["fact_type"],
                original_statement_excerpt=doc["original_statement_excerpt"],
                normalized_fact=doc["normalized_fact"],
                source_type=doc["source_type"],
                effective_date=doc.get("effective_date"),
                record_status=doc["record_status"],
                confidence=doc.get("confidence", 1.0),
                needs_confirmation=doc.get("needs_confirmation", False),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
        )
    return facts


@router.post(
    "/{patient_id}/context/{fact_id}/confirm",
    response_model=PatientContextFactOut,
    status_code=status.HTTP_200_OK,
    summary="Confirm Candidate Fact",
    description="Confirms an unverified or ambiguous fact, promoting it to user_confirmed.",
)
async def confirm_context_fact(
    fact_id: str,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PatientContextFactOut:
    """Promote candidate fact to user_confirmed."""
    obj_id = to_object_id(fact_id)
    if not obj_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    fact = await db.patient_context_facts.find_one({
        "_id": obj_id,
        "patient_id": str(patient["_id"]),
    })
    if not fact or fact.get("record_status") == RecordStatus.DELETED.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    now = datetime.now(timezone.utc)
    await db.patient_context_facts.update_one(
        {"_id": obj_id},
        {"$set": {
            "record_status": RecordStatus.USER_CONFIRMED.value,
            "needs_confirmation": False,
            "updated_at": now,
        }}
    )

    updated_doc = await db.patient_context_facts.find_one({"_id": obj_id})
    return PatientContextFactOut(
        id=str(updated_doc["_id"]),
        patient_id=updated_doc["patient_id"],
        owner_user_id=updated_doc["owner_user_id"],
        fact_type=updated_doc["fact_type"],
        original_statement_excerpt=updated_doc["original_statement_excerpt"],
        normalized_fact=updated_doc["normalized_fact"],
        source_type=updated_doc["source_type"],
        effective_date=updated_doc.get("effective_date"),
        record_status=updated_doc["record_status"],
        confidence=updated_doc.get("confidence", 1.0),
        needs_confirmation=updated_doc.get("needs_confirmation", False),
        created_at=updated_doc["created_at"],
        updated_at=updated_doc["updated_at"],
    )


@router.patch(
    "/{patient_id}/context/{fact_id}",
    response_model=PatientContextFactOut,
    status_code=status.HTTP_200_OK,
    summary="Correct Saved Fact",
    description="Updates or corrects a saved persistent context fact.",
)
async def update_context_fact(
    fact_id: str,
    update_in: PatientContextFactUpdate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PatientContextFactOut:
    """Correct or update a saved medical fact."""
    obj_id = to_object_id(fact_id)
    if not obj_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    fact = await db.patient_context_facts.find_one({
        "_id": obj_id,
        "patient_id": str(patient["_id"]),
    })
    if not fact or fact.get("record_status") == RecordStatus.DELETED.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    update_fields = update_in.model_dump(exclude_unset=True)
    if not update_fields:
        return PatientContextFactOut(
            id=str(fact["_id"]),
            patient_id=fact["patient_id"],
            owner_user_id=fact["owner_user_id"],
            fact_type=fact["fact_type"],
            original_statement_excerpt=fact["original_statement_excerpt"],
            normalized_fact=fact["normalized_fact"],
            source_type=fact["source_type"],
            effective_date=fact.get("effective_date"),
            record_status=fact["record_status"],
            confidence=fact.get("confidence", 1.0),
            needs_confirmation=fact.get("needs_confirmation", False),
            created_at=fact["created_at"],
            updated_at=fact["updated_at"],
        )

    # Convert enums to string values for MongoDB
    if "record_status" in update_fields and isinstance(update_fields["record_status"], RecordStatus):
        update_fields["record_status"] = update_fields["record_status"].value

    now = datetime.now(timezone.utc)
    update_fields["updated_at"] = now

    await db.patient_context_facts.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    updated_doc = await db.patient_context_facts.find_one({"_id": obj_id})
    return PatientContextFactOut(
        id=str(updated_doc["_id"]),
        patient_id=updated_doc["patient_id"],
        owner_user_id=updated_doc["owner_user_id"],
        fact_type=updated_doc["fact_type"],
        original_statement_excerpt=updated_doc["original_statement_excerpt"],
        normalized_fact=updated_doc["normalized_fact"],
        source_type=updated_doc["source_type"],
        effective_date=updated_doc.get("effective_date"),
        record_status=updated_doc["record_status"],
        confidence=updated_doc.get("confidence", 1.0),
        needs_confirmation=updated_doc.get("needs_confirmation", False),
        created_at=updated_doc["created_at"],
        updated_at=updated_doc["updated_at"],
    )


@router.delete(
    "/{patient_id}/context/{fact_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Saved Fact",
    description="Soft-deletes a medical context fact from active memory.",
)
async def delete_context_fact(
    fact_id: str,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """Soft-delete context fact."""
    obj_id = to_object_id(fact_id)
    if not obj_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    fact = await db.patient_context_facts.find_one({
        "_id": obj_id,
        "patient_id": str(patient["_id"]),
    })
    if not fact or fact.get("record_status") == RecordStatus.DELETED.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")

    now = datetime.now(timezone.utc)
    await db.patient_context_facts.update_one(
        {"_id": obj_id},
        {"$set": {
            "record_status": RecordStatus.DELETED.value,
            "updated_at": now,
        }}
    )

    return {"status": "success", "message": "Medical context fact successfully removed."}


@router.get(
    "/{patient_id}/memory-settings",
    status_code=status.HTTP_200_OK,
    summary="Get Memory Preferences",
    description="Retrieves persistent conversational medical memory settings for a patient profile.",
)
async def get_memory_preference(
    patient: Dict[str, Any] = Depends(verify_patient_access),
) -> Dict[str, Any]:
    """Retrieve memory preference status for patient."""
    return {
        "patient_id": str(patient["_id"]),
        "memory_enabled": patient.get("memory_enabled", True),
    }


@router.patch(
    "/{patient_id}/memory-settings",
    status_code=status.HTTP_200_OK,
    summary="Update Memory Preferences",
    description="Enables or disables persistent conversational medical memory for a patient profile.",
)
async def update_memory_preference(
    pref_in: MemoryPreferenceUpdate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """Toggle persistent medical memory on or off."""
    now = datetime.now(timezone.utc)
    await db.patient_profiles.update_one(
        {"_id": patient["_id"]},
        {"$set": {
            "memory_enabled": pref_in.memory_enabled,
            "updated_at": now,
        }}
    )

    return {
        "patient_id": str(patient["_id"]),
        "memory_enabled": pref_in.memory_enabled,
        "message": f"Persistent medical memory is now {'enabled' if pref_in.memory_enabled else 'disabled'}.",
    }
