"""Unit and integration tests for system health and root endpoints."""

import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Test that GET /api/v1/health returns HTTP 200 and expected schema."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project_name"] == "MediReport Analyzer"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    
    # Verify timestamp format is valid ISO 8601
    parsed_time = datetime.fromisoformat(data["timestamp"])
    assert parsed_time is not None


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test that GET / returns HTTP 200 and basic application info."""
    response = await client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "online"
    assert data["project"] == "MediReport Analyzer"
    assert "/docs" in data["documentation"]
