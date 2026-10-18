"""Asynchronous MongoDB connection and lifecycle management.

Uses motor (AsyncIOMotorClient) for non-blocking database queries.
Initializes essential indexes on startup to ensure data integrity.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.core.config import settings

logger = logging.getLogger("medireport.database")


class MongoManager:
    """Manages the MongoDB client connection and database access."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Initializes the MongoDB client and verifies connection with a ping."""
        logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI.split("@")[-1])
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
            )
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Verify connectivity
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB database: %s", settings.MONGODB_DB_NAME)
            await self.create_indexes()
        except Exception as exc:
            logger.warning(
                "Could not connect to live MongoDB instance (%s). "
                "Ensure MONGODB_URI in .env is configured correctly.", exc
            )

    async def close(self):
        """Closes the MongoDB connection pool."""
        if self.client:
            logger.info("Closing MongoDB connection...")
            self.client.close()
            self.client = None
            self.db = None

    async def create_indexes(self):
        """Creates foundational database indexes for integrity and performance."""
        if self.db is None:
            return

        try:
            # Users collection: Unique email index
            await self.db.users.create_index(
                [("email", ASCENDING)],
                unique=True,
                name="idx_users_email_unique"
            )

            # Patient profiles: owner_user_id index for fast lookup & isolation
            await self.db.patient_profiles.create_index(
                [("owner_user_id", ASCENDING)],
                name="idx_patient_profiles_owner"
            )

            # Reports collection: patient_id + report_date
            await self.db.reports.create_index(
                [("patient_id", ASCENDING), ("uploaded_at", ASCENDING)],
                name="idx_reports_patient_date"
            )

            # Patient context facts collection: patient_id + created_at
            await self.db.patient_context_facts.create_index(
                [("patient_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_context_facts_patient_date"
            )

            # Lab results collection: patient_id + collected_at
            await self.db.lab_results.create_index(
                [("patient_id", ASCENDING), ("collected_at", ASCENDING)],
                name="idx_lab_results_patient_date"
            )

            # Symptoms, conditions, medications: patient_id index
            for coll_name in ["symptoms", "conditions", "medications"]:
                await self.db[coll_name].create_index(
                    [("patient_id", ASCENDING)],
                    name=f"idx_{coll_name}_patient"
                )

            logger.info("Database indexes successfully initialized.")
        except Exception as exc:
            logger.warning("Failed to create database indexes: %s", exc)


# Global database manager instance
mongo_manager = MongoManager()


async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency to retrieve the active MongoDB database."""
    if mongo_manager.db is None:
        raise RuntimeError("Database connection is not initialized.")
    return mongo_manager.db
