"""Application configuration module.

This module defines the central `Settings` class using Pydantic Settings.
It loads environment variables from a `.env` file or the environment,
validates types, and makes settings accessible across the application.
"""

from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration class for MediReport Analyzer.
    
    Attributes:
        PROJECT_NAME: Human-readable name of the project.
        VERSION: Current semantic version of the backend.
        API_V1_STR: Prefix for all version 1 API routes.
        ENVIRONMENT: Runtime environment ('development', 'testing', 'production').
        DEBUG: Boolean flag indicating if debug mode is active.
        SECRET_KEY: Secret key used for signing JWT tokens and session data.
        ACCESS_TOKEN_EXPIRE_MINUTES: Lifetime of an issued access token.
        CORS_ORIGINS: List of allowed frontend origin URLs.
        MONGODB_URI: Connection string for MongoDB (local or Atlas cloud).
        MONGODB_DB_NAME: Target database name within MongoDB.
        FILE_STORAGE_PATH: Relative or absolute path for storing uploaded reports.
        MAX_UPLOAD_SIZE_BYTES: Maximum allowed upload file size (default: 10MB).
        GEMINI_API_KEY: Google Gemini API key for grounded explanations (Phase 6).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "MediReport Analyzer"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "medireport_analyzer"

    # Storage
    FILE_STORAGE_PATH: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # AI
    GEMINI_API_KEY: str = ""

    @property
    def is_production(self) -> bool:
        """Helper to check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def resolved_storage_path(self) -> Path:
        """Returns the resolved absolute path to the file storage directory."""
        path = Path(self.FILE_STORAGE_PATH).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton settings instance
settings = Settings()
