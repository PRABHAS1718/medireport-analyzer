"""Comprehensive QA test suite for app/core/config.py.

Tests default values, type coercion, environment overrides, properties,
and validation failure boundaries.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError
from app.core.config import Settings, settings


def test_cfg_01_default_settings():
    """TC-CFG-01: Verify default configuration attributes are correctly initialized."""
    assert settings.PROJECT_NAME == "MediReport Analyzer"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) >= 1
    assert settings.MAX_UPLOAD_SIZE_BYTES == 10 * 1024 * 1024


def test_cfg_02_is_production_property():
    """TC-CFG-02: Verify is_production returns True only when ENVIRONMENT is production."""
    dev_settings = Settings(ENVIRONMENT="development")
    assert dev_settings.is_production is False

    prod_settings = Settings(ENVIRONMENT="production")
    assert prod_settings.is_production is True

    prod_caps_settings = Settings(ENVIRONMENT="PRODUCTION")
    assert prod_caps_settings.is_production is True


def test_cfg_03_resolved_storage_path(tmp_path):
    """TC-CFG-03: Verify resolved_storage_path resolves to absolute path and creates directory."""
    custom_path = tmp_path / "custom_uploads"
    custom_settings = Settings(FILE_STORAGE_PATH=str(custom_path))
    resolved = custom_settings.resolved_storage_path

    assert resolved.is_absolute()
    assert resolved.exists()
    assert resolved.is_dir()


def test_cfg_04_type_coercion():
    """TC-CFG-04: Verify Pydantic type coercion for string representations of ints and booleans."""
    coerced_settings = Settings(
        ACCESS_TOKEN_EXPIRE_MINUTES="120",  # String instead of int
        DEBUG="false",                      # String instead of bool
    )
    assert coerced_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120
    assert coerced_settings.DEBUG is False


def test_cfg_05_invalid_type_validation_error():
    """TC-CFG-05: Verify ValidationError is raised when unparseable types are passed."""
    with pytest.raises(ValidationError):
        Settings(ACCESS_TOKEN_EXPIRE_MINUTES="not-a-number")

    with pytest.raises(ValidationError):
        Settings(MAX_UPLOAD_SIZE_BYTES="unlimited")


def test_cfg_06_extra_fields_ignored():
    """TC-CFG-06: Verify extra unknown environment variables do not crash Settings."""
    extra_settings = Settings(UNKNOWN_VARIABLE="some_value")
    assert not hasattr(extra_settings, "UNKNOWN_VARIABLE")
