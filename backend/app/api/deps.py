"""Dependency injection providers for authentication, database, and authorization.

Enforces patient ownership and security boundaries on every protected endpoint.
"""

from typing import Dict, Any, Optional
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token
from app.database.mongodb import get_database

security_bearer = HTTPBearer(auto_error=False)


def to_object_id(id_str: str) -> Optional[ObjectId]:
    """Safely converts a string to a BSON ObjectId, returning None if invalid."""
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """Validates the Bearer token and returns the authenticated user record.
    
    Raises:
        HTTPException(401): If token is missing, expired, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    obj_id = to_object_id(user_id)
    if not obj_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity in token is malformed.",
        )

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or suspended.",
        )

    return user


async def verify_patient_access(
    patient_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Dict[str, Any]:
    """Verifies that the requested patient profile exists AND belongs to the current user.
    
    Cross-user isolation rule:
    Returns HTTP 404 if the patient profile does not exist OR if it belongs to another user.
    Returning 404 instead of 403 prevents attackers from discovering the existence of
    another patient's ID through enumeration.
    """
    obj_id = to_object_id(patient_id)
    if not obj_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    patient = await db.patient_profiles.find_one({"_id": obj_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    # Strictly check ownership
    user_id_str = str(current_user["_id"])
    if str(patient.get("owner_user_id")) != user_id_str:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    return patient
