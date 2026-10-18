"""V1 API Router Aggregator.

Consolidates all v1 endpoint routers into a single master router.
As new domains (auth, patients, reports, comparisons) are implemented across
phases, their routers will be mounted here.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, patients

api_router = APIRouter()

# System
api_router.include_router(health.router, tags=["System Health"])

# Authentication & Users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Patient Profiles
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
