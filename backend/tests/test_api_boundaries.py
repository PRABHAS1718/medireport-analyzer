"""Boundary, validation, and negative edge-case tests for v1 endpoints."""

import pytest
from httpx import AsyncClient
from bson import ObjectId


async def register_and_get_token(client: AsyncClient, email: str, password: str = "StrongPass123!") -> str:
    """Helper to create a user and return their Bearer JWT token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "preferred_language": "en"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_bnd_01_invalid_email_formats(client: AsyncClient):
    """TC-BND-01: Verify registration rejects invalid email structures."""
    invalid_emails = [
        "plainaddress",
        "@missingusername.com",
        "username@.com",
        "username@domain..com",
        "username with spaces@domain.com",
    ]
    for email in invalid_emails:
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!"}
        )
        assert res.status_code == 422, f"Expected 422 for invalid email: {email}"


@pytest.mark.asyncio
async def test_bnd_02_email_case_insensitivity(client: AsyncClient):
    """TC-BND-02: Verify email registration and login are case-insensitive."""
    mixed_case = "Dr.Jekyll@Hospital.Org"
    lower_case = "dr.jekyll@hospital.org"

    # Register with mixed case
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": mixed_case, "password": "PotionFormula123!"}
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == lower_case

    # Login with lowercase
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": lower_case, "password": "PotionFormula123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


@pytest.mark.asyncio
async def test_bnd_03_suspended_user_login_rejected(client: AsyncClient, test_db):
    """TC-BND-03: Verify inactive or suspended user cannot log in."""
    email = "suspended_user@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "ValidPassword123!"}
    )

    # Set user status to suspended in MongoDB
    await test_db.users.update_one(
        {"email": email},
        {"$set": {"status": "suspended"}}
    )

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ValidPassword123!"}
    )
    assert login_res.status_code == 403
    assert "inactive or suspended" in login_res.json()["detail"]


@pytest.mark.asyncio
async def test_bnd_04_deleted_user_token_rejected(client: AsyncClient, test_db):
    """TC-BND-04: Verify token fails if the user account was deleted from database."""
    email = "temporary_user@example.com"
    token = await register_and_get_token(client, email)

    # Delete user directly from DB
    await test_db.users.delete_one({"email": email})

    # Call /auth/me with the issued token
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert "no longer exists" in res.json()["detail"]


@pytest.mark.asyncio
async def test_bnd_05_patient_display_name_boundaries(client: AsyncClient):
    """TC-BND-05: Verify patient display name boundaries (empty or >100 characters)."""
    token = await register_and_get_token(client, "name_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty name
    res_empty = await client.post("/api/v1/patients", json={"display_name": ""}, headers=headers)
    assert res_empty.status_code == 422

    # Name exceeding 100 characters
    long_name = "A" * 101
    res_long = await client.post("/api/v1/patients", json={"display_name": long_name}, headers=headers)
    assert res_long.status_code == 422

    # Exactly 100 characters (valid upper boundary)
    valid_100 = "B" * 100
    res_100 = await client.post("/api/v1/patients", json={"display_name": valid_100}, headers=headers)
    assert res_100.status_code == 201


@pytest.mark.asyncio
async def test_bnd_06_patient_dob_regex_validation(client: AsyncClient):
    """TC-BND-06: Verify date_of_birth strictly enforces YYYY-MM-DD pattern."""
    token = await register_and_get_token(client, "dob_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    invalid_dobs = [
        "15-05-1990",      # DD-MM-YYYY
        "1990/05/15",      # Slashes instead of dashes
        "May 15, 1990",    # Text format
        "1990-5-5",        # Missing zero padding
        "not-a-date",
    ]
    for dob in invalid_dobs:
        res = await client.post(
            "/api/v1/patients",
            json={"display_name": "Test Patient", "date_of_birth": dob},
            headers=headers
        )
        assert res.status_code == 422, f"Expected 422 for invalid date format: {dob}"


@pytest.mark.asyncio
async def test_bnd_07_malformed_patient_id_fails_safely(client: AsyncClient):
    """TC-BND-07: Verify requesting a malformed (non-ObjectId) patient ID returns 404 rather than 500 error."""
    token = await register_and_get_token(client, "malformed_id@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    malformed_ids = ["123", "not-a-valid-hex-id", "!@#$%", "1234567890abcdef1234567z"]
    for bad_id in malformed_ids:
        res = await client.get(f"/api/v1/patients/{bad_id}", headers=headers)
        assert res.status_code == 404
        assert "Patient profile not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_bnd_08_empty_patient_patch_preserves_data(client: AsyncClient):
    """TC-BND-08: Verify sending an empty PATCH body does not wipe or corrupt patient data."""
    token = await register_and_get_token(client, "patch_empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/patients",
        json={"display_name": "Original Name", "blood_group": "O-"},
        headers=headers
    )
    patient_id = create_res.json()["id"]

    # Send empty PATCH
    patch_res = await client.patch(f"/api/v1/patients/{patient_id}", json={}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["display_name"] == "Original Name"
    assert patch_res.json()["blood_group"] == "O-"


@pytest.mark.asyncio
async def test_bnd_09_token_malformed_sub_returns_401(client: AsyncClient):
    """TC-BND-09: Verify token with non-ObjectId sub payload is rejected with 401."""
    from app.core.security import create_access_token
    token = create_access_token(subject="invalid-non-hex-id")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert "User identity in token is malformed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_bnd_10_authenticated_suspended_user_access_returns_403(client: AsyncClient, test_db):
    """TC-BND-10: Verify authenticated request with valid token fails with 403 if user account becomes suspended."""
    email = "active_then_suspended@example.com"
    token = await register_and_get_token(client, email)

    # Change user status in DB to suspended
    await test_db.users.update_one({"email": email}, {"$set": {"status": "suspended"}})

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 403
    assert "inactive or suspended" in res.json()["detail"]


@pytest.mark.asyncio
async def test_bnd_11_valid_nonexistent_patient_id_returns_404(client: AsyncClient):
    """TC-BND-11: Verify querying a valid 24-char ObjectId that does not exist in DB returns 404."""
    token = await register_and_get_token(client, "valid_hex_nonexistent@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Valid 24-character hexadecimal ObjectId that has never been created
    non_existent_hex_id = "000000000000000000000000"
    res = await client.get(f"/api/v1/patients/{non_existent_hex_id}", headers=headers)
    assert res.status_code == 404
    assert "Patient profile not found" in res.json()["detail"]

