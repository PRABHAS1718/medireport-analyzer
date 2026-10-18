"""Health check endpoint.

Provides an operational check to verify the API service is up and healthy.
Used by automated test gates, container orchestrators, and monitoring probes.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Overall service status, typically 'healthy'")
    project_name: str = Field(..., description="Name of the service")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment")
    timestamp: str = Field(..., description="UTC ISO-formatted timestamp of the check")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns service status, environment, version, and UTC timestamp.",
)
async def check_health() -> HealthResponse:
    """Check service health and operational parameters."""
    return HealthResponse(
        status="healthy",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
