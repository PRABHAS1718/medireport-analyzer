"""QA tests for database manager lifecycle, index initialization, and connection error handling."""

import pytest
from app.database.mongodb import MongoManager, get_database


@pytest.mark.asyncio
async def test_db_01_uninitialized_get_database_raises_runtime_error():
    """TC-DB-01: Verify get_database raises RuntimeError if database is not initialized."""
    manager = MongoManager()
    manager.db = None

    # Temporarily swap global manager
    from app.database import mongodb
    original_db = mongodb.mongo_manager.db
    mongodb.mongo_manager.db = None

    try:
        with pytest.raises(RuntimeError) as exc_info:
            await get_database()
        assert "Database connection is not initialized" in str(exc_info.value)
    finally:
        mongodb.mongo_manager.db = original_db


@pytest.mark.asyncio
async def test_db_02_create_indexes_on_mock(test_db):
    """TC-DB-02: Verify create_indexes creates expected indexes on users and patient_profiles."""
    manager = MongoManager()
    manager.db = test_db

    await manager.create_indexes()

    user_indexes = await test_db.users.index_information()
    assert "idx_users_email_unique" in user_indexes
    assert user_indexes["idx_users_email_unique"]["unique"] is True

    patient_indexes = await test_db.patient_profiles.index_information()
    assert "idx_patient_profiles_owner" in patient_indexes


@pytest.mark.asyncio
async def test_db_03_close_connection_nulls_client():
    """TC-DB-03: Verify close() gracefully resets client and db references to None."""
    manager = MongoManager()
    manager.client = None
    manager.db = None
    await manager.close()
    assert manager.client is None
    assert manager.db is None
