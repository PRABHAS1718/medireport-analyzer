"""Unit and security tests for patient profile management and cross-user data isolation."""

import pytest
from httpx import AsyncClient


async def create_user_and_token(client: AsyncClient, email: str, password: str = "SecurePassword123!") -> str:
    """Helper fixture to register a user and return their Bearer access token."""
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
async def test_create_and_get_patient_profile(client: AsyncClient):
    """Test creating and retrieving a patient profile."""
    token = await create_user_and_token(client, "patient_owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "display_name": "Ramesh Kumar",
        "date_of_birth": "1980-05-15",
        "sex": "male",
        "blood_group": "B+",
        "preferred_language": "hi",
    }
    create_res = await client.post("/api/v1/patients", json=payload, headers=headers)
    assert create_res.status_code == 201
    
    data = create_res.json()
    assert data["display_name"] == "Ramesh Kumar"
    assert data["date_of_birth"] == "1980-05-15"
    assert data["sex"] == "male"
    assert data["blood_group"] == "B+"
    assert data["preferred_language"] == "hi"
    assert "id" in data
    assert "owner_user_id" in data

    patient_id = data["id"]

    # Retrieve by ID
    get_res = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["display_name"] == "Ramesh Kumar"


@pytest.mark.asyncio
async def test_list_patients_scoped_to_user(client: AsyncClient):
    """Test that listing patients returns all profiles belonging to the user."""
    token = await create_user_and_token(client, "family_caregiver@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create two profiles (e.g. self and parent)
    await client.post(
        "/api/v1/patients",
        json={"display_name": "Self Profile", "sex": "female"},
        headers=headers,
    )
    await client.post(
        "/api/v1/patients",
        json={"display_name": "Elderly Mother", "sex": "female"},
        headers=headers,
    )

    list_res = await client.get("/api/v1/patients", headers=headers)
    assert list_res.status_code == 200
    profiles = list_res.json()
    assert len(profiles) == 2
    names = [p["display_name"] for p in profiles]
    assert "Self Profile" in names
    assert "Elderly Mother" in names


@pytest.mark.asyncio
async def test_update_patient_profile(client: AsyncClient):
    """Test updating permitted fields on a patient profile."""
    token = await create_user_and_token(client, "updater@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/patients",
        json={"display_name": "Initial Name", "blood_group": "O+"},
        headers=headers,
    )
    patient_id = create_res.json()["id"]

    # Update blood group and display name
    update_res = await client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"display_name": "Updated Name", "blood_group": "AB+"},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["display_name"] == "Updated Name"
    assert updated_data["blood_group"] == "AB+"


@pytest.mark.asyncio
async def test_cross_user_patient_isolation_security_gate(client: AsyncClient):
    """MANDATORY SECURITY GATE: Verify strict cross-user patient isolation.
    
    User A creates a patient profile.
    User B MUST NOT be able to read, update, or list User A's patient profile.
    Any attempt by User B to access User A's profile must fail with HTTP 404 (Not Found)
    to prevent discovery and data leakage.
    """
    token_a = await create_user_and_token(client, "user_a@example.com")
    token_b = await create_user_and_token(client, "user_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a patient profile
    res_a = await client.post(
        "/api/v1/patients",
        json={"display_name": "User A Private Profile", "blood_group": "A-"},
        headers=headers_a,
    )
    patient_a_id = res_a.json()["id"]

    # 1. User B attempts GET on User A's patient ID -> MUST return 404
    b_get_res = await client.get(f"/api/v1/patients/{patient_a_id}", headers=headers_b)
    assert b_get_res.status_code == 404
    assert "Patient profile not found" in b_get_res.json()["detail"]

    # 2. User B attempts PATCH on User A's patient ID -> MUST return 404
    b_patch_res = await client.patch(
        f"/api/v1/patients/{patient_a_id}",
        json={"display_name": "Malicious Tampering Attempt"},
        headers=headers_b,
    )
    assert b_patch_res.status_code == 404

    # 3. User B lists their patients -> User A's patient MUST NOT be present
    b_list_res = await client.get("/api/v1/patients", headers=headers_b)
    assert b_list_res.status_code == 200
    b_profiles = b_list_res.json()
    assert len(b_profiles) == 0

    # 4. Verify User A's profile remains completely untouched
    a_verify_res = await client.get(f"/api/v1/patients/{patient_a_id}", headers=headers_a)
    assert a_verify_res.status_code == 200
    assert a_verify_res.json()["display_name"] == "User A Private Profile"
