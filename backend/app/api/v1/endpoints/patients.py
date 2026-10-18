"""Patient profile management endpoints with strict ownership enforcement."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, verify_patient_access, to_object_id
from app.database.mongodb import get_database
from app.schemas.patient import (
    PatientProfileCreate,
    PatientProfileUpdate,
    PatientProfileOut,
)

router = APIRouter()


@router.post(
    "",
    response_model=PatientProfileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Patient Profile",
    description="Creates a patient profile strictly associated with the authenticated user.",
)
async def create_patient(
    profile_in: PatientProfileCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PatientProfileOut:
    """Create a new patient profile owned by current user."""
    now = datetime.now(timezone.utc)
    owner_id_str = str(current_user["_id"])

    profile_doc = {
        "owner_user_id": owner_id_str,
        "display_name": profile_in.display_name,
        "date_of_birth": profile_in.date_of_birth,
        "sex": profile_in.sex,
        "blood_group": profile_in.blood_group,
        "preferred_language": profile_in.preferred_language,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }

    result = await db.patient_profiles.insert_one(profile_doc)

    return PatientProfileOut(
        id=str(result.inserted_id),
        owner_user_id=profile_doc["owner_user_id"],
        display_name=profile_doc["display_name"],
        date_of_birth=profile_doc["date_of_birth"],
        sex=profile_doc["sex"],
        blood_group=profile_doc["blood_group"],
        preferred_language=profile_doc["preferred_language"],
        status=profile_doc["status"],
        created_at=profile_doc["created_at"],
        updated_at=profile_doc["updated_at"],
    )


@router.get(
    "",
    response_model=List[PatientProfileOut],
    status_code=status.HTTP_200_OK,
    summary="List Patient Profiles",
    description="Returns all patient profiles authorized for the current user.",
)
async def list_patients(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> List[PatientProfileOut]:
    """List all patient profiles belonging to current user."""
    owner_id_str = str(current_user["_id"])
    cursor = db.patient_profiles.find({"owner_user_id": owner_id_str, "status": "active"})
    
    profiles = []
    async for doc in cursor:
        profiles.append(
            PatientProfileOut(
                id=str(doc["_id"]),
                owner_user_id=doc["owner_user_id"],
                display_name=doc["display_name"],
                date_of_birth=doc.get("date_of_birth"),
                sex=doc.get("sex"),
                blood_group=doc.get("blood_group"),
                preferred_language=doc.get("preferred_language", "en"),
                status=doc.get("status", "active"),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
        )
    return profiles


@router.get(
    "/{patient_id}",
    response_model=PatientProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Get Patient Profile",
    description="Retrieves a specific patient profile after verifying ownership access.",
)
async def get_patient(
    patient: Dict[str, Any] = Depends(verify_patient_access),
) -> PatientProfileOut:
    """Retrieve patient profile with verified ownership."""
    return PatientProfileOut(
        id=str(patient["_id"]),
        owner_user_id=patient["owner_user_id"],
        display_name=patient["display_name"],
        date_of_birth=patient.get("date_of_birth"),
        sex=patient.get("sex"),
        blood_group=patient.get("blood_group"),
        preferred_language=patient.get("preferred_language", "en"),
        status=patient.get("status", "active"),
        created_at=patient["created_at"],
        updated_at=patient["updated_at"],
    )


@router.patch(
    "/{patient_id}",
    response_model=PatientProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Update Patient Profile",
    description="Updates permitted fields on an existing patient profile.",
)
async def update_patient(
    update_in: PatientProfileUpdate,
    patient: Dict[str, Any] = Depends(verify_patient_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PatientProfileOut:
    """Update patient profile fields."""
    update_fields = update_in.model_dump(exclude_unset=True)
    if not update_fields:
        # Nothing to update, return existing
        return PatientProfileOut(
            id=str(patient["_id"]),
            owner_user_id=patient["owner_user_id"],
            display_name=patient["display_name"],
            date_of_birth=patient.get("date_of_birth"),
            sex=patient.get("sex"),
            blood_group=patient.get("blood_group"),
            preferred_language=patient.get("preferred_language", "en"),
            status=patient.get("status", "active"),
            created_at=patient["created_at"],
            updated_at=patient["updated_at"],
        )

    now = datetime.now(timezone.utc)
    update_fields["updated_at"] = now

    await db.patient_profiles.update_one(
        {"_id": patient["_id"]},
        {"$set": update_fields}
    )

    updated_doc = await db.patient_profiles.find_one({"_id": patient["_id"]})
    return PatientProfileOut(
        id=str(updated_doc["_id"]),
        owner_user_id=updated_doc["owner_user_id"],
        display_name=updated_doc["display_name"],
        date_of_birth=updated_doc.get("date_of_birth"),
        sex=updated_doc.get("sex"),
        blood_group=updated_doc.get("blood_group"),
        preferred_language=updated_doc.get("preferred_language", "en"),
        status=updated_doc.get("status", "active"),
        created_at=updated_doc["created_at"],
        updated_at=updated_doc["updated_at"],
    )
