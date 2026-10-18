"""Unit and integration tests for medical record endpoints (labs, symptoms, medications, history)."""

import pytest
from httpx import AsyncClient


async def create_user_and_patient(client: AsyncClient, email: str) -> tuple[str, str]:
    """Helper to create a user and a patient profile, returning (token, patient_id)."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "preferred_language": "en"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pat_res = await client.post(
        "/api/v1/patients",
        json={"display_name": "Test Patient", "sex": "male", "blood_group": "O+"},
        headers=headers,
    )
    patient_id = pat_res.json()["id"]
    return token, patient_id


@pytest.mark.asyncio
async def test_create_and_list_labs(client: AsyncClient):
    """Test recording and listing lab measurements for an authorized patient."""
    token, patient_id = await create_user_and_patient(client, "labs_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    lab_payload = {
        "original_test_name": "Hemoglobin A1c",
        "normalized_test_code": "HBA1C",
        "value": 6.8,
        "unit": "%",
        "reference_range": "<5.7",
        "collected_at": "2026-04-12",
    }
    create_res = await client.post(f"/api/v1/patients/{patient_id}/labs", json=lab_payload, headers=headers)
    assert create_res.status_code == 201
    lab_data = create_res.json()
    assert lab_data["original_test_name"] == "Hemoglobin A1c"
    assert lab_data["value"] == 6.8
    assert lab_data["unit"] == "%"
    assert lab_data["verification_status"] == "user_confirmed"

    # List labs
    list_res = await client.get(f"/api/v1/patients/{patient_id}/labs", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


@pytest.mark.asyncio
async def test_create_symptoms_conditions_medications(client: AsyncClient):
    """Test creating and retrieving symptoms, conditions, and medications."""
    token, patient_id = await create_user_and_patient(client, "records_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Symptom
    sym_res = await client.post(
        f"/api/v1/patients/{patient_id}/symptoms",
        json={"symptom_name": "Migraine", "severity": "severe", "onset_date": "2026-01"},
        headers=headers,
    )
    assert sym_res.status_code == 201
    assert sym_res.json()["symptom_name"] == "Migraine"
    assert sym_res.json()["verification_status"] == "patient_reported"

    # 2. Condition
    cond_res = await client.post(
        f"/api/v1/patients/{patient_id}/conditions",
        json={"condition_name": "Hypertension", "diagnosed_date": "2020"},
        headers=headers,
    )
    assert cond_res.status_code == 201
    assert cond_res.json()["condition_name"] == "Hypertension"

    # 3. Medication
    med_res = await client.post(
        f"/api/v1/patients/{patient_id}/medications",
        json={"medication_name": "Amlodipine", "dosage": "5 mg", "frequency": "once daily"},
        headers=headers,
    )
    assert med_res.status_code == 201
    assert med_res.json()["medication_name"] == "Amlodipine"


@pytest.mark.asyncio
async def test_unified_patient_history(client: AsyncClient):
    """Test retrieving the comprehensive unified patient history timeline."""
    token, patient_id = await create_user_and_patient(client, "history_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Add 1 lab and 1 medication
    await client.post(
        f"/api/v1/patients/{patient_id}/labs",
        json={"original_test_name": "Serum Creatinine", "value": 0.9, "unit": "mg/dL"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/patients/{patient_id}/medications",
        json={"medication_name": "Vitamin D3", "dosage": "60000 IU"},
        headers=headers,
    )

    history_res = await client.get(f"/api/v1/patients/{patient_id}/history", headers=headers)
    assert history_res.status_code == 200
    data = history_res.json()
    assert data["patient_name"] == "Test Patient"
    assert data["counts"]["labs"] == 1
    assert data["counts"]["medications"] == 1
    assert len(data["labs"]) == 1
    assert len(data["medications"]) == 1


@pytest.mark.asyncio
async def test_cross_user_isolation_on_medical_records(client: AsyncClient):
    """MANDATORY SECURITY GATE: User B cannot add or access User A's medical records."""
    token_a, patient_a = await create_user_and_patient(client, "owner_user@example.com")
    token_b, _ = await create_user_and_patient(client, "attacker_user@example.com")

    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to post lab to User A's patient
    res_post = await client.post(
        f"/api/v1/patients/{patient_a}/labs",
        json={"original_test_name": "Unauthorized Test", "value": 100.0, "unit": "mg/dL"},
        headers=headers_b,
    )
    assert res_post.status_code == 404

    # User B attempts to read User A's history
    res_get = await client.get(f"/api/v1/patients/{patient_a}/history", headers=headers_b)
    assert res_get.status_code == 404


@pytest.mark.asyncio
async def test_list_individual_medical_records(client: AsyncClient):
    """Test retrieving distinct lists for symptoms, conditions, and medications."""
    token, patient_id = await create_user_and_patient(client, "list_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initially empty lists
    assert (await client.get(f"/api/v1/patients/{patient_id}/symptoms", headers=headers)).json() == []
    assert (await client.get(f"/api/v1/patients/{patient_id}/conditions", headers=headers)).json() == []
    assert (await client.get(f"/api/v1/patients/{patient_id}/medications", headers=headers)).json() == []

    # Populate 1 of each
    await client.post(
        f"/api/v1/patients/{patient_id}/symptoms",
        json={"symptom_name": "Fatigue", "severity": "mild"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/patients/{patient_id}/conditions",
        json={"condition_name": "Asthma", "is_active": True},
        headers=headers,
    )
    await client.post(
        f"/api/v1/patients/{patient_id}/medications",
        json={"medication_name": "Albuterol", "dosage": "90 mcg"},
        headers=headers,
    )

    # Verify listing returns the created items
    sym_list = (await client.get(f"/api/v1/patients/{patient_id}/symptoms", headers=headers)).json()
    assert len(sym_list) == 1
    assert sym_list[0]["symptom_name"] == "Fatigue"

    cond_list = (await client.get(f"/api/v1/patients/{patient_id}/conditions", headers=headers)).json()
    assert len(cond_list) == 1
    assert cond_list[0]["condition_name"] == "Asthma"

    med_list = (await client.get(f"/api/v1/patients/{patient_id}/medications", headers=headers)).json()
    assert len(med_list) == 1
    assert med_list[0]["medication_name"] == "Albuterol"

