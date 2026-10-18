"""Authentication endpoints for user registration, login, and profile access."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.database.mongodb import get_database
from app.schemas.user import UserCreate, UserLogin, UserOut, Token

router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new user account with hashed password credentials.",
)
async def register_user(
    user_in: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserOut:
    """Register a new user account."""
    # Check if email is already registered
    existing_user = await db.users.find_one({"email": user_in.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    now = datetime.now(timezone.utc)
    user_doc = {
        "email": user_in.email.lower(),
        "password_hash": hash_password(user_in.password),
        "status": "active",
        "preferred_language": user_in.preferred_language,
        "created_at": now,
        "updated_at": now,
    }

    result = await db.users.insert_one(user_doc)
    
    return UserOut(
        id=str(result.inserted_id),
        email=user_doc["email"],
        preferred_language=user_doc["preferred_language"],
        status=user_doc["status"],
        created_at=user_doc["created_at"],
        updated_at=user_doc["updated_at"],
    )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates credentials and returns a signed JWT access token.",
)
async def login_user(
    user_in: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Token:
    """Authenticate and issue an access token."""
    user = await db.users.find_one({"email": user_in.email.lower()})
    if not user or not verify_password(user_in.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or suspended.",
        )

    access_token = create_access_token(subject=str(user["_id"]))
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
    description="Returns the profile details of the currently authenticated user.",
)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserOut:
    """Retrieve authenticated user details."""
    return UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        preferred_language=current_user.get("preferred_language", "en"),
        status=current_user.get("status", "active"),
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"],
    )
