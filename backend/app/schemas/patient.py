"""Patient profile schemas for creation, update, and representation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PatientProfileBase(BaseModel):
    """Base patient profile attributes."""
    display_name: str = Field(..., min_length=1, max_length=100, description="Name or pseudonymous label for profile")
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Birth date in YYYY-MM-DD format")
    sex: Optional[str] = Field(None, description="Sex assigned at birth or clinical gender ('male', 'female', 'other')")
    blood_group: Optional[str] = Field(None, description="Blood group (e.g., 'A+', 'O-', 'B+')")
    preferred_language: str = Field(default="en", description="Preferred output language code for this patient")


class PatientProfileCreate(PatientProfileBase):
    """Payload to create a new patient profile.
    
    Notice owner_user_id is NOT accepted here: it is strictly injected from
    the authenticated user session to preserve ownership and isolation.
    """
    pass


class PatientProfileUpdate(BaseModel):
    """Payload to update an existing patient profile."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    sex: Optional[str] = None
    blood_group: Optional[str] = None
    preferred_language: Optional[str] = None


class PatientProfileOut(PatientProfileBase):
    """Public patient profile schema."""
    id: str = Field(..., description="Unique profile identifier")
    owner_user_id: str = Field(..., description="ID of the user who owns this patient profile")
    status: str = Field(default="active", description="Profile status ('active', 'archived')")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
