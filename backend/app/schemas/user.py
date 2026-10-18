"""User schemas for registration, authentication, and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user attributes."""
    email: EmailStr = Field(..., description="Unique email address of the user")
    preferred_language: str = Field(default="en", description="Preferred ISO language code (e.g., 'en', 'hi')")


class UserCreate(UserBase):
    """Payload for user registration."""
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)")


class UserLogin(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")


class UserOut(UserBase):
    """Safe public user representation (never exposes password hash)."""
    id: str = Field(..., description="Unique user identifier")
    status: str = Field(default="active", description="Account status ('active', 'suspended')")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Bearer token response schema."""
    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """Decoded JWT payload content."""
    sub: Optional[str] = None
