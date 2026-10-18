"""Pytest configuration and shared fixtures for backend testing.

Uses mongomock-motor for in-memory, fully isolated MongoDB testing.
Enables fast, offline test execution without modifying live databases.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.database.mongodb import get_database, mongo_manager


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    """Specify asyncio as the default backend for anyio."""
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
def mock_mongo_client():
    """Provides a session-scoped in-memory Mongo mock client."""
    client = AsyncMongoMockClient()
    return client


@pytest_asyncio.fixture
async def test_db(mock_mongo_client):
    """Provides a clean in-memory database instance for each test.
    
    Drops collections before each test to guarantee complete test isolation.
    """
    db = mock_mongo_client["test_medireport"]
    # Clean collections before each test run
    await db.users.delete_many({})
    await db.patient_profiles.delete_many({})
    await db.reports.delete_many({})
    
    # Set manager db to mock db as well
    mongo_manager.db = db
    return db


@pytest_asyncio.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient with MongoDB dependency overridden to use in-memory test_db."""
    
    async def override_get_database():
        return test_db

    app.dependency_overrides[get_database] = override_get_database
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
