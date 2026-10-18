"""Comprehensive QA test suite for app/core/security.py.

Tests bcrypt password hashing, salt uniqueness, verification, JWT token
issuance, decoding, expiration handling, and tampering resistance.
"""

import pytest
from datetime import timedelta
import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_ALGORITHM,
)
from app.core.config import settings


def test_sec_01_hash_generates_unique_salts():
    """TC-SEC-01: Verify that hashing the same password twice yields different hashes due to salting."""
    pwd = "SamePassword123!"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    assert hash1 != hash2
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True


def test_sec_02_verify_password_correctness():
    """TC-SEC-02: Verify verify_password correctly identifies valid and invalid passwords."""
    pwd = "CorrectHorseBatteryStaple!"
    hashed = hash_password(pwd)

    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_sec_03_verify_corrupted_hash():
    """TC-SEC-03: Verify verify_password fails safely on corrupted or malformed hash strings."""
    assert verify_password("Password123!", "not-a-valid-bcrypt-hash") is False
    assert verify_password("Password123!", "") is False


def test_sec_04_create_and_decode_token():
    """TC-SEC-04: Verify create_access_token produces a decodable JWT with expected payload."""
    subject_id = "user_12345"
    token = create_access_token(subject=subject_id)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == subject_id
    assert "exp" in payload
    assert "iat" in payload


def test_sec_05_expired_token_returns_none():
    """TC-SEC-05: Verify decode_access_token rejects expired tokens."""
    subject_id = "expired_user"
    # Token expired 10 minutes ago
    expired_token = create_access_token(
        subject=subject_id,
        expires_delta=timedelta(minutes=-10)
    )

    payload = decode_access_token(expired_token)
    assert payload is None


def test_sec_06_tampered_token_returns_none():
    """TC-SEC-06: Verify decode_access_token rejects modified token signatures."""
    token = create_access_token(subject="user_real")
    # Tamper with the signature portion
    tampered_token = token[:-5] + "XXXXX"

    payload = decode_access_token(tampered_token)
    assert payload is None


def test_sec_07_token_signed_with_different_secret():
    """TC-SEC-07: Verify decode_access_token rejects tokens signed by another secret key."""
    foreign_token = jwt.encode(
        {"sub": "attacker", "exp": 9999999999},
        "completely-different-secret-key-32bytes!",
        algorithm=JWT_ALGORITHM,
    )

    payload = decode_access_token(foreign_token)
    assert payload is None
